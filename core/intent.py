from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.command import ParsedCommand


class IntentType(str, Enum):
    HELP = "help"
    LOCATION = "location"
    POSITION = "position"
    ASK = "ask"
    CHAT = "chat"
    MESH = "mesh"
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
    if command.name == "mesh":
        return Intent(kind=IntentType.MESH)
    if command.name == "ask" and command.argument:
        return Intent(kind=IntentType.ASK, question=command.argument)
    if command.name == "chat" and command.argument:
        return Intent(kind=IntentType.CHAT, question=command.argument)
    return Intent(kind=IntentType.UNKNOWN)
