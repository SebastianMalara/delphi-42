from pathlib import Path

import pytest

from core.runtime_config import ConfigError, load_runtime_config


def test_load_runtime_config_applies_defaults_and_resolves_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
node_name: test-node
radio:
  device: /dev/ttyUSB1
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: data/index/oracle.db
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path, root_dir=tmp_path)

    assert config.node_name == "test-node"
    assert config.radio.device == "/dev/ttyUSB1"
    assert config.privacy.answer_public_messages is False
    assert config.llm.backend == "llama.cpp"
    assert config.knowledge.plaintext_dir == (tmp_path / "data/library/plaintext").resolve()
    assert config.knowledge.index_path == (tmp_path / "data/index/oracle.db").resolve()


def test_load_runtime_config_rejects_public_answers(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
privacy:
  answer_public_messages: true
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
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Unsupported llm.backend"):
        load_runtime_config(config_path, root_dir=tmp_path)
