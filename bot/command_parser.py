from __future__ import annotations

from dataclasses import dataclass

SUPPORTED_COMMANDS = {"help", "where", "pos", "ask"}

HELP_TEXT = """Commands:
help
where
pos
ask <question>
"""


@dataclass(frozen=True)
class ParsedCommand:
    name: str
    argument: str | None = None


def parse_command(message: str) -> ParsedCommand:
    """Parse a Meshtastic DM into a canonical command."""
    text = message.strip()
    if not text:
        return ParsedCommand(name="help")

    head, _, tail = text.partition(" ")
    command = head.lower()
    argument = tail.strip() or None

    if command in {"help", "where", "pos"}:
        return ParsedCommand(name=command)

    if command == "ask":
        if argument is None:
            return ParsedCommand(name="help")
        return ParsedCommand(name="ask", argument=argument)

    # Plain text is treated as an implicit ask request to keep the UX simple.
    return ParsedCommand(name="ask", argument=text)
