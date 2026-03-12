from types import SimpleNamespace

import pytest

from core.llm_runner import AXCLOpenAIRunner, ModelExecutionError, ModelUnavailableError


class FakeClient:
    def __init__(self, *, model_ids: list[str], content: str) -> None:
        self._model_ids = model_ids
        self._content = content
        self.models = SimpleNamespace(list=self._list_models)
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create_completion)
        )

    def _list_models(self) -> SimpleNamespace:
        return SimpleNamespace(data=[SimpleNamespace(id=model_id) for model_id in self._model_ids])

    def _create_completion(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self._content)
                )
            ]
        )


def test_axcl_openai_runner_preflights_model_and_parses_answer() -> None:
    runner = AXCLOpenAIRunner(
        base_url="http://127.0.0.1:8000/v1",
        model="qwen3-1.7B-Int8-ctx-axcl",
        client_factory=lambda **_: FakeClient(
            model_ids=["qwen3-1.7B-Int8-ctx-axcl"],
            content="SHORT: Boil water.\nLONG:\nBoil water for one minute before drinking.",
        ),
    )

    answer = runner.generate("prompt")

    assert answer.short_answer == "Boil water."
    assert "one minute" in answer.extended_answer


def test_axcl_openai_runner_rejects_missing_model() -> None:
    with pytest.raises(ModelUnavailableError, match="Configured model"):
        AXCLOpenAIRunner(
            base_url="http://127.0.0.1:8000/v1",
            model="qwen3-1.7B-Int8-ctx-axcl",
            client_factory=lambda **_: FakeClient(
                model_ids=["other-model"],
                content="SHORT: x\nLONG:\ny",
            ),
        )


def test_axcl_openai_runner_rejects_empty_completion() -> None:
    runner = AXCLOpenAIRunner(
        base_url="http://127.0.0.1:8000/v1",
        model="qwen3-1.7B-Int8-ctx-axcl",
        client_factory=lambda **_: FakeClient(
            model_ids=["qwen3-1.7B-Int8-ctx-axcl"],
            content="",
        ),
    )

    with pytest.raises(ModelExecutionError, match="empty completion"):
        runner.generate("prompt")
