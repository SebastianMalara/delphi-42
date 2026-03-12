from __future__ import annotations

from pathlib import Path
from typing import Protocol


NO_GROUNDED_ANSWER = "The archive does not contain a grounded answer yet."
ARCHIVE_UNAVAILABLE = "The archive is temporarily unavailable."


class ModelUnavailableError(RuntimeError):
    """Raised when the configured local model cannot be used."""


class ModelExecutionError(RuntimeError):
    """Raised when a model backend fails during generation."""


class LLMRunner(Protocol):
    def generate(self, prompt: str, max_words: int = 40) -> str:
        ...


class RuleBasedRunner:
    """Deterministic fallback that summarizes the first retrieved passage."""

    def generate(self, prompt: str, max_words: int = 40) -> str:
        context = _extract_context(prompt)
        if not context or context == "(no matching passages)":
            return NO_GROUNDED_ANSWER
        first_line = context.splitlines()[0].removeprefix("- ").strip()
        return truncate_words(first_line, max_words)


class LlamaCppRunner:
    """High-level llama.cpp runner using llama-cpp-python when available."""

    def __init__(self, model_path: Path) -> None:
        if not model_path.exists():
            raise ModelUnavailableError(f"Configured GGUF model is missing: {model_path}")

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise ModelUnavailableError(
                "llama-cpp-python is not installed; install the optional llm dependency."
            ) from exc

        self.model_path = model_path
        try:
            self._llm = Llama(model_path=str(model_path))
        except Exception as exc:  # pragma: no cover - depends on native runtime state
            raise ModelUnavailableError(
                f"Failed to initialize llama.cpp model from {model_path}"
            ) from exc

    def generate(self, prompt: str, max_words: int = 40) -> str:
        try:
            output = self._llm(
                prompt,
                max_tokens=max(max_words * 3, 32),
                stop=["\nQuestion:", "\nContext:"],
                echo=False,
            )
        except Exception as exc:  # pragma: no cover - depends on native runtime state
            raise ModelExecutionError("llama.cpp generation failed") from exc

        try:
            text = output["choices"][0]["text"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelExecutionError("llama.cpp returned an unexpected response shape") from exc

        if not text:
            raise ModelExecutionError("llama.cpp returned an empty completion")
        return truncate_words(text, max_words)


def _extract_context(prompt: str) -> str:
    marker = "Context:\n"
    question_marker = "\n\nQuestion:\n"
    if marker not in prompt or question_marker not in prompt:
        return ""
    return prompt.split(marker, maxsplit=1)[1].split(question_marker, maxsplit=1)[0].strip()


def truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(".,;:") + "..."
