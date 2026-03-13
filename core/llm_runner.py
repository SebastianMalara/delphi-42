from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


NO_GROUNDED_ANSWER = "The archive does not contain a grounded answer yet."
ARCHIVE_UNAVAILABLE = "The archive is temporarily unavailable."


class ModelUnavailableError(RuntimeError):
    """Raised when the configured local model cannot be used."""


class ModelExecutionError(RuntimeError):
    """Raised when a model backend fails during generation."""


@dataclass(frozen=True)
class AnswerDraft:
    short_answer: str
    extended_answer: str


class LLMRunner(Protocol):
    def generate(self, prompt: str) -> AnswerDraft:
        ...


class RuleBasedRunner:
    """Deterministic fallback that summarizes the first retrieved passage."""

    def generate(self, prompt: str) -> AnswerDraft:
        context = _extract_context(prompt)
        if not context or context == "(no matching passages)":
            return AnswerDraft(NO_GROUNDED_ANSWER, NO_GROUNDED_ANSWER)

        first_line = context.splitlines()[0].removeprefix("- ").strip()
        return AnswerDraft(short_answer=first_line, extended_answer=first_line)


class OpenAICompatibleRunner:
    """OpenAI-compatible local runner for host-local inference services."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str = "sk-",
        timeout_seconds: int = 45,
        client_factory: Callable[..., Any] | None = None,
    ) -> None:
        self.base_url = base_url
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

        if client_factory is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ModelUnavailableError(
                    "openai is not installed; install the optional llm dependency."
                ) from exc
            client_factory = OpenAI

        try:
            self._client = client_factory(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=self.timeout_seconds,
            )
        except Exception as exc:
            raise ModelUnavailableError("Failed to initialize local OpenAI client") from exc

        self._preflight_model()

    def generate(self, prompt: str) -> AnswerDraft:
        text = self._create_completion(prompt)
        return parse_answer_draft(text)

    def generate_long_answer(self, prompt: str) -> str:
        return self._create_completion(prompt)

    def _create_completion(self, prompt: str) -> str:
        try:
            output = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
        except Exception as exc:
            raise ModelExecutionError("OpenAI-compatible chat completion failed") from exc

        try:
            message = output.choices[0].message
            text = _coerce_content(getattr(message, "content", ""))
        except (AttributeError, IndexError, TypeError) as exc:
            raise ModelExecutionError("OpenAI-compatible API returned an unexpected shape") from exc

        if not text:
            raise ModelExecutionError("OpenAI-compatible API returned an empty completion")
        return text

    def _preflight_model(self) -> None:
        try:
            response = self._client.models.list()
        except Exception as exc:
            raise ModelUnavailableError("Local OpenAI-compatible API is unavailable") from exc

        models = [getattr(model, "id", "") for model in getattr(response, "data", [])]
        if not models:
            raise ModelUnavailableError("Local OpenAI-compatible API returned no models")
        if self.model not in models:
            raise ModelUnavailableError(
                f"Configured model '{self.model}' is not available from the local API"
            )


AXCLOpenAIRunner = OpenAICompatibleRunner


def parse_answer_draft(text: str) -> AnswerDraft:
    raw = " ".join(text.strip().split())
    if not raw:
        raise ModelExecutionError("Model returned an empty answer draft")

    short_marker = "SHORT:"
    long_marker = "LONG:"
    if short_marker not in text or long_marker not in text:
        raise ModelExecutionError(
            "OpenAI-compatible API did not return the required SHORT/LONG format"
        )

    short_part = text.split(short_marker, maxsplit=1)[1].split(long_marker, maxsplit=1)[0]
    long_part = text.split(long_marker, maxsplit=1)[1]
    short = " ".join(short_part.strip().split())
    extended = " ".join(long_part.strip().split())
    if not short or not extended:
        raise ModelExecutionError("OpenAI-compatible API returned an incomplete SHORT/LONG answer")
    return AnswerDraft(short_answer=short, extended_answer=extended)


def _coerce_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
                continue
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
        return " ".join(part.strip() for part in parts if part and part.strip())
    return str(content).strip()


def _extract_context(prompt: str) -> str:
    marker = "Context:\n"
    question_marker = "\n\nQuestion:\n"
    if marker not in prompt or question_marker not in prompt:
        return ""
    return prompt.split(marker, maxsplit=1)[1].split(question_marker, maxsplit=1)[0].strip()
