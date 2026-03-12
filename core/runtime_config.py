from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


DEFAULT_BROADCAST_MESSAGES = (
    "THE ORACLE LISTENS. SEND DM FOR COUNSEL.",
    "ASH NODE AWAKE.",
    "SEEK WISDOM IN PRIVATE.",
)

SUPPORTED_LLM_BACKENDS = {"llama.cpp", "deterministic"}


class ConfigError(ValueError):
    """Raised when the Delphi-42 runtime configuration is invalid."""


@dataclass(frozen=True)
class RadioConfig:
    device: str = "/dev/ttyUSB0"
    channel: int = 0


@dataclass(frozen=True)
class PrivacyConfig:
    answer_public_messages: bool = False
    share_position_publicly: bool = False


@dataclass(frozen=True)
class BroadcastConfig:
    interval_minutes: int = 90
    messages: tuple[str, ...] = DEFAULT_BROADCAST_MESSAGES


@dataclass(frozen=True)
class KnowledgeConfig:
    plaintext_dir: Path
    index_path: Path
    kiwix_url: str = "http://127.0.0.1:8080"


@dataclass(frozen=True)
class LLMConfig:
    backend: str = "llama.cpp"
    model_path: Path = Path("models/oracle.gguf")
    max_words: int = 40


@dataclass(frozen=True)
class WiFiConfig:
    ssid: str = "DELPHI-42"


@dataclass(frozen=True)
class OracleRuntimeConfig:
    node_name: str
    radio: RadioConfig
    privacy: PrivacyConfig
    broadcasts: BroadcastConfig
    knowledge: KnowledgeConfig
    llm: LLMConfig
    wifi: WiFiConfig
    source_path: Path

    def summary(self) -> str:
        return (
            f"node={self.node_name} "
            f"radio_device={self.radio.device} "
            f"channel={self.radio.channel} "
            f"index={self.knowledge.index_path} "
            f"llm_backend={self.llm.backend} "
            f"max_words={self.llm.max_words}"
        )

    def validate_for_bot(self) -> None:
        if not self.knowledge.index_path.exists():
            raise ConfigError(
                f"Configured index path does not exist: {self.knowledge.index_path}"
            )


def load_runtime_config(
    path: Path,
    *,
    root_dir: Path | None = None,
) -> OracleRuntimeConfig:
    root_dir = (root_dir or Path.cwd()).resolve()
    raw_data = _read_yaml(path)

    config = OracleRuntimeConfig(
        node_name=str(raw_data.get("node_name", "delphi-42")).strip() or "delphi-42",
        radio=RadioConfig(
            device=str(raw_data.get("radio", {}).get("device", "/dev/ttyUSB0")).strip(),
            channel=int(raw_data.get("radio", {}).get("channel", 0)),
        ),
        privacy=PrivacyConfig(
            answer_public_messages=bool(
                raw_data.get("privacy", {}).get("answer_public_messages", False)
            ),
            share_position_publicly=bool(
                raw_data.get("privacy", {}).get("share_position_publicly", False)
            ),
        ),
        broadcasts=BroadcastConfig(
            interval_minutes=int(
                raw_data.get("broadcasts", {}).get("interval_minutes", 90)
            ),
            messages=_parse_broadcast_messages(raw_data),
        ),
        knowledge=KnowledgeConfig(
            plaintext_dir=_resolve_path(
                raw_data.get("knowledge", {}).get(
                    "plaintext_dir", "data/library/plaintext"
                ),
                root_dir,
            ),
            index_path=_resolve_path(
                raw_data.get("knowledge", {}).get("index_path", "data/index/oracle.db"),
                root_dir,
            ),
            kiwix_url=str(
                raw_data.get("knowledge", {}).get("kiwix_url", "http://127.0.0.1:8080")
            ),
        ),
        llm=LLMConfig(
            backend=str(raw_data.get("llm", {}).get("backend", "llama.cpp")).strip(),
            model_path=_resolve_path(
                raw_data.get("llm", {}).get("model_path", "models/oracle.gguf"),
                root_dir,
            ),
            max_words=int(raw_data.get("llm", {}).get("max_words", 40)),
        ),
        wifi=WiFiConfig(ssid=str(raw_data.get("wifi", {}).get("ssid", "DELPHI-42"))),
        source_path=path.resolve(),
    )
    _validate_runtime_config(config)
    return config


def _read_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file does not exist: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ConfigError("Config root must be a mapping.")
    return raw


def _resolve_path(raw_path: str | Path, root_dir: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (root_dir / path).resolve()


def _parse_broadcast_messages(raw_data: dict) -> tuple[str, ...]:
    raw_messages = raw_data.get("broadcasts", {}).get("messages", DEFAULT_BROADCAST_MESSAGES)
    if not isinstance(raw_messages, (list, tuple)):
        raise ConfigError("broadcasts.messages must be a list of strings.")

    messages = tuple(str(message).strip() for message in raw_messages if str(message).strip())
    return messages or DEFAULT_BROADCAST_MESSAGES


def _validate_runtime_config(config: OracleRuntimeConfig) -> None:
    if not config.radio.device:
        raise ConfigError("radio.device must not be empty.")
    if config.radio.channel < 0:
        raise ConfigError("radio.channel must be 0 or greater.")
    if config.broadcasts.interval_minutes <= 0:
        raise ConfigError("broadcasts.interval_minutes must be greater than 0.")
    if config.privacy.answer_public_messages:
        raise ConfigError("Prototype v1 forbids answering public mesh messages.")
    if config.privacy.share_position_publicly:
        raise ConfigError("Prototype v1 forbids sharing position publicly.")
    if config.llm.backend not in SUPPORTED_LLM_BACKENDS:
        raise ConfigError(
            f"Unsupported llm.backend '{config.llm.backend}'. "
            f"Supported values: {sorted(SUPPORTED_LLM_BACKENDS)}"
        )
    if config.llm.max_words <= 0:
        raise ConfigError("llm.max_words must be greater than 0.")
