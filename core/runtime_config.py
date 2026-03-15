from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml


DEFAULT_BROADCAST_MESSAGES = (
    "THE ORACLE LISTENS. SEND DM FOR COUNSEL.",
    "ASH NODE AWAKE.",
    "SEEK WISDOM IN PRIVATE.",
)

OPENAI_COMPATIBLE_BACKEND = "openai-compatible"
LEGACY_OPENAI_BACKEND = "axcl-openai"
SUPPORTED_LLM_BACKENDS = {OPENAI_COMPATIBLE_BACKEND, LEGACY_OPENAI_BACKEND, "deterministic"}
GENERIC_OPENAI_PROVIDER = "generic"
STACKFLOW_PROVIDER = "stackflow"
LM_STUDIO_PROVIDER = "lm-studio"
OVMS_PROVIDER = "ovms"
SUPPORTED_LLM_PROVIDERS = {
    GENERIC_OPENAI_PROVIDER,
    STACKFLOW_PROVIDER,
    LM_STUDIO_PROVIDER,
    OVMS_PROVIDER,
}
SUPPORTED_RADIO_TRANSPORTS = {"meshtastic", "simulated"}


class ConfigError(ValueError):
    """Raised when the Delphi-42 runtime configuration is invalid."""


@dataclass(frozen=True)
class RadioConfig:
    transport: str = "meshtastic"
    device: str = "/dev/ttyUSB0"
    channel: int = 0
    text_packet_spacing_seconds: float = 8.0
    text_packet_retry_attempts: int = 2
    text_packet_retry_delay_seconds: float = 15.0
    max_text_payload_bytes: int = 120


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
    kiwix_url: str = "http://127.0.0.1:8080"
    zim_dir: Path = Path("data/library/zim")
    zim_allowlist: tuple[str, ...] = ()
    zim_search_limit: int = 3


@dataclass(frozen=True)
class LLMConfig:
    backend: str = OPENAI_COMPATIBLE_BACKEND
    provider: str = GENERIC_OPENAI_PROVIDER
    base_url: str = "http://127.0.0.1:8000/v1"
    model: str = "qwen3-1.7B-Int8-ctx-axcl"
    api_key: str = "sk-"
    timeout_seconds: int = 45


@dataclass(frozen=True)
class ReplyConfig:
    short_max_chars: int = 120
    condensed_max_chars: int = 600
    max_total_packets: int = 6
    ask_min_total_packets: Optional[int] = None
    ask_max_total_packets: Optional[int] = None
    chat_min_total_packets: Optional[int] = None
    chat_max_total_packets: Optional[int] = None


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
            f"radio_payload_bytes={self.radio.max_text_payload_bytes} "
            f"zim_dir={self.knowledge.zim_dir} "
            f"llm_backend={self.llm.backend} "
            f"llm_provider={self.llm.provider} "
            f"llm_model={self.llm.model} "
            f"zim_allowlist={','.join(self.knowledge.zim_allowlist) or '-'} "
            f"reply_short_max={self.reply.short_max_chars}"
        )

    def validate_for_bot(self) -> None:
        if not self.knowledge.zim_dir.exists():
            raise ConfigError(
                f"Configured zim_dir does not exist: {self.knowledge.zim_dir}"
            )
        missing = [
            filename
            for filename in self.knowledge.zim_allowlist
            if not (self.knowledge.zim_dir / filename).exists()
        ]
        if missing:
            raise ConfigError(
                "Configured zim_allowlist files are missing: "
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
            text_packet_spacing_seconds=float(
                raw_data.get("radio", {}).get("text_packet_spacing_seconds", 8.0)
            ),
            text_packet_retry_attempts=int(
                raw_data.get("radio", {}).get("text_packet_retry_attempts", 2)
            ),
            text_packet_retry_delay_seconds=float(
                raw_data.get("radio", {}).get("text_packet_retry_delay_seconds", 15.0)
            ),
            max_text_payload_bytes=int(
                raw_data.get("radio", {}).get("max_text_payload_bytes", 120)
            ),
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
            kiwix_url=str(
                raw_data.get("knowledge", {}).get("kiwix_url", "http://127.0.0.1:8080")
            ),
            zim_dir=_resolve_path(
                raw_data.get("knowledge", {}).get("zim_dir", "data/library/zim"),
                root_dir,
            ),
            zim_allowlist=_parse_string_tuple(
                raw_data.get("knowledge", {}).get("zim_allowlist", ())
            ),
            zim_search_limit=int(
                raw_data.get("knowledge", {}).get("zim_search_limit", 3)
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
            provider=str(
                raw_data.get("llm", {}).get("provider", GENERIC_OPENAI_PROVIDER)
            ).strip(),
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
            condensed_max_chars=int(
                raw_data.get("reply", {}).get("condensed_max_chars", 600)
            ),
            max_total_packets=int(
                raw_data.get("reply", {}).get("max_total_packets", 6)
            ),
            ask_min_total_packets=_optional_int(
                raw_data.get("reply", {}).get("ask_min_total_packets")
            ),
            ask_max_total_packets=_optional_int(
                raw_data.get("reply", {}).get("ask_max_total_packets")
            ),
            chat_min_total_packets=_optional_int(
                raw_data.get("reply", {}).get("chat_min_total_packets")
            ),
            chat_max_total_packets=_optional_int(
                raw_data.get("reply", {}).get("chat_max_total_packets")
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


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


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
    if config.radio.text_packet_spacing_seconds < 0:
        raise ConfigError("radio.text_packet_spacing_seconds must be 0 or greater.")
    if config.radio.text_packet_retry_attempts < 0:
        raise ConfigError("radio.text_packet_retry_attempts must be 0 or greater.")
    if config.radio.text_packet_retry_delay_seconds < 0:
        raise ConfigError("radio.text_packet_retry_delay_seconds must be 0 or greater.")
    if config.radio.max_text_payload_bytes < 0:
        raise ConfigError("radio.max_text_payload_bytes must be 0 or greater.")
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
    if config.llm.provider not in SUPPORTED_LLM_PROVIDERS:
        raise ConfigError(
            f"Unsupported llm.provider '{config.llm.provider}'. "
            f"Supported values: {sorted(SUPPORTED_LLM_PROVIDERS)}"
        )
    if config.llm.backend == OPENAI_COMPATIBLE_BACKEND:
        if not config.llm.base_url:
            raise ConfigError("llm.base_url must not be empty for openai-compatible.")
        if not config.llm.model:
            raise ConfigError("llm.model must not be empty for openai-compatible.")
    if config.llm.timeout_seconds <= 0:
        raise ConfigError("llm.timeout_seconds must be greater than 0.")
    if config.knowledge.zim_search_limit <= 0:
        raise ConfigError("knowledge.zim_search_limit must be greater than 0.")
    if not config.knowledge.zim_allowlist:
        raise ConfigError("knowledge.zim_allowlist must not be empty.")
    if config.reply.short_max_chars <= 0:
        raise ConfigError("reply.short_max_chars must be greater than 0.")
    if config.reply.condensed_max_chars <= 0:
        raise ConfigError("reply.condensed_max_chars must be greater than 0.")
    if config.reply.max_total_packets <= 0:
        raise ConfigError("reply.max_total_packets must be greater than 0.")
    if (
        config.reply.ask_min_total_packets is not None
        and config.reply.ask_min_total_packets <= 0
    ):
        raise ConfigError("reply.ask_min_total_packets must be greater than 0.")
    if (
        config.reply.ask_max_total_packets is not None
        and config.reply.ask_max_total_packets <= 0
    ):
        raise ConfigError("reply.ask_max_total_packets must be greater than 0.")
    if (
        config.reply.chat_min_total_packets is not None
        and config.reply.chat_min_total_packets <= 0
    ):
        raise ConfigError("reply.chat_min_total_packets must be greater than 0.")
    if (
        config.reply.chat_max_total_packets is not None
        and config.reply.chat_max_total_packets <= 0
    ):
        raise ConfigError("reply.chat_max_total_packets must be greater than 0.")
    if (
        config.reply.ask_min_total_packets is not None
        and config.reply.ask_max_total_packets is not None
        and config.reply.ask_min_total_packets > config.reply.ask_max_total_packets
    ):
        raise ConfigError("reply.ask_min_total_packets must be less than or equal to reply.ask_max_total_packets.")
    if (
        config.reply.chat_min_total_packets is not None
        and config.reply.chat_max_total_packets is not None
        and config.reply.chat_min_total_packets > config.reply.chat_max_total_packets
    ):
        raise ConfigError("reply.chat_min_total_packets must be less than or equal to reply.chat_max_total_packets.")
