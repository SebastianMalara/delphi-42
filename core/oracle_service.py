from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import re

from bot.command_parser import HELP_TEXT, ParsedCommand

from .intent import IntentType, classify_command
from .llm_runner import (
    ARCHIVE_UNAVAILABLE,
    CHAT_UNAVAILABLE,
    NO_GROUNDED_ANSWER,
    LLMRunner,
    ModelExecutionError,
    ModelUnavailableError,
)
from .prompt_builder import (
    ASK_SYSTEM_PROMPT,
    CHAT_SYSTEM_PROMPT,
    build_chat_prompt,
    build_condense_prompt,
    build_grounded_answer_prompt,
    build_shrink_prompt,
)
from .reply_formatter import (
    first_sentence,
    fits_utf8_bytes,
    normalize_text,
    packet_payload_budget,
    prefix_text,
    split_prefixed_packets,
    split_text_by_bytes,
    trim_text,
    trim_to_utf8_bytes,
)
from .retriever import (
    NullRetriever,
    RetrievalAssessment,
    RetrievalChunk,
    RetrievalConfidence,
    Retriever,
    assess_retrieval,
)
from .runtime_config import ReplyConfig


class ReplyMode(str, Enum):
    HELP = "help"
    POSITION = "position"
    ASK_MODEL = "ask_model"
    ASK_DETERMINISTIC_FALLBACK = "ask_deterministic_fallback"
    ASK_NO_GROUNDED_ANSWER = "ask_no_grounded_answer"
    CHAT_MODEL = "chat_model"
    CHAT_UNAVAILABLE = "chat_unavailable"
    ARCHIVE_UNAVAILABLE = "archive_unavailable"


@dataclass(frozen=True)
class OracleReply:
    packets: tuple[str, ...]
    share_position: bool = False
    mode: ReplyMode = ReplyMode.HELP
    command_name: str = "help"
    retrieval_hits: int = 0
    retrieval_source: str = "none"
    retrieval_confidence: str = RetrievalConfidence.WEAK.value
    retrieval_sources: tuple[str, ...] = ()
    retrieval_titles: tuple[str, ...] = ()
    retrieval_scores: tuple[int, ...] = ()
    shrink_attempts: int = 0

    @property
    def text(self) -> str:
        return self.packets[0] if self.packets else ""


@dataclass(frozen=True)
class RetrievalDecision:
    source: str
    confidence: RetrievalConfidence
    anchor_terms: tuple[str, ...]
    context: tuple[RetrievalChunk, ...]
    candidates: tuple[RetrievalChunk, ...]
    should_use_model: bool
    selected_chunk: RetrievalChunk | None = None
    best_score: int = 0


@dataclass(frozen=True)
class AnswerBundle:
    full_answer: str
    condensed_answer: str
    short_answer: str


class OracleService:
    """Answer Meshtastic requests using Kiwix retrieval and multi-pass generation."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        llm: LLMRunner | None = None,
        reply_config: ReplyConfig | None = None,
        *,
        retrieval_limit: int = 3,
        response_prefix: str = "🤖 ",
        packet_byte_limit: int = 0,
        chat_history_exchanges: int = 4,
    ) -> None:
        self.retriever = retriever or NullRetriever()
        self.llm = llm
        self.reply_config = reply_config or ReplyConfig()
        self.retrieval_limit = retrieval_limit
        self.response_prefix = response_prefix
        self.packet_byte_limit = packet_byte_limit
        self.chat_history_exchanges = chat_history_exchanges
        self._chat_history: dict[str, deque[tuple[str, str]]] = defaultdict(
            lambda: deque(maxlen=max(self.chat_history_exchanges, 1) * 2)
        )

    def handle(
        self,
        command: ParsedCommand,
        *,
        sender_id: str | None = None,
    ) -> OracleReply:
        intent = classify_command(command)

        if intent.kind is IntentType.HELP:
            return self._static_reply(HELP_TEXT.strip(), mode=ReplyMode.HELP, command_name="help")

        if intent.kind in {IntentType.LOCATION, IntentType.POSITION}:
            return OracleReply(
                packets=self._static_packets("Sending a private position packet."),
                share_position=True,
                mode=ReplyMode.POSITION,
                command_name=command.name,
            )

        if intent.kind is IntentType.ASK and intent.question:
            return self._handle_ask(intent.question)

        if intent.kind is IntentType.CHAT and intent.question:
            return self._handle_chat(intent.question, sender_id=sender_id or "anonymous")

        return self._static_reply(
            HELP_TEXT.strip(),
            mode=ReplyMode.HELP,
            command_name="help",
        )

    def inspect_ask(self, question: str) -> RetrievalDecision:
        assessment = self._assess_retriever(question, self.retriever)
        retrieval_source = "kiwix" if assessment.context else "none"
        if assessment.confidence is RetrievalConfidence.WEAK or not assessment.context:
            retrieval_source = "none"

        return RetrievalDecision(
            source=retrieval_source,
            confidence=assessment.confidence,
            anchor_terms=assessment.anchor_terms,
            context=assessment.context,
            candidates=assessment.candidates,
            should_use_model=(
                assessment.confidence is not RetrievalConfidence.WEAK
                and bool(assessment.context)
            ),
            selected_chunk=assessment.selected_chunk,
            best_score=assessment.best_score,
        )

    def _handle_ask(self, question: str) -> OracleReply:
        decision = self.inspect_ask(question)
        context = list(decision.context)
        retrieval_hits = len(context)

        if decision.confidence is RetrievalConfidence.WEAK or not context:
            return self._static_reply(
                NO_GROUNDED_ANSWER,
                mode=ReplyMode.ASK_NO_GROUNDED_ANSWER,
                command_name="ask",
                retrieval_confidence=decision.confidence.value,
                retrieval_chunks=decision.candidates,
            )

        bundle, mode, shrink_attempts = self._build_ask_bundle(question, context)
        if bundle is None:
            return self._static_reply(
                ARCHIVE_UNAVAILABLE,
                mode=ReplyMode.ARCHIVE_UNAVAILABLE,
                command_name="ask",
                retrieval_hits=retrieval_hits,
                retrieval_source=decision.source,
                retrieval_confidence=decision.confidence.value,
                retrieval_chunks=decision.candidates,
            )

        packets, packet_shrinks = self._format_bundle(
            bundle,
            preserve_grounding=True,
        )
        return OracleReply(
            packets=packets,
            mode=mode,
            command_name="ask",
            retrieval_hits=retrieval_hits,
            retrieval_source=decision.source,
            retrieval_confidence=decision.confidence.value,
            retrieval_sources=self._retrieval_sources(decision.candidates),
            retrieval_titles=self._retrieval_titles(decision.candidates),
            retrieval_scores=self._retrieval_scores(decision.candidates),
            shrink_attempts=shrink_attempts + packet_shrinks,
        )

    def _handle_chat(self, message: str, *, sender_id: str) -> OracleReply:
        if self.llm is None:
            return self._static_reply(
                CHAT_UNAVAILABLE,
                mode=ReplyMode.CHAT_UNAVAILABLE,
                command_name="chat",
            )

        history = tuple(self._chat_history[sender_id])
        bundle, shrink_attempts = self._build_chat_bundle(message, history)
        if bundle is None:
            return self._static_reply(
                CHAT_UNAVAILABLE,
                mode=ReplyMode.CHAT_UNAVAILABLE,
                command_name="chat",
            )

        packets, packet_shrinks = self._format_bundle(
            bundle,
            preserve_grounding=False,
        )
        self._remember_chat(sender_id, user_message=message, assistant_message=bundle.condensed_answer)
        return OracleReply(
            packets=packets,
            mode=ReplyMode.CHAT_MODEL,
            command_name="chat",
            shrink_attempts=shrink_attempts + packet_shrinks,
        )

    def _build_ask_bundle(
        self,
        question: str,
        context: list[RetrievalChunk],
    ) -> tuple[AnswerBundle | None, ReplyMode, int]:
        deterministic_bundle = self._deterministic_bundle(context)
        if self.llm is None:
            return deterministic_bundle, ReplyMode.ASK_DETERMINISTIC_FALLBACK, 0

        prompt = build_grounded_answer_prompt(question, context)
        try:
            full_answer = self.llm.complete(
                prompt,
                system_prompt=ASK_SYSTEM_PROMPT,
                temperature=0.0,
            )
        except (ModelExecutionError, ModelUnavailableError):
            return deterministic_bundle, ReplyMode.ASK_DETERMINISTIC_FALLBACK, 0

        full_answer = normalize_text(full_answer)
        if not full_answer or full_answer == NO_GROUNDED_ANSWER:
            return None, ReplyMode.ASK_NO_GROUNDED_ANSWER, 0

        condensed, condensed_shrinks = self._rewrite_to_limit(
            full_answer,
            target_chars=self.reply_config.condensed_max_chars,
            preserve_grounding=True,
            system_prompt=ASK_SYSTEM_PROMPT,
        )
        short, short_shrinks = self._rewrite_to_limit(
            condensed,
            target_chars=self.reply_config.short_max_chars,
            preserve_grounding=True,
            system_prompt=ASK_SYSTEM_PROMPT,
        )

        return (
            AnswerBundle(
                full_answer=full_answer,
                condensed_answer=condensed,
                short_answer=short,
            ),
            ReplyMode.ASK_MODEL,
            condensed_shrinks + short_shrinks,
        )

    def _build_chat_bundle(
        self,
        message: str,
        history: tuple[tuple[str, str], ...],
    ) -> tuple[AnswerBundle | None, int]:
        prompt = build_chat_prompt(message, history=history)
        try:
            full_answer = self.llm.complete(
                prompt,
                system_prompt=CHAT_SYSTEM_PROMPT,
                temperature=0.6,
            )
        except (ModelExecutionError, ModelUnavailableError):
            return None, 0

        full_answer = normalize_text(full_answer)
        if not full_answer:
            return None, 0

        condensed, condensed_shrinks = self._rewrite_to_limit(
            full_answer,
            target_chars=self.reply_config.condensed_max_chars,
            preserve_grounding=False,
            system_prompt=CHAT_SYSTEM_PROMPT,
        )
        short, short_shrinks = self._rewrite_to_limit(
            condensed,
            target_chars=self.reply_config.short_max_chars,
            preserve_grounding=False,
            system_prompt=CHAT_SYSTEM_PROMPT,
        )
        return (
            AnswerBundle(
                full_answer=full_answer,
                condensed_answer=condensed,
                short_answer=short,
            ),
            condensed_shrinks + short_shrinks,
        )

    def _rewrite_to_limit(
        self,
        text: str,
        *,
        target_chars: int,
        preserve_grounding: bool,
        system_prompt: str,
    ) -> tuple[str, int]:
        normalized = normalize_text(text)
        if len(normalized) <= target_chars:
            return normalized, 0

        if self.llm is None:
            return self._deterministic_limit(normalized, target_chars), 0

        prompt = build_condense_prompt(
            normalized,
            target_chars=target_chars,
            preserve_grounding=preserve_grounding,
        )
        try:
            rewritten = normalize_text(
                self.llm.complete(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=0.0,
                )
            )
        except (ModelExecutionError, ModelUnavailableError):
            return self._deterministic_limit(normalized, target_chars), 0

        if not rewritten:
            return self._deterministic_limit(normalized, target_chars), 0
        if len(rewritten) <= target_chars:
            return rewritten, 1
        return self._deterministic_limit(rewritten, target_chars), 1

    def _format_bundle(
        self,
        bundle: AnswerBundle,
        *,
        preserve_grounding: bool,
    ) -> tuple[tuple[str, ...], int]:
        shrink_attempts = 0
        short_text = normalize_text(bundle.short_answer) or normalize_text(bundle.condensed_answer)
        condensed_text = normalize_text(bundle.condensed_answer) or normalize_text(bundle.full_answer)

        short_text, short_shrinks = self._validate_short_answer(
            short_text,
            preserve_grounding=preserve_grounding,
        )
        shrink_attempts += short_shrinks
        first_packet = prefix_text(short_text, self.response_prefix)

        remaining_packets = max(self.reply_config.max_total_packets - 1, 0)
        if remaining_packets <= 0 or not condensed_text:
            return (first_packet,), shrink_attempts

        continuation_text = condensed_text
        if normalize_text(continuation_text) == normalize_text(short_text):
            return (first_packet,), shrink_attempts

        continuation_text, continuation_shrinks = self._validate_continuation_answer(
            continuation_text,
            preserve_grounding=preserve_grounding,
            max_parts=remaining_packets,
        )
        shrink_attempts += continuation_shrinks

        continuation_packets = self._continuation_packets(
            continuation_text,
            max_parts=remaining_packets,
        )
        if continuation_packets and continuation_packets[0] == first_packet:
            continuation_packets = continuation_packets[1:]
        if not continuation_packets:
            return (first_packet,), shrink_attempts
        return (first_packet, *continuation_packets[:remaining_packets]), shrink_attempts

    def _validate_short_answer(
        self,
        short_text: str,
        *,
        preserve_grounding: bool,
    ) -> tuple[str, int]:
        shrink_attempts = 0
        text = normalize_text(short_text)
        if len(text) > self.reply_config.short_max_chars:
            text, did_shrink = self._maybe_shrink_text(
                text,
                max_chars=self.reply_config.short_max_chars,
                preserve_grounding=preserve_grounding,
            )
            shrink_attempts += did_shrink
        text = self._deterministic_limit(text, self.reply_config.short_max_chars)

        if self.packet_byte_limit > 0:
            prefixed = prefix_text(text, self.response_prefix)
            if not fits_utf8_bytes(prefixed, self.packet_byte_limit):
                text, did_shrink = self._maybe_shrink_text(
                    text,
                    max_chars=packet_payload_budget(self.response_prefix, self.packet_byte_limit),
                    preserve_grounding=preserve_grounding,
                )
                shrink_attempts += did_shrink
            payload_budget = packet_payload_budget(self.response_prefix, self.packet_byte_limit)
            text = trim_to_utf8_bytes(text, payload_budget)
        return text, shrink_attempts

    def _validate_continuation_answer(
        self,
        continuation_text: str,
        *,
        preserve_grounding: bool,
        max_parts: int,
    ) -> tuple[str, int]:
        shrink_attempts = 0
        text = normalize_text(continuation_text)
        if max_parts <= 0:
            return "", shrink_attempts

        if self.packet_byte_limit <= 0:
            if len(text) > self.reply_config.condensed_max_chars:
                text, did_shrink = self._maybe_shrink_text(
                    text,
                    max_chars=self.reply_config.condensed_max_chars,
                    preserve_grounding=preserve_grounding,
                )
                shrink_attempts += did_shrink
            return self._deterministic_limit(text, self.reply_config.condensed_max_chars), shrink_attempts

        payload_budget = packet_payload_budget(self.response_prefix, self.packet_byte_limit)
        total_budget = payload_budget * max_parts
        if len(text.encode("utf-8")) > total_budget:
            text, did_shrink = self._maybe_shrink_text(
                text,
                max_chars=min(self.reply_config.condensed_max_chars, total_budget),
                preserve_grounding=preserve_grounding,
            )
            shrink_attempts += did_shrink

        required_parts = len(
            split_text_by_bytes(
                text,
                max_bytes=payload_budget,
                max_parts=max_parts + 1,
            )
        )
        if required_parts > max_parts:
            text = self._deterministic_limit(text, total_budget)
        return text, shrink_attempts

    def _continuation_packets(self, text: str, *, max_parts: int) -> list[str]:
        if max_parts <= 0 or not text:
            return []
        if self.packet_byte_limit <= 0:
            return [prefix_text(text, self.response_prefix)]
        return split_prefixed_packets(
            text,
            prefix=self.response_prefix,
            packet_byte_limit=self.packet_byte_limit,
            max_parts=max_parts,
        )

    def _maybe_shrink_text(
        self,
        text: str,
        *,
        max_chars: int,
        preserve_grounding: bool,
    ) -> tuple[str, int]:
        normalized = normalize_text(text)
        if len(normalized) <= max_chars or self.llm is None:
            return normalized, 0

        system_prompt = ASK_SYSTEM_PROMPT if preserve_grounding else CHAT_SYSTEM_PROMPT
        prompt = build_shrink_prompt(
            normalized,
            max_chars=max_chars,
            preserve_grounding=preserve_grounding,
        )
        try:
            shrunk = normalize_text(
                self.llm.complete(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=0.0,
                )
            )
        except (ModelExecutionError, ModelUnavailableError):
            return normalized, 0

        if not shrunk:
            return normalized, 0
        return shrunk, 1

    def _assess_retriever(
        self,
        question: str,
        retriever: Retriever | None,
    ) -> RetrievalAssessment:
        if retriever is None:
            return RetrievalAssessment(
                anchor_terms=(),
                confidence=RetrievalConfidence.WEAK,
                selected_chunk=None,
                context=(),
                candidates=(),
            )

        candidates = retriever.search(
            question,
            limit=max(self.retrieval_limit * 6, 12),
        )
        return assess_retrieval(
            question,
            candidates,
            context_limit=self.retrieval_limit,
        )

    def _deterministic_bundle(self, context: list[RetrievalChunk]) -> AnswerBundle | None:
        full_answer = self._deterministic_context_answer(context)
        if not full_answer:
            return None
        condensed = self._deterministic_limit(
            full_answer,
            self.reply_config.condensed_max_chars,
        )
        short_source = first_sentence(condensed) or condensed
        short = self._deterministic_limit(short_source, self.reply_config.short_max_chars)
        if not short:
            return None
        return AnswerBundle(
            full_answer=full_answer,
            condensed_answer=condensed,
            short_answer=short,
        )

    def _deterministic_context_answer(
        self,
        context: list[RetrievalChunk],
    ) -> str:
        if not context:
            return ""

        sentences: list[str] = []
        seen: set[str] = set()
        for chunk in context[: self.retrieval_limit]:
            for sentence in re.split(r"(?<=[.!?])\s+", chunk.snippet):
                normalized = normalize_text(sentence)
                if not normalized:
                    continue
                key = normalized.casefold()
                if key in seen:
                    continue
                seen.add(key)
                sentences.append(normalized)
        return normalize_text(" ".join(sentences))

    def _deterministic_limit(self, text: str, max_chars: int) -> str:
        normalized = normalize_text(text)
        if len(normalized) <= max_chars:
            return normalized

        sentences = [chunk for chunk in re.split(r"(?<=[.!?])\s+", normalized) if chunk]
        current: list[str] = []
        for sentence in sentences:
            candidate = " ".join(current + [sentence]).strip()
            if len(candidate) > max_chars and current:
                break
            if len(candidate) > max_chars:
                return trim_text(sentence, max_chars)
            current.append(sentence)
        if current:
            return " ".join(current)
        return trim_text(normalized, max_chars)

    def _remember_chat(
        self,
        sender_id: str,
        *,
        user_message: str,
        assistant_message: str,
    ) -> None:
        history = self._chat_history[sender_id]
        history.append(("user", normalize_text(user_message)))
        history.append(("assistant", normalize_text(assistant_message)))

    def _retrieval_sources(self, chunks: tuple[RetrievalChunk, ...]) -> tuple[str, ...]:
        return tuple(chunk.source for chunk in chunks[: self.retrieval_limit])

    def _retrieval_titles(self, chunks: tuple[RetrievalChunk, ...]) -> tuple[str, ...]:
        return tuple(chunk.title for chunk in chunks[: self.retrieval_limit])

    def _retrieval_scores(self, chunks: tuple[RetrievalChunk, ...]) -> tuple[int, ...]:
        return tuple(chunk.matched_terms for chunk in chunks[: self.retrieval_limit])

    def _static_packets(self, text: str) -> tuple[str, ...]:
        if self.packet_byte_limit <= 0:
            return (prefix_text(text, self.response_prefix),)

        packets = split_prefixed_packets(
            text,
            prefix=self.response_prefix,
            packet_byte_limit=self.packet_byte_limit,
            max_parts=max(self.reply_config.max_total_packets, 1),
        )
        return tuple(packets or [prefix_text(text, self.response_prefix)])

    def _static_reply(
        self,
        text: str,
        *,
        mode: ReplyMode,
        command_name: str,
        retrieval_hits: int = 0,
        retrieval_source: str = "none",
        retrieval_confidence: str = RetrievalConfidence.WEAK.value,
        retrieval_chunks: tuple[RetrievalChunk, ...] = (),
    ) -> OracleReply:
        return OracleReply(
            packets=self._static_packets(text),
            mode=mode,
            command_name=command_name,
            retrieval_hits=retrieval_hits,
            retrieval_source=retrieval_source,
            retrieval_confidence=retrieval_confidence,
            retrieval_sources=self._retrieval_sources(retrieval_chunks),
            retrieval_titles=self._retrieval_titles(retrieval_chunks),
            retrieval_scores=self._retrieval_scores(retrieval_chunks),
        )
