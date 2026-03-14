from __future__ import annotations

import json
from pathlib import Path

from core.llm_runner import AnswerDraft, ModelExecutionError
from ingest.build_index import SQLiteIndexBuilder, build_chunks
from ingest.zim_extract import ExtractedDocument
from scripts.mac_preflight import run_preflight


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def _build_index(index_path: Path) -> None:
    documents = [
        ExtractedDocument(
            title="Water Purification",
            source_id="water.txt",
            text="Boil water for one minute before drinking.",
        )
    ]
    SQLiteIndexBuilder(index_path).build(build_chunks(documents))


def _import_ok(_: str) -> object:
    return object()


class FakeRunner:
    def __init__(self, *, fail_with: Exception | None = None, **_: object) -> None:
        self.fail_with = fail_with

    def generate(self, prompt: str) -> AnswerDraft:
        if self.fail_with is not None:
            raise self.fail_with
        return AnswerDraft(short_answer="ready", extended_answer=f"ready: {prompt}")


class PromptCapturingRunner(FakeRunner):
    last_prompt: str = ""

    def generate(self, prompt: str) -> AnswerDraft:
        type(self).last_prompt = prompt
        return super().generate(prompt)


def test_run_preflight_passes_for_simulated_mac_config(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-mac.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.mac.sim.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: lm-studio
  base_url: http://127.0.0.1:1234/v1
  model: lmstudio-qwen
  api_key: lm-studio
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse(
            {"data": [{"id": "lmstudio-qwen"}]}
        ),
        glob_fn=lambda pattern: ["/dev/cu.usbmodem1101"] if pattern.startswith("/dev/cu.") else [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    assert all(result.ok for result in results)


def test_run_preflight_flags_missing_live_serial_device(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-mac.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.mac.live.yaml"
    config_path.write_text(
        f"""
radio:
  transport: meshtastic
  device: /dev/cu.usbmodem9999
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: lm-studio
  base_url: http://127.0.0.1:1234/v1
  model: lmstudio-qwen
  api_key: lm-studio
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse(
            {"data": [{"id": "lmstudio-qwen"}]}
        ),
        glob_fn=lambda pattern: ["/dev/cu.usbmodem1101"] if pattern.startswith("/dev/cu.") else [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    serial_check = next(result for result in results if result.name == "serial-devices")
    assert serial_check.ok is False
    assert "/dev/cu.usbmodem9999" in serial_check.details


def test_run_preflight_flags_missing_zim_allowlist_files(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-mac.db"
    _build_index(index_path)
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)

    config_path = tmp_path / "oracle.mac.sim.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: {zim_dir}
  runtime_zim_fallback_enabled: true
  runtime_zim_allowlist:
    - medicine.zim
llm:
  backend: openai-compatible
  provider: lm-studio
  base_url: http://127.0.0.1:1234/v1
  model: lmstudio-qwen
  api_key: lm-studio
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse(
            {"data": [{"id": "lmstudio-qwen"}]}
        ),
        glob_fn=lambda pattern: [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    zim_check = next(result for result in results if result.name == "zim-files")
    assert zim_check.ok is False
    assert "medicine.zim" in zim_check.details


def test_run_preflight_flags_placeholder_values(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-mac.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.mac.live.yaml"
    config_path.write_text(
        f"""
radio:
  transport: meshtastic
  device: /dev/cu.usbmodemREPLACE_ME
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: lm-studio
  base_url: http://127.0.0.1:1234/v1
  model: replace-with-lmstudio-model-id
  api_key: lm-studio
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse(
            {"data": [{"id": "replace-with-lmstudio-model-id"}]}
        ),
        glob_fn=lambda pattern: ["/dev/cu.usbmodem1101"] if pattern.startswith("/dev/cu.") else [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    placeholder_check = next(result for result in results if result.name == "config-placeholders")
    assert placeholder_check.ok is False
    assert "radio.device" in placeholder_check.details
    assert "llm.model" in placeholder_check.details


def test_run_preflight_flags_completion_probe_failure(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-mac.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.mac.sim.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: lm-studio
  base_url: http://127.0.0.1:1234/v1
  model: lmstudio-qwen
  api_key: lm-studio
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse(
            {"data": [{"id": "lmstudio-qwen"}]}
        ),
        glob_fn=lambda pattern: [],
        runner_factory=lambda **kwargs: FakeRunner(
            fail_with=ModelExecutionError("OpenAI-compatible chat completion failed"),
            **kwargs,
        ),
    )

    completion_check = next(result for result in results if result.name == "llm-completion")
    assert completion_check.ok is False
    assert "chat completion failed" in completion_check.details


def test_run_preflight_accepts_ovms_provider_with_v3_base_url(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-ovms.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.ubuntu.ovms.sim.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: ovms
  base_url: http://127.0.0.1:8000/v3
  model: ovms-qwen
  api_key: sk-
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse({"data": [{"id": "ovms-qwen"}]}),
        glob_fn=lambda pattern: [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    assert all(result.ok for result in results)


def test_run_preflight_completion_probe_uses_structured_prompt(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-mac.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.mac.sim.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: lm-studio
  base_url: http://127.0.0.1:1234/v1
  model: lmstudio-qwen
  api_key: lm-studio
""".strip(),
        encoding="utf-8",
    )

    PromptCapturingRunner.last_prompt = ""
    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse(
            {"data": [{"id": "lmstudio-qwen"}]}
        ),
        glob_fn=lambda pattern: ["/dev/cu.usbmodem1101"] if pattern.startswith("/dev/cu.") else [],
        runner_factory=lambda **kwargs: PromptCapturingRunner(**kwargs),
    )

    completion_check = next(result for result in results if result.name == "llm-completion")
    assert completion_check.ok is True
    assert "Return exactly this format:" in PromptCapturingRunner.last_prompt
    assert "SHORT: <one-line direct answer>" in PromptCapturingRunner.last_prompt
    assert "LONG:" in PromptCapturingRunner.last_prompt


def test_run_preflight_flags_provider_path_mismatch(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-ovms.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.ubuntu.ovms.sim.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: ovms
  base_url: http://127.0.0.1:8000/v1
  model: ovms-qwen
  api_key: sk-
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse({"data": [{"id": "ovms-qwen"}]}),
        glob_fn=lambda pattern: [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    provider_check = next(result for result in results if result.name == "llm-provider")
    assert provider_check.ok is False
    assert "expects llm.base_url ending with '/v3'" in provider_check.details


def test_run_preflight_detects_linux_serial_devices(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-ovms.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.ubuntu.ovms.live.yaml"
    config_path.write_text(
        f"""
radio:
  transport: meshtastic
  device: /dev/ttyACM0
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: ovms
  base_url: http://127.0.0.1:8000/v3
  model: ovms-qwen
  api_key: sk-
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse({"data": [{"id": "ovms-qwen"}]}),
        glob_fn=lambda pattern: ["/dev/ttyACM0"] if pattern == "/dev/ttyACM*" else [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    serial_check = next(result for result in results if result.name == "serial-devices")
    assert serial_check.ok is True
    assert "/dev/ttyACM0" in serial_check.details


def test_run_preflight_detects_linux_by_id_serial_devices(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle-ovms.db"
    _build_index(index_path)
    by_id_path = "/dev/serial/by-id/usb-Heltec_HT-n5262_demo-if00"

    config_path = tmp_path / "oracle.ubuntu.ovms.live.yaml"
    config_path.write_text(
        f"""
radio:
  transport: meshtastic
  device: {by_id_path}
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: ovms
  base_url: http://127.0.0.1:8000/v3
  model: ovms-qwen
  api_key: sk-
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse({"data": [{"id": "ovms-qwen"}]}),
        glob_fn=lambda pattern: [by_id_path] if pattern == "/dev/serial/by-id/*" else [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    serial_check = next(result for result in results if result.name == "serial-devices")
    assert serial_check.ok is True
    assert by_id_path in serial_check.details


def test_run_preflight_lists_linux_by_id_devices_when_configured_device_is_missing(
    tmp_path: Path,
) -> None:
    index_path = tmp_path / "data/index/oracle-ovms.db"
    _build_index(index_path)
    configured_device = "/dev/ttyACM9"
    by_id_path = "/dev/serial/by-id/usb-Heltec_HT-n5262_demo-if00"

    config_path = tmp_path / "oracle.ubuntu.ovms.live.yaml"
    config_path.write_text(
        f"""
radio:
  transport: meshtastic
  device: {configured_device}
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: data/library/zim
  runtime_zim_fallback_enabled: false
llm:
  backend: openai-compatible
  provider: ovms
  base_url: http://127.0.0.1:8000/v3
  model: ovms-qwen
  api_key: sk-
""".strip(),
        encoding="utf-8",
    )

    _, results = run_preflight(
        config_path,
        import_module_fn=_import_ok,
        urlopen_fn=lambda req, timeout=0: FakeHTTPResponse({"data": [{"id": "ovms-qwen"}]}),
        glob_fn=lambda pattern: [by_id_path] if pattern == "/dev/serial/by-id/*" else [],
        runner_factory=lambda **kwargs: FakeRunner(**kwargs),
    )

    serial_check = next(result for result in results if result.name == "serial-devices")
    assert serial_check.ok is False
    assert configured_device in serial_check.details
    assert by_id_path in serial_check.details
