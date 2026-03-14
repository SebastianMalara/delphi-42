from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from bot.command_parser import HELP_TEXT, ParsedCommand

from .intent import IntentType, classify_command
from .llm_runner import (
    ARCHIVE_UNAVAILABLE,
    NO_GROUNDED_ANSWER,
    AnswerDraft,
    LLMRunner,
    ModelExecutionError,
    ModelUnavailableError,
    RuleBasedRunner,
)
from .prompt_builder import build_long_answer_prompt, build_prompt
from .reply_formatter import derive_short_answer, format_answer_packets
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
    MODEL = "model"
    MODEL_LONG_FALLBACK = "model_long_fallback"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"
    NO_GROUNDED_ANSWER = "no_grounded_answer"
    ARCHIVE_UNAVAILABLE = "archive_unavailable"


@dataclass(frozen=True)
class OracleReply:
    packets: tuple[str, ...]
    share_position: bool = False
    mode: ReplyMode = ReplyMode.HELP
    retrieval_hits: int = 0
    retrieval_source: str = "none"
    retrieval_confidence: str = RetrievalConfidence.WEAK.value
    retrieval_sources: tuple[str, ...] = ()
    retrieval_titles: tuple[str, ...] = ()
    retrieval_scores: tuple[int, ...] = ()

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


class OracleService:
    """Answer Meshtastic requests using local-only retrieval and generation."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        llm: LLMRunner | None = None,
        reply_config: ReplyConfig | None = None,
        fallback_llm: LLMRunner | None = None,
        fallback_retriever: Retriever | None = None,
        retrieval_limit: int = 3,
    ) -> None:
        self.retriever = retriever or NullRetriever()
        self.llm = llm
        self.reply_config = reply_config or ReplyConfig()
        self.fallback_llm = fallback_llm or RuleBasedRunner()
        self.fallback_retriever = fallback_retriever
        self.retrieval_limit = retrieval_limit

    def handle(self, command: ParsedCommand) -> OracleReply:
        intent = classify_command(command)

        if intent.kind is IntentType.HELP:
            return self._single_packet(HELP_TEXT.strip(), mode=ReplyMode.HELP)

        if intent.kind in {IntentType.LOCATION, IntentType.POSITION}:
            return OracleReply(
                packets=("Sending a private position packet.",),
                share_position=True,
                mode=ReplyMode.POSITION,
            )

        if intent.kind is IntentType.ASK and intent.question:
            return self._handle_ask(intent.question)

        return self._single_packet(
            "Send `help` for commands or `ask <question>` for counsel.",
            mode=ReplyMode.HELP,
        )

    def inspect_ask(self, question: str) -> RetrievalDecision:
        primary = self._assess_retriever(question, self.retriever)
        selected = primary
        retrieval_source = "sqlite" if primary.context else "none"

        if self.fallback_retriever is not None and primary.confidence is not RetrievalConfidence.STRONG:
            fallback = self._assess_retriever(question, self.fallback_retriever)
            if self._assessment_rank(fallback) > self._assessment_rank(primary):
                selected = fallback
                retrieval_source = "zim" if primary.confidence is RetrievalConfidence.WEAK else "sqlite+zim"

        if selected.confidence is RetrievalConfidence.WEAK or not selected.context:
            retrieval_source = "none"

        return RetrievalDecision(
            source=retrieval_source,
            confidence=selected.confidence,
            anchor_terms=selected.anchor_terms,
            context=selected.context,
            candidates=selected.candidates,
            should_use_model=(
                selected.confidence is RetrievalConfidence.STRONG and bool(selected.context)
            ),
            selected_chunk=selected.selected_chunk,
            best_score=selected.best_score,
        )

    def _handle_ask(self, question: str) -> OracleReply:
        decision = self.inspect_ask(question)
        context = list(decision.context)
        retrieval_hits = len(context)

        if decision.confidence is RetrievalConfidence.WEAK or not context:
            return OracleReply(
                packets=(NO_GROUNDED_ANSWER,),
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_hits=0,
                retrieval_source="none",
                retrieval_confidence=decision.confidence.value,
                retrieval_sources=self._retrieval_sources(decision.candidates),
                retrieval_titles=self._retrieval_titles(decision.candidates),
                retrieval_scores=self._retrieval_scores(decision.candidates),
            )

        if not decision.should_use_model:
            draft = self._deterministic_context_draft(context)
            if draft is None:
                return self._single_packet(
                    NO_GROUNDED_ANSWER,
                    mode=ReplyMode.NO_GROUNDED_ANSWER,
                    retrieval_confidence=decision.confidence.value,
                    retrieval_chunks=decision.candidates,
                )
            return OracleReply(
                packets=self._format_packets(draft),
                mode=ReplyMode.DETERMINISTIC_FALLBACK,
                retrieval_hits=retrieval_hits,
                retrieval_source=decision.source,
                retrieval_confidence=decision.confidence.value,
                retrieval_sources=self._retrieval_sources(decision.candidates),
                retrieval_titles=self._retrieval_titles(decision.candidates),
                retrieval_scores=self._retrieval_scores(decision.candidates),
            )

        prompt = build_prompt(
            question=question,
            context_chunks=context,
            short_max_chars=self.reply_config.short_max_chars,
            continuation_max_chars=self.reply_config.continuation_max_chars,
            max_continuation_packets=self.reply_config.max_continuation_packets,
        )
        if self.llm is not None:
            try:
                draft = self.llm.generate(prompt)
                packets = self._format_packets(draft)
                mode = ReplyMode.MODEL
                if len(packets) == 1 and self._context_supports_continuation(context):
                    richer_draft, richer_mode = self._recover_richer_answer(question, context)
                    if richer_draft is not None and richer_mode is not None:
                        draft = richer_draft
                        packets = self._format_packets(draft)
                        mode = richer_mode
                return OracleReply(
                    packets=packets,
                    mode=mode,
                    retrieval_hits=retrieval_hits,
                    retrieval_source=decision.source,
                    retrieval_confidence=decision.confidence.value,
                    retrieval_sources=self._retrieval_sources(decision.candidates),
                    retrieval_titles=self._retrieval_titles(decision.candidates),
                    retrieval_scores=self._retrieval_scores(decision.candidates),
                )
            except ModelExecutionError:
                fallback_draft, fallback_mode = self._recover_richer_answer(question, context)
                if fallback_draft is not None and fallback_mode is not None:
                    return OracleReply(
                        packets=self._format_packets(fallback_draft),
                        mode=fallback_mode,
                        retrieval_hits=retrieval_hits,
                        retrieval_source=decision.source,
                        retrieval_confidence=decision.confidence.value,
                        retrieval_sources=self._retrieval_sources(decision.candidates),
                        retrieval_titles=self._retrieval_titles(decision.candidates),
                        retrieval_scores=self._retrieval_scores(decision.candidates),
                    )
            except ModelUnavailableError:
                pass

        fallback_draft = self._deterministic_context_draft(context)
        if fallback_draft is None:
            try:
                fallback_draft = self.fallback_llm.generate(prompt)
            except Exception:
                return self._single_packet(
                    ARCHIVE_UNAVAILABLE,
                    mode=ReplyMode.ARCHIVE_UNAVAILABLE,
                    retrieval_hits=retrieval_hits,
                    retrieval_source=decision.source,
                    retrieval_confidence=decision.confidence.value,
                    retrieval_chunks=decision.candidates,
                )

        if fallback_draft.short_answer == NO_GROUNDED_ANSWER:
            return self._single_packet(
                NO_GROUNDED_ANSWER,
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_confidence=decision.confidence.value,
                retrieval_chunks=decision.candidates,
            )

        return OracleReply(
            packets=self._format_packets(fallback_draft),
            mode=ReplyMode.DETERMINISTIC_FALLBACK,
            retrieval_hits=retrieval_hits,
            retrieval_source=decision.source,
            retrieval_confidence=decision.confidence.value,
            retrieval_sources=self._retrieval_sources(decision.candidates),
            retrieval_titles=self._retrieval_titles(decision.candidates),
            retrieval_scores=self._retrieval_scores(decision.candidates),
        )

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
        context_expander = getattr(retriever, "expand_source_context", None)
        return assess_retrieval(
            question,
            candidates,
            context_limit=self.retrieval_limit,
            context_expander=context_expander,
        )

    def _assessment_rank(self, assessment: RetrievalAssessment) -> tuple[int, int, int]:
        confidence_rank = {
            RetrievalConfidence.WEAK: 0,
            RetrievalConfidence.MEDIUM: 1,
            RetrievalConfidence.STRONG: 2,
        }[assessment.confidence]
        return (confidence_rank, assessment.best_score, assessment.best_title_overlap)

    def _format_packets(self, draft: AnswerDraft) -> tuple[str, ...]:
        return format_answer_packets(
            draft,
            short_max_chars=self.reply_config.short_max_chars,
            continuation_max_chars=self.reply_config.continuation_max_chars,
            max_continuation_packets=self.reply_config.max_continuation_packets,
        )

    def _recover_richer_answer(
        self,
        question: str,
        context: list[RetrievalChunk],
    ) -> tuple[AnswerDraft | None, ReplyMode | None]:
        model_draft = self._long_answer_model_fallback(question, context)
        if model_draft is not None and len(self._format_packets(model_draft)) > 1:
            return model_draft, ReplyMode.MODEL_LONG_FALLBACK

        deterministic_draft = self._deterministic_context_draft(context)
        if deterministic_draft is not None and len(self._format_packets(deterministic_draft)) > 1:
            return deterministic_draft, ReplyMode.DETERMINISTIC_FALLBACK

        if model_draft is not None:
            return model_draft, ReplyMode.MODEL_LONG_FALLBACK

        return None, None

    def _context_supports_continuation(self, context: list[RetrievalChunk]) -> bool:
        draft = self._deterministic_context_draft(context)
        if draft is None:
            return False
        return len(self._format_packets(draft)) > 1

    def _deterministic_context_draft(
        self,
        context: list[RetrievalChunk],
    ) -> AnswerDraft | None:
        if not context:
            return None

        max_chars = self.reply_config.continuation_max_chars * max(
            self.reply_config.max_continuation_packets,
            1,
        )
        sentences: list[str] = []
        seen: set[str] = set()
        total_chars = 0

        for chunk in context[: self.retrieval_limit]:
            for sentence in re.split(r"(?<=[.!?])\s+", chunk.snippet):
                normalized = " ".join(sentence.strip().split())
                if not normalized:
                    continue
                key = normalized.casefold()
                if key in seen:
                    continue
                projected = total_chars + len(normalized) + (1 if sentences else 0)
                if sentences and projected > max_chars:
                    break
                seen.add(key)
                sentences.append(normalized)
                total_chars = projected
            if sentences and total_chars >= max_chars:
                break

        if not sentences:
            return None

        extended_answer = " ".join(sentences)
        short_answer = derive_short_answer(
            extended_answer,
            max_chars=self.reply_config.short_max_chars,
        )
        if not short_answer:
            return None

        return AnswerDraft(short_answer=short_answer, extended_answer=extended_answer)

    def _long_answer_model_fallback(
        self,
        question: str,
        context: list[RetrievalChunk],
    ) -> AnswerDraft | None:
        long_answer_generator = getattr(self.llm, "generate_long_answer", None)
        if not callable(long_answer_generator):
            return None

        long_prompt = build_long_answer_prompt(
            question=question,
            context_chunks=context,
            continuation_max_chars=self.reply_config.continuation_max_chars,
            max_continuation_packets=self.reply_config.max_continuation_packets,
        )
        try:
            long_answer = str(long_answer_generator(long_prompt)).strip()
        except Exception:
            return None

        if not long_answer or long_answer == NO_GROUNDED_ANSWER:
            return None

        short_answer = derive_short_answer(
            long_answer,
            max_chars=self.reply_config.short_max_chars,
        )
        if not short_answer:
            return None

        return AnswerDraft(short_answer=short_answer, extended_answer=long_answer)

    def _retrieval_sources(self, chunks: tuple[RetrievalChunk, ...]) -> tuple[str, ...]:
        return tuple(chunk.source for chunk in chunks[: self.retrieval_limit])

    def _retrieval_titles(self, chunks: tuple[RetrievalChunk, ...]) -> tuple[str, ...]:
        return tuple(chunk.title for chunk in chunks[: self.retrieval_limit])

    def _retrieval_scores(self, chunks: tuple[RetrievalChunk, ...]) -> tuple[int, ...]:
        return tuple(chunk.matched_terms for chunk in chunks[: self.retrieval_limit])

    def _single_packet(
        self,
        text: str,
        *,
        mode: ReplyMode,
        retrieval_hits: int = 0,
        retrieval_source: str = "none",
        retrieval_confidence: str = RetrievalConfidence.WEAK.value,
        retrieval_chunks: tuple[RetrievalChunk, ...] = (),
    ) -> OracleReply:
        return OracleReply(
            packets=(text,),
            mode=mode,
            retrieval_hits=retrieval_hits,
            retrieval_source=retrieval_source,
            retrieval_confidence=retrieval_confidence,
            retrieval_sources=self._retrieval_sources(retrieval_chunks),
            retrieval_titles=self._retrieval_titles(retrieval_chunks),
            retrieval_scores=self._retrieval_scores(retrieval_chunks),
        )
