from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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
    RetrievalChunk,
    Retriever,
    grounded_retrieval_chunks,
    minimum_grounding_threshold,
    normalized_query_terms,
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
    retrieval_sources: tuple[str, ...] = ()
    retrieval_titles: tuple[str, ...] = ()
    retrieval_scores: tuple[int, ...] = ()

    @property
    def text(self) -> str:
        return self.packets[0] if self.packets else ""


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

    def _handle_ask(self, question: str) -> OracleReply:
        query_terms = normalized_query_terms(question)
        threshold = minimum_grounding_threshold(query_terms)

        primary_context = grounded_retrieval_chunks(
            question,
            self.retriever.search(question, limit=self.retrieval_limit),
        )
        context = primary_context
        retrieval_source = "sqlite" if primary_context else "none"

        primary_best = self._best_score(primary_context)
        if self.fallback_retriever is not None and (
            not primary_context or primary_best <= threshold
        ):
            fallback_context = grounded_retrieval_chunks(
                question,
                self.fallback_retriever.search(question, limit=self.retrieval_limit),
            )
            fallback_best = self._best_score(fallback_context)
            if fallback_context and (not primary_context or fallback_best > primary_best):
                context = fallback_context
                retrieval_source = "zim" if not primary_context else "sqlite+zim"

        retrieval_hits = len(context)
        if not context:
            return OracleReply(
                packets=(NO_GROUNDED_ANSWER,),
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_hits=retrieval_hits,
                retrieval_source="none",
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
                return OracleReply(
                    packets=self._format_packets(draft),
                    mode=ReplyMode.MODEL,
                    retrieval_hits=retrieval_hits,
                    retrieval_source=retrieval_source,
                    retrieval_sources=self._retrieval_sources(context),
                    retrieval_titles=self._retrieval_titles(context),
                    retrieval_scores=self._retrieval_scores(context),
                )
            except ModelExecutionError:
                fallback_draft = self._long_answer_model_fallback(question, context)
                if fallback_draft is not None:
                    return OracleReply(
                        packets=self._format_packets(fallback_draft),
                        mode=ReplyMode.MODEL_LONG_FALLBACK,
                        retrieval_hits=retrieval_hits,
                        retrieval_source=retrieval_source,
                        retrieval_sources=self._retrieval_sources(context),
                        retrieval_titles=self._retrieval_titles(context),
                        retrieval_scores=self._retrieval_scores(context),
                    )
            except ModelUnavailableError:
                pass

        try:
            fallback_draft = self.fallback_llm.generate(prompt)
        except Exception:
            return self._single_packet(
                ARCHIVE_UNAVAILABLE,
                mode=ReplyMode.ARCHIVE_UNAVAILABLE,
                retrieval_hits=retrieval_hits,
                retrieval_source=retrieval_source,
                context=context,
            )

        if fallback_draft.short_answer == NO_GROUNDED_ANSWER:
            return self._single_packet(
                NO_GROUNDED_ANSWER,
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_hits=retrieval_hits,
                retrieval_source="none",
            )

        return OracleReply(
            packets=self._format_packets(fallback_draft),
            mode=ReplyMode.DETERMINISTIC_FALLBACK,
            retrieval_hits=retrieval_hits,
            retrieval_source=retrieval_source,
            retrieval_sources=self._retrieval_sources(context),
            retrieval_titles=self._retrieval_titles(context),
            retrieval_scores=self._retrieval_scores(context),
        )

    def _best_score(self, context: list[RetrievalChunk]) -> int:
        return max((chunk.matched_terms for chunk in context), default=0)

    def _format_packets(self, draft: AnswerDraft) -> tuple[str, ...]:
        return format_answer_packets(
            draft,
            short_max_chars=self.reply_config.short_max_chars,
            continuation_max_chars=self.reply_config.continuation_max_chars,
            max_continuation_packets=self.reply_config.max_continuation_packets,
        )

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

    def _retrieval_sources(self, context: list[RetrievalChunk]) -> tuple[str, ...]:
        return tuple(chunk.source for chunk in context[: self.retrieval_limit])

    def _retrieval_titles(self, context: list[RetrievalChunk]) -> tuple[str, ...]:
        return tuple(chunk.title for chunk in context[: self.retrieval_limit])

    def _retrieval_scores(self, context: list[RetrievalChunk]) -> tuple[int, ...]:
        return tuple(chunk.matched_terms for chunk in context[: self.retrieval_limit])

    def _single_packet(
        self,
        text: str,
        *,
        mode: ReplyMode,
        retrieval_hits: int = 0,
        retrieval_source: str = "none",
        context: list[RetrievalChunk] | None = None,
    ) -> OracleReply:
        context = context or []
        return OracleReply(
            packets=(text,),
            mode=mode,
            retrieval_hits=retrieval_hits,
            retrieval_source=retrieval_source,
            retrieval_sources=self._retrieval_sources(context),
            retrieval_titles=self._retrieval_titles(context),
            retrieval_scores=self._retrieval_scores(context),
        )
