from __future__ import annotations

import re
from typing import Any, Callable, Protocol


NO_GROUNDED_ANSWER = "The archive does not contain a grounded answer yet."
ARCHIVE_UNAVAILABLE = "The archive is temporarily unavailable."
CHAT_UNAVAILABLE = "Chat mode needs the local model right now."


class ModelUnavailableError(RuntimeError):
    """Raised when the configured local model cannot be used."""


class ModelExecutionError(RuntimeError):
    """Raised when a model backend fails during generation."""


class LLMRunner(Protocol):
    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        ...


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

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        return self._create_completion(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )

    def _create_completion(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        temperature: float,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            output = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
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
        return _strip_reasoning_markup(text)

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


_THINK_TAG_RE = re.compile(r"<think\b[^>]*>.*?</think>", re.IGNORECASE | re.DOTALL)


def _strip_reasoning_markup(text: str) -> str:
    stripped = _THINK_TAG_RE.sub("", text).strip()
    return stripped or text
