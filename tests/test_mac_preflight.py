from __future__ import annotations

import json
from pathlib import Path

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
    - wikipedia_en_medicine_maxi_2023-12.zim
llm:
  backend: openai-compatible
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
    )

    zim_check = next(result for result in results if result.name == "zim-files")
    assert zim_check.ok is False
    assert "wikipedia_en_medicine_maxi_2023-12.zim" in zim_check.details
