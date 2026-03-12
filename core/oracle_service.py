from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bot.command_parser import HELP_TEXT, ParsedCommand

from .intent import IntentType, classify_command
from .llm_runner import (
    ARCHIVE_UNAVAILABLE,
    NO_GROUNDED_ANSWER,
    LLMRunner,
    ModelExecutionError,
    ModelUnavailableError,
    RuleBasedRunner,
    truncate_words,
)
from .prompt_builder import build_prompt
from .retriever import NullRetriever, RetrievalChunk, Retriever


class ReplyMode(str, Enum):
    HELP = "help"
    POSITION = "position"
    MODEL = "model"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"
    NO_GROUNDED_ANSWER = "no_grounded_answer"
    ARCHIVE_UNAVAILABLE = "archive_unavailable"


@dataclass(frozen=True)
class OracleReply:
    text: str
    share_position: bool = False
    mode: ReplyMode = ReplyMode.HELP
    retrieval_hits: int = 0


class OracleService:
    """Answer Meshtastic requests using local-only retrieval and generation."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        llm: LLMRunner | None = None,
        max_words: int = 40,
        fallback_llm: LLMRunner | None = None,
        retrieval_limit: int = 3,
    ) -> None:
        self.retriever = retriever or NullRetriever()
        self.llm = llm
        self.max_words = max_words
        self.fallback_llm = fallback_llm or RuleBasedRunner()
        self.retrieval_limit = retrieval_limit

    def handle(self, command: ParsedCommand) -> OracleReply:
        intent = classify_command(command)

        if intent.kind is IntentType.HELP:
            return OracleReply(text=HELP_TEXT.strip(), mode=ReplyMode.HELP)

        if intent.kind in {IntentType.LOCATION, IntentType.POSITION}:
            return OracleReply(
                text="Sending a private position packet.",
                share_position=True,
                mode=ReplyMode.POSITION,
            )

        if intent.kind is IntentType.ASK and intent.question:
            return self._handle_ask(intent.question)

        return OracleReply(
            text="Send `help` for commands or `ask <question>` for counsel.",
            mode=ReplyMode.HELP,
        )

    def _handle_ask(self, question: str) -> OracleReply:
        context = self.retriever.search(question, limit=self.retrieval_limit)
        retrieval_hits = len(context)
        if not self._has_grounding(context):
            return OracleReply(
                text=NO_GROUNDED_ANSWER,
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_hits=retrieval_hits,
            )

        prompt = build_prompt(
            question=question,
            context_chunks=context,
            max_words=self.max_words,
        )
        if self.llm is not None:
            try:
                text = self.llm.generate(prompt, max_words=self.max_words)
                return OracleReply(
                    text=truncate_words(text, self.max_words),
                    mode=ReplyMode.MODEL,
                    retrieval_hits=retrieval_hits,
                )
            except (ModelUnavailableError, ModelExecutionError):
                pass

        try:
            fallback_text = self.fallback_llm.generate(prompt, max_words=self.max_words)
        except Exception:
            return OracleReply(
                text=ARCHIVE_UNAVAILABLE,
                mode=ReplyMode.ARCHIVE_UNAVAILABLE,
                retrieval_hits=retrieval_hits,
            )

        if fallback_text == NO_GROUNDED_ANSWER:
            return OracleReply(
                text=fallback_text,
                mode=ReplyMode.NO_GROUNDED_ANSWER,
                retrieval_hits=retrieval_hits,
            )

        return OracleReply(
            text=truncate_words(fallback_text, self.max_words),
            mode=ReplyMode.DETERMINISTIC_FALLBACK,
            retrieval_hits=retrieval_hits,
        )

    def _has_grounding(self, context: list[RetrievalChunk]) -> bool:
        return any(chunk.snippet.strip() and chunk.matched_terms >= 1 for chunk in context)
