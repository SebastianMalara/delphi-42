from pathlib import Path

import pytest

from bot.dev_console import build_dev_console
from bot.radio_interface import DryRunRadio
from core.runtime_config import ConfigError


def test_build_dev_console_requires_simulated_transport(tmp_path: Path) -> None:
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)
    (zim_dir / "medicine.zim").write_bytes(b"zim")

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: meshtastic
knowledge:
  zim_dir: {zim_dir}
  zim_allowlist:
    - medicine.zim
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="radio.transport"):
        build_dev_console(config_path)


def test_build_dev_console_uses_dry_run_radio(tmp_path: Path, monkeypatch) -> None:
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)
    (zim_dir / "medicine.zim").write_bytes(b"zim")

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  zim_dir: {zim_dir}
  zim_allowlist:
    - medicine.zim
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "bot.oracle_bot.KiwixRetriever",
        lambda *args, **kwargs: object(),
    )

    bot, radio, _ = build_dev_console(config_path)

    assert isinstance(bot.radio, DryRunRadio)
    assert isinstance(radio, DryRunRadio)
