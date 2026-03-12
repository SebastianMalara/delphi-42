from pathlib import Path

import pytest

from bot.dev_console import build_dev_console
from bot.radio_interface import DryRunRadio
from core.runtime_config import ConfigError
from ingest.build_index import SQLiteIndexBuilder, build_chunks
from ingest.zim_extract import ExtractedDocument


def _build_index(index_path: Path) -> None:
    documents = [
        ExtractedDocument(
            title="Water Purification",
            source_id="water.txt",
            text="Boil water for one minute before drinking.",
        )
    ]
    SQLiteIndexBuilder(index_path).build(build_chunks(documents))


def test_build_dev_console_requires_simulated_transport(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: meshtastic
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="radio.transport"):
        build_dev_console(config_path)


def test_build_dev_console_uses_dry_run_radio(tmp_path: Path) -> None:
    index_path = tmp_path / "data/index/oracle.db"
    _build_index(index_path)

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    bot, radio, _ = build_dev_console(config_path)

    assert isinstance(bot.radio, DryRunRadio)
    assert isinstance(radio, DryRunRadio)
