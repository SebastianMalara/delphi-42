from __future__ import annotations

from core.command import ParsedCommand  # canonical definition lives in core

SUPPORTED_COMMANDS = {"help", "where", "pos", "ask", "chat", "mesh"}

HELP_TEXT = """Commands:
?help
?where
?pos
?ask <question>
?chat <message>
?mesh

Examples:
?ask how to purify water
?chat keep me company
?mesh
"""

__all__ = ["ParsedCommand", "parse_command", "SUPPORTED_COMMANDS", "HELP_TEXT"]


def parse_command(message: str) -> ParsedCommand:
    """Parse a Meshtastic DM into a canonical command."""
    text = message.strip()
    if not text:
        return ParsedCommand(name="help")

    if not text.startswith("?"):
        return ParsedCommand(name="help")

    head, _, tail = text.partition(" ")
    command = head[1:].lower()
    argument = tail.strip() or None

    if command in {"help", "where", "pos", "mesh"}:
        return ParsedCommand(name=command)

    if command in {"ask", "chat"}:
        if argument is None:
            return ParsedCommand(name="help")
        return ParsedCommand(name=command, argument=argument)

    return ParsedCommand(name="help")
