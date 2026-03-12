from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


DEFAULT_BROADCAST_MESSAGES = (
    "THE ORACLE LISTENS. SEND DM FOR COUNSEL.",
    "ASH NODE AWAKE.",
    "SEEK WISDOM IN PRIVATE.",
)

OPENAI_COMPATIBLE_BACKEND = "openai-compatible"
LEGACY_OPENAI_BACKEND = "axcl-openai"
SUPPORTED_LLM_BACKENDS = {OPENAI_COMPATIBLE_BACKEND, LEGACY_OPENAI_BACKEND, "deterministic"}
SUPPORTED_RADIO_TRANSPORTS = {"meshtastic", "simulated"}


class ConfigError(ValueError):
    """Raised when the Delphi-42 runtime configuration is invalid."""


@dataclass(frozen=True)
class RadioConfig:
    transport: str = "meshtastic"
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
    zim_dir: Path = Path("data/library/zim")
    runtime_zim_fallback_enabled: bool = False
    runtime_zim_allowlist: tuple[str, ...] = ()
    runtime_zim_search_limit: int = 3


@dataclass(frozen=True)
class LLMConfig:
    backend: str = OPENAI_COMPATIBLE_BACKEND
    base_url: str = "http://127.0.0.1:8000/v1"
    model: str = "qwen3-1.7B-Int8-ctx-axcl"
    api_key: str = "sk-"
    timeout_seconds: int = 45


@dataclass(frozen=True)
class ReplyConfig:
    short_max_chars: int = 120
    continuation_max_chars: int = 600
    max_continuation_packets: int = 3


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
    reply: ReplyConfig
    wifi: WiFiConfig
    source_path: Path

    def summary(self) -> str:
        return (
            f"node={self.node_name} "
            f"radio_transport={self.radio.transport} "
            f"radio_device={self.radio.device or '-'} "
            f"channel={self.radio.channel} "
            f"index={self.knowledge.index_path} "
            f"llm_backend={self.llm.backend} "
            f"llm_model={self.llm.model} "
            f"zim_fallback={self.knowledge.runtime_zim_fallback_enabled} "
            f"reply_short_max={self.reply.short_max_chars}"
        )

    def validate_for_bot(self) -> None:
        if not self.knowledge.index_path.exists():
            raise ConfigError(
                f"Configured index path does not exist: {self.knowledge.index_path}"
            )
        if self.knowledge.runtime_zim_fallback_enabled:
            if not self.knowledge.zim_dir.exists():
                raise ConfigError(
                    f"Configured zim_dir does not exist: {self.knowledge.zim_dir}"
                )
            missing = [
                filename
                for filename in self.knowledge.runtime_zim_allowlist
                if not (self.knowledge.zim_dir / filename).exists()
            ]
            if missing:
                raise ConfigError(
                    "Configured runtime_zim_allowlist files are missing: "
                    + ", ".join(missing)
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
            transport=str(
                raw_data.get("radio", {}).get("transport", "meshtastic")
            ).strip(),
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
            zim_dir=_resolve_path(
                raw_data.get("knowledge", {}).get("zim_dir", "data/library/zim"),
                root_dir,
            ),
            runtime_zim_fallback_enabled=bool(
                raw_data.get("knowledge", {}).get(
                    "runtime_zim_fallback_enabled", False
                )
            ),
            runtime_zim_allowlist=_parse_string_tuple(
                raw_data.get("knowledge", {}).get("runtime_zim_allowlist", ())
            ),
            runtime_zim_search_limit=int(
                raw_data.get("knowledge", {}).get("runtime_zim_search_limit", 3)
            ),
        ),
        llm=LLMConfig(
            backend=_normalize_backend(
                str(
                    raw_data.get("llm", {}).get(
                        "backend", OPENAI_COMPATIBLE_BACKEND
                    )
                ).strip()
            ),
            base_url=str(
                raw_data.get("llm", {}).get("base_url", "http://127.0.0.1:8000/v1")
            ).strip(),
            model=str(
                raw_data.get("llm", {}).get("model", "qwen3-1.7B-Int8-ctx-axcl")
            ).strip(),
            api_key=str(raw_data.get("llm", {}).get("api_key", "sk-")).strip(),
            timeout_seconds=int(raw_data.get("llm", {}).get("timeout_seconds", 45)),
        ),
        reply=ReplyConfig(
            short_max_chars=int(raw_data.get("reply", {}).get("short_max_chars", 120)),
            continuation_max_chars=int(
                raw_data.get("reply", {}).get("continuation_max_chars", 600)
            ),
            max_continuation_packets=int(
                raw_data.get("reply", {}).get("max_continuation_packets", 3)
            ),
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


def _parse_string_tuple(raw_values: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(raw_values, (list, tuple)):
        raise ConfigError("Expected a list of strings.")
    return tuple(str(value).strip() for value in raw_values if str(value).strip())


def _normalize_backend(backend: str) -> str:
    if backend == LEGACY_OPENAI_BACKEND:
        return OPENAI_COMPATIBLE_BACKEND
    return backend


def _validate_runtime_config(config: OracleRuntimeConfig) -> None:
    if config.radio.transport not in SUPPORTED_RADIO_TRANSPORTS:
        raise ConfigError(
            f"Unsupported radio.transport '{config.radio.transport}'. "
            f"Supported values: {sorted(SUPPORTED_RADIO_TRANSPORTS)}"
        )
    if config.radio.transport == "meshtastic" and not config.radio.device:
        raise ConfigError("radio.device must not be empty when radio.transport is meshtastic.")
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
    if config.llm.backend == OPENAI_COMPATIBLE_BACKEND:
        if not config.llm.base_url:
            raise ConfigError("llm.base_url must not be empty for openai-compatible.")
        if not config.llm.model:
            raise ConfigError("llm.model must not be empty for openai-compatible.")
    if config.llm.timeout_seconds <= 0:
        raise ConfigError("llm.timeout_seconds must be greater than 0.")
    if config.knowledge.runtime_zim_search_limit <= 0:
        raise ConfigError("knowledge.runtime_zim_search_limit must be greater than 0.")
    if (
        config.knowledge.runtime_zim_fallback_enabled
        and not config.knowledge.runtime_zim_allowlist
    ):
        raise ConfigError(
            "knowledge.runtime_zim_allowlist must not be empty when "
            "runtime_zim_fallback_enabled is true."
        )
    if config.reply.short_max_chars <= 0:
        raise ConfigError("reply.short_max_chars must be greater than 0.")
    if config.reply.continuation_max_chars <= 0:
        raise ConfigError("reply.continuation_max_chars must be greater than 0.")
    if config.reply.max_continuation_packets < 0:
        raise ConfigError("reply.max_continuation_packets must be 0 or greater.")
