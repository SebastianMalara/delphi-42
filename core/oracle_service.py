from __future__ import annotations

from dataclasses import dataclass

from bot.command_parser import HELP_TEXT, ParsedCommand

from .intent import IntentType, classify_command
from .llm_runner import LLMRunner, RuleBasedRunner
from .prompt_builder import build_prompt
from .retriever import NullRetriever, Retriever


@dataclass(frozen=True)
class OracleReply:
    text: str
    share_position: bool = False


class OracleService:
    """Answer Meshtastic requests using local-only retrieval and generation."""

    def __init__(
        self,
        retriever: Retriever | None = None,
        llm: LLMRunner | None = None,
        max_words: int = 40,
    ) -> None:
        self.retriever = retriever or NullRetriever()
        self.llm = llm or RuleBasedRunner()
        self.max_words = max_words

    def handle(self, command: ParsedCommand) -> OracleReply:
        intent = classify_command(command)

        if intent.kind is IntentType.HELP:
            return OracleReply(text=HELP_TEXT.strip())

        if intent.kind in {IntentType.LOCATION, IntentType.POSITION}:
            return OracleReply(
                text="Sending a private position packet.",
                share_position=True,
            )

        if intent.kind is IntentType.ASK and intent.question:
            context = self.retriever.search(intent.question)
            prompt = build_prompt(
                question=intent.question,
                context_chunks=context,
                max_words=self.max_words,
            )
            return OracleReply(text=self.llm.generate(prompt, max_words=self.max_words))

        return OracleReply(text="Send `help` for commands or `ask <question>` for counsel.")
