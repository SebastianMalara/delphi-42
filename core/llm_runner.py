from __future__ import annotations

from typing import Protocol


class LLMRunner(Protocol):
    def generate(self, prompt: str, max_words: int = 40) -> str:
        ...


class RuleBasedRunner:
    """Deterministic fallback until a real local LLM is wired in."""

    def generate(self, prompt: str, max_words: int = 40) -> str:
        context = _extract_context(prompt)
        if not context or context == "(no matching passages)":
            return "The archive does not contain a grounded answer yet."
        first_line = context.splitlines()[0].removeprefix("- ").strip()
        return _truncate_words(first_line, max_words)


def _extract_context(prompt: str) -> str:
    marker = "Context:\n"
    question_marker = "\n\nQuestion:\n"
    if marker not in prompt or question_marker not in prompt:
        return ""
    return prompt.split(marker, maxsplit=1)[1].split(question_marker, maxsplit=1)[0].strip()


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,;:") + "..."
