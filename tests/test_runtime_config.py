from pathlib import Path

import pytest

from core.runtime_config import ConfigError, load_runtime_config


def test_load_runtime_config_applies_defaults_and_resolves_paths(tmp_path: Path) -> None:
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)
    (zim_dir / "medicine.zim").write_bytes(b"zim")

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
node_name: test-node
radio:
  transport: meshtastic
  device: /dev/ttyUSB1
knowledge:
  zim_dir: data/library/zim
  zim_allowlist:
    - medicine.zim
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path, root_dir=tmp_path)

    assert config.node_name == "test-node"
    assert config.radio.transport == "meshtastic"
    assert config.radio.device == "/dev/ttyUSB1"
    assert config.reply.short_max_chars == 120
    assert config.reply.condensed_max_chars == 600
    assert config.reply.max_total_packets == 6
    assert config.knowledge.zim_dir == zim_dir.resolve()
    assert config.knowledge.zim_allowlist == ("medicine.zim",)


def test_load_runtime_config_rejects_public_answers(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
privacy:
  answer_public_messages: true
knowledge:
  zim_allowlist:
    - medicine.zim
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="public mesh messages"):
        load_runtime_config(config_path, root_dir=tmp_path)


def test_load_runtime_config_rejects_unsupported_backend(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
llm:
  backend: remote-api
knowledge:
  zim_allowlist:
    - medicine.zim
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Unsupported llm.backend"):
        load_runtime_config(config_path, root_dir=tmp_path)


def test_load_runtime_config_accepts_legacy_backend_alias(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
llm:
  backend: axcl-openai
knowledge:
  zim_allowlist:
    - medicine.zim
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path, root_dir=tmp_path)

    assert config.llm.backend == "openai-compatible"


def test_load_runtime_config_rejects_invalid_reply_limits(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
reply:
  short_max_chars: 0
knowledge:
  zim_allowlist:
    - medicine.zim
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="reply.short_max_chars"):
        load_runtime_config(config_path, root_dir=tmp_path)


def test_load_runtime_config_rejects_empty_zim_allowlist(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
knowledge:
  zim_allowlist: []
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="knowledge.zim_allowlist"):
        load_runtime_config(config_path, root_dir=tmp_path)
