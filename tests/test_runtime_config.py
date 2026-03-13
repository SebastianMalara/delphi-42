from pathlib import Path

import pytest

from core.runtime_config import ConfigError, load_runtime_config


def test_load_runtime_config_applies_defaults_and_resolves_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
node_name: test-node
radio:
  transport: meshtastic
  device: /dev/ttyUSB1
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: data/index/oracle.db
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path, root_dir=tmp_path)

    assert config.node_name == "test-node"
    assert config.radio.transport == "meshtastic"
    assert config.radio.device == "/dev/ttyUSB1"
    assert config.privacy.answer_public_messages is False
    assert config.llm.backend == "openai-compatible"
    assert config.llm.provider == "generic"
    assert config.llm.base_url == "http://127.0.0.1:8000/v1"
    assert config.llm.model == "qwen3-1.7B-Int8-ctx-axcl"
    assert config.reply.short_max_chars == 120
    assert config.knowledge.plaintext_dir == (tmp_path / "data/library/plaintext").resolve()
    assert config.knowledge.index_path == (tmp_path / "data/index/oracle.db").resolve()
    assert config.knowledge.zim_dir == (tmp_path / "data/library/zim").resolve()
    assert config.knowledge.runtime_zim_fallback_enabled is False
    assert config.knowledge.runtime_zim_search_limit == 3


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


def test_load_runtime_config_rejects_unsupported_provider(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
llm:
  provider: mystery-box
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Unsupported llm.provider"):
        load_runtime_config(config_path, root_dir=tmp_path)


def test_load_runtime_config_rejects_unsupported_radio_transport(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
radio:
  transport: satellite
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="Unsupported radio.transport"):
        load_runtime_config(config_path, root_dir=tmp_path)


def test_load_runtime_config_accepts_legacy_backend_alias(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
llm:
  backend: axcl-openai
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path, root_dir=tmp_path)

    assert config.llm.backend == "openai-compatible"


def test_load_runtime_config_accepts_provider_values(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
llm:
  provider: ovms
  base_url: http://127.0.0.1:8000/v3
  model: demo-model
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path, root_dir=tmp_path)

    assert config.llm.provider == "ovms"
    assert config.llm.base_url == "http://127.0.0.1:8000/v3"


def test_load_runtime_config_allows_simulated_transport_without_device(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
radio:
  transport: simulated
  device: ""
""".strip(),
        encoding="utf-8",
    )

    config = load_runtime_config(config_path, root_dir=tmp_path)

    assert config.radio.transport == "simulated"
    assert config.radio.device == ""


def test_repo_mac_config_profiles_load() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    sim_config = load_runtime_config(
        repo_root / "config/oracle.mac.sim.yaml",
        root_dir=repo_root,
    )
    live_config = load_runtime_config(
        repo_root / "config/oracle.mac.live.yaml",
        root_dir=repo_root,
    )

    assert sim_config.radio.transport == "simulated"
    assert sim_config.llm.provider == "lm-studio"
    assert sim_config.llm.base_url == "http://127.0.0.1:1234/v1"
    assert live_config.radio.transport == "meshtastic"
    assert live_config.radio.device.startswith("/dev/cu.usbmodem")


def test_repo_ubuntu_ovms_config_profiles_load() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    sim_config = load_runtime_config(
        repo_root / "config/oracle.ubuntu.ovms.sim.yaml",
        root_dir=repo_root,
    )
    live_config = load_runtime_config(
        repo_root / "config/oracle.ubuntu.ovms.live.yaml",
        root_dir=repo_root,
    )

    assert sim_config.radio.transport == "simulated"
    assert sim_config.llm.provider == "ovms"
    assert sim_config.llm.base_url == "http://127.0.0.1:8000/v3"
    assert live_config.radio.transport == "meshtastic"
    assert live_config.radio.device.startswith("/dev/ttyACM")


def test_load_runtime_config_rejects_invalid_reply_limits(tmp_path: Path) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
reply:
  short_max_chars: 0
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="reply.short_max_chars"):
        load_runtime_config(config_path, root_dir=tmp_path)


def test_load_runtime_config_rejects_enabled_zim_fallback_without_allowlist(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        """
knowledge:
  runtime_zim_fallback_enabled: true
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="runtime_zim_allowlist"):
        load_runtime_config(config_path, root_dir=tmp_path)
