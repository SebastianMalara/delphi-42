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
from .prompt_builder import build_prompt
from .reply_formatter import format_answer_packets
from .retriever import NullRetriever, RetrievalChunk, Retriever
from .runtime_config import ReplyConfig


class ReplyMode(str, Enum):
    HELP = "help"
    POSITION = "position"
    MODEL = "model"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"
    NO_GROUNDED_ANSWER = "no_grounded_answer"
    ARCHIVE_UNAVAILABLE = "archive_unavailable"


@dataclass(frozen=True)
class OracleReply:
    packets: tuple[str, ...]
    share_position: bool = False
    mode: ReplyMode = ReplyMode.HELP
    retrieval_hits: int = 0

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
        context = self.retriever.search(question, limit=self.retrieval_limit)
        if not self._has_grounding(context) and self.fallback_retriever is not None:
            fallback_context = self.fallback_retriever.search(
                question, limit=self.retrieval_limit
            )
            if self._has_grounding(fallback_context):
                context = fallback_context

        retrieval_hits = len(context)
        if not self._has_grounding(context):
            return OracleReply(
                packets=(NO_GROUNDED_ANSWER,),
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_hits=retrieval_hits,
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
                )
            except (ModelUnavailableError, ModelExecutionError):
                pass

        try:
            fallback_draft = self.fallback_llm.generate(prompt)
        except Exception:
            return self._single_packet(
                ARCHIVE_UNAVAILABLE,
                mode=ReplyMode.ARCHIVE_UNAVAILABLE,
                retrieval_hits=retrieval_hits,
            )

        if fallback_draft.short_answer == NO_GROUNDED_ANSWER:
            return self._single_packet(
                NO_GROUNDED_ANSWER,
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_hits=retrieval_hits,
            )

        return OracleReply(
            packets=self._format_packets(fallback_draft),
            mode=ReplyMode.DETERMINISTIC_FALLBACK,
            retrieval_hits=retrieval_hits,
        )

    def _has_grounding(self, context: list[RetrievalChunk]) -> bool:
        return any(chunk.snippet.strip() and chunk.matched_terms >= 1 for chunk in context)

    def _format_packets(self, draft: AnswerDraft) -> tuple[str, ...]:
        return format_answer_packets(
            draft,
            short_max_chars=self.reply_config.short_max_chars,
            continuation_max_chars=self.reply_config.continuation_max_chars,
            max_continuation_packets=self.reply_config.max_continuation_packets,
        )

    def _single_packet(
        self,
        text: str,
        *,
        mode: ReplyMode,
        retrieval_hits: int = 0,
    ) -> OracleReply:
        return OracleReply(
            packets=(text,),
            mode=mode,
            retrieval_hits=retrieval_hits,
        )
