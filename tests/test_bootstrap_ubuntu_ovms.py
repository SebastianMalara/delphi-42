import json
from pathlib import Path

import pytest

from core.runtime_config import load_runtime_config
from scripts.bootstrap_ubuntu_ovms import (
    BootstrapError,
    DEFAULT_KIWIX_URL,
    DEFAULT_MODEL,
    DEFAULT_ZIM_ALIAS,
    detect_heltec_radio_device,
    load_state,
    render_runtime_artifacts,
    resolve_archive,
    select_latest_archive_filename,
)
from scripts.manage_zims import add_file_archive


class FakeHTTPResponse:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload.encode("utf-8")

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_select_latest_archive_filename_prefers_newest_release() -> None:
    listing = """
    <a href="wikipedia_en_medicine_nopic_2025-10.zim">older</a>
    <a href="wikipedia_en_medicine_nopic_2026-01.zim">newer</a>
    <a href="wikipedia_en_medicine_nopic_2024-08.zim">oldest</a>
    """

    filename = select_latest_archive_filename("nopic", listing)

    assert filename == "wikipedia_en_medicine_nopic_2026-01.zim"


def test_resolve_archive_reuses_pinned_state_without_network(tmp_path: Path) -> None:
    state_path = tmp_path / "bootstrap-state.json"
    state_path.write_text(
        json.dumps(
            {
                "archive_profile": "nopic",
                "archive_filename": "wikipedia_en_medicine_nopic_2026-01.zim",
                "archive_url": "https://download.kiwix.org/zim/wikipedia/wikipedia_en_medicine_nopic_2026-01.zim",
                "archive_alias": DEFAULT_ZIM_ALIAS,
                "llm_model": DEFAULT_MODEL,
                "llm_base_url": "http://127.0.0.1:8000/v3",
                "radio_device": "/dev/serial/by-id/usb-Heltec-demo",
                "generated_at": "2026-03-13T16:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    archive = resolve_archive(
        "nopic",
        root=tmp_path,
        urlopen_fn=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("network not expected")),
    )

    assert archive.filename == "wikipedia_en_medicine_nopic_2026-01.zim"
    assert archive.alias == DEFAULT_ZIM_ALIAS


def test_detect_heltec_radio_device_rejects_multiple_candidates(tmp_path: Path) -> None:
    serial_root = tmp_path / "dev/serial/by-id"
    serial_root.mkdir(parents=True)
    tty_a = tmp_path / "dev/ttyACM1"
    tty_b = tmp_path / "dev/ttyACM2"
    tty_a.touch()
    tty_b.touch()
    (serial_root / "usb-Heltec_first-if00").symlink_to(tty_a)
    (serial_root / "usb-Heltec_second-if00").symlink_to(tty_b)

    with pytest.raises(BootstrapError, match="Multiple Heltec serial devices"):
        detect_heltec_radio_device("auto", serial_root=serial_root)


def test_render_runtime_artifacts_writes_kiwix_only_configs(tmp_path: Path) -> None:
    payload = render_runtime_artifacts(
        tmp_path,
        archive=resolve_archive(
            "nopic",
            override_url=(
                "https://download.kiwix.org/zim/wikipedia/"
                "wikipedia_en_medicine_nopic_2026-01.zim"
            ),
        ),
        base_url="http://127.0.0.1:8000/v3",
        kiwix_url=DEFAULT_KIWIX_URL,
        model=DEFAULT_MODEL,
        radio_device=Path("/dev/serial/by-id/usb-Heltec_HT-n5262_demo-if00"),
    )

    sim_config = load_runtime_config(Path(payload["sim_config_path"]), root_dir=tmp_path)
    live_config = load_runtime_config(Path(payload["live_config_path"]), root_dir=tmp_path)
    state = load_state(tmp_path)

    assert sim_config.radio.transport == "simulated"
    assert sim_config.knowledge.kiwix_url == DEFAULT_KIWIX_URL
    assert sim_config.knowledge.zim_allowlist == (DEFAULT_ZIM_ALIAS,)
    assert live_config.radio.device == "/dev/serial/by-id/usb-Heltec_HT-n5262_demo-if00"
    assert live_config.reply.short_max_chars == 100
    assert live_config.reply.condensed_max_chars == 600
    assert live_config.reply.max_total_packets == 7
    assert live_config.reply.ask_min_total_packets == 5
    assert live_config.reply.ask_max_total_packets == 7
    assert live_config.reply.chat_min_total_packets == 2
    assert live_config.reply.chat_max_total_packets == 4
    assert state is not None
    assert state.archive_filename == "wikipedia_en_medicine_nopic_2026-01.zim"


def test_render_runtime_artifacts_uses_registry_answer_allowlist(tmp_path: Path) -> None:
    source = tmp_path / "registry-source.zim"
    source.write_bytes(b"zim")
    add_file_archive(
        tmp_path,
        alias="appropedia.zim",
        source_path=source,
        answer_enabled=True,
    )

    payload = render_runtime_artifacts(
        tmp_path,
        archive=resolve_archive(
            "nopic",
            override_url=(
                "https://download.kiwix.org/zim/wikipedia/"
                "wikipedia_en_medicine_nopic_2026-01.zim"
            ),
        ),
        base_url="http://127.0.0.1:8000/v3",
        kiwix_url=DEFAULT_KIWIX_URL,
        model=DEFAULT_MODEL,
        radio_device=Path("/dev/serial/by-id/usb-Heltec_HT-n5262_demo-if00"),
    )

    sim_config = load_runtime_config(Path(payload["sim_config_path"]), root_dir=tmp_path)
    assert sim_config.knowledge.zim_allowlist == ("appropedia.zim",)


def test_bootstrap_script_reuses_existing_kiwix_runtime_layout() -> None:
    script_path = Path(__file__).resolve().parents[1] / "scripts/bootstrap_ubuntu_ovms.sh"
    script_text = script_path.read_text(encoding="utf-8")

    assert "--reuse-index" in script_text
    assert "--no-kiwix" in script_text
    assert "KIWIX_CONTAINER=\"delphi-kiwix\"" in script_text
    assert "Reusing staged Kiwix archives" in script_text
    assert "Managed archive registry is missing" in script_text
    assert f"MODEL_ID=\"{DEFAULT_MODEL}\"" in script_text
    assert "--tool_parser hermes3" in script_text
