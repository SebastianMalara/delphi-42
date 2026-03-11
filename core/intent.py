from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from bot.command_parser import ParsedCommand


class IntentType(str, Enum):
    HELP = "help"
    LOCATION = "location"
    POSITION = "position"
    ASK = "ask"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Intent:
    kind: IntentType
    question: str | None = None


def classify_command(command: ParsedCommand) -> Intent:
    if command.name == "help":
        return Intent(kind=IntentType.HELP)
    if command.name == "where":
        return Intent(kind=IntentType.LOCATION)
    if command.name == "pos":
        return Intent(kind=IntentType.POSITION)
    if command.name == "ask" and command.argument:
        return Intent(kind=IntentType.ASK, question=command.argument)
    return Intent(kind=IntentType.UNKNOWN)
