from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Callable

from core.llm_runner import LLMRunner, ModelUnavailableError, OpenAICompatibleRunner
from core.oracle_service import OracleService
from core.retriever import SQLiteRetriever
from core.runtime_config import ConfigError, OracleRuntimeConfig, load_runtime_config
from core.zim_retriever import RuntimeZimRetriever

from .message_router import MessageRouter, RoutedReply
from .radio_interface import (
    DryRunRadio,
    MeshtasticRadioClient,
    OutboundMessage,
    PositionUnavailableError,
    RadioClient,
    RadioTransportError,
)


LOGGER = logging.getLogger("delphi42.bot")
POSITION_UNAVAILABLE_TEXT = "Position fix unavailable right now."


class OracleBot:
    """Long-running bot loop for the Delphi-42 runtime."""

    def __init__(
        self,
        radio: RadioClient,
        router: MessageRouter,
        *,
        logger: logging.Logger | None = None,
        radio_factory: Callable[[], RadioClient] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        reconnect_backoff_seconds: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0, 30.0),
        text_packet_spacing_seconds: float = 0.0,
        text_packet_retry_attempts: int = 0,
        text_packet_retry_delay_seconds: float = 0.0,
        max_text_payload_bytes: int = 0,
    ) -> None:
        self.radio = radio
        self.router = router
        self.logger = logger or LOGGER
        self.radio_factory = radio_factory or (lambda: radio)
        self.sleep_fn = sleep_fn
        self.reconnect_backoff_seconds = reconnect_backoff_seconds
        self.text_packet_spacing_seconds = text_packet_spacing_seconds
        self.text_packet_retry_attempts = text_packet_retry_attempts
        self.text_packet_retry_delay_seconds = text_packet_retry_delay_seconds
        self.max_text_payload_bytes = max_text_payload_bytes

    def process_inbox(self) -> list[str]:
        delivery_log: list[str] = []
        for message in self.radio.receive():
            routed = self.router.route(message)
            if routed is None:
                self.logger.info(
                    "ignored inbound packet sender=%s channel=%s direct=%s",
                    message.sender_id,
                    message.channel,
                    message.is_direct_message,
                )
                continue

            delivery_log.extend(self._deliver(routed))
        return delivery_log

    def run_forever(self, poll_interval_seconds: float = 1.0) -> None:
        try:
            while True:
                try:
                    self.process_inbox()
                except RadioTransportError as exc:
                    self.logger.warning("radio transport failure: %s", exc)
                    self._recover_radio()
                    continue
                self.sleep_fn(poll_interval_seconds)
        finally:
            self._safe_close_radio()

    def _deliver(self, routed: RoutedReply) -> list[str]:
        events: list[str] = []
        packet_total = len(routed.reply.packets)
        packet_index = 0
        for response in routed.messages:
            if response.send_position:
                outbound, delivery_kind = self._send_response(response)
                event = self._delivery_event(
                    outbound=outbound,
                    delivery_kind=delivery_kind,
                    routed=routed,
                )
                self.logger.info(event)
                events.append(event)
                continue

            packet_index += 1
            if packet_index > 1 and self.text_packet_spacing_seconds > 0:
                self.sleep_fn(self.text_packet_spacing_seconds)

            outbound = self._trim_text_response(response)
            packet_bytes = len(outbound.text.encode("utf-8"))
            delivered = False
            max_attempts = self.text_packet_retry_attempts + 1

            for attempt in range(1, max_attempts + 1):
                try:
                    sent, delivery_kind = self._send_response(outbound)
                except RadioTransportError as exc:
                    self.logger.warning(
                        "packet send failed destination=%s packet=%s/%s attempt=%s: %s",
                        outbound.destination,
                        packet_index,
                        packet_total,
                        attempt,
                        exc,
                    )
                    if attempt >= max_attempts:
                        status = (
                            "delivery_failed" if packet_index == 1 else "delivery_incomplete"
                        )
                        summary = (
                            f"to={outbound.destination} channel={outbound.channel} "
                            f"status={status} mode={routed.reply.mode.value} "
                            f"packet_index={packet_index} packet_total={packet_total} "
                            f"packet_count={packet_total}"
                        )
                        self.logger.warning(summary)
                        events.append(summary)
                        return events
                    self._recover_radio()
                    if self.text_packet_retry_delay_seconds > 0:
                        self.sleep_fn(self.text_packet_retry_delay_seconds)
                    continue

                event = self._delivery_event(
                    outbound=sent,
                    delivery_kind=delivery_kind,
                    routed=routed,
                    packet_index=packet_index,
                    packet_total=packet_total,
                    packet_bytes=packet_bytes,
                    send_attempt=attempt,
                )
                self.logger.info(event)
                events.append(event)
                delivered = True
                break

            if not delivered:
                return events

        summary = (
            f"to={routed.inbound.sender_id} channel={routed.inbound.channel} "
            f"status=delivery_complete mode={routed.reply.mode.value} "
            f"packet_count={packet_total}"
        )
        self.logger.info(summary)
        events.append(summary)
        return events

    def _send_response(self, response: OutboundMessage) -> tuple[OutboundMessage, str]:
        if not response.send_position:
            self.radio.send_text(response)
            return response, "text"

        try:
            self.radio.send_position(response)
            return response, "position"
        except PositionUnavailableError as exc:
            fallback = OutboundMessage(
                destination=response.destination,
                text=POSITION_UNAVAILABLE_TEXT,
                channel=response.channel,
            )
            self.logger.warning("position unavailable for %s: %s", response.destination, exc)
            self.radio.send_text(fallback)
            return fallback, "text"

    def _trim_text_response(self, response: OutboundMessage) -> OutboundMessage:
        if response.send_position or self.max_text_payload_bytes <= 0:
            return response

        return OutboundMessage(
            destination=response.destination,
            text=_trim_to_utf8_bytes(response.text, self.max_text_payload_bytes),
            channel=response.channel,
            send_position=False,
        )

    def _delivery_event(
        self,
        *,
        outbound: OutboundMessage,
        delivery_kind: str,
        routed: RoutedReply,
        packet_index: int | None = None,
        packet_total: int | None = None,
        packet_bytes: int | None = None,
        send_attempt: int | None = None,
    ) -> str:
        parts = [
            f"to={outbound.destination}",
            f"channel={outbound.channel}",
            f"kind={delivery_kind}",
            f"mode={routed.reply.mode.value}",
            f"hits={routed.reply.retrieval_hits}",
            f"retrieval={routed.reply.retrieval_source}",
            f"confidence={routed.reply.retrieval_confidence}",
            f"packet_count={len(routed.reply.packets)}",
            f"sources={','.join(routed.reply.retrieval_sources) or '-'}",
            f"titles={','.join(routed.reply.retrieval_titles) or '-'}",
            f"scores={','.join(str(score) for score in routed.reply.retrieval_scores) or '-'}",
        ]
        if packet_index is not None and packet_total is not None:
            parts.append(f"packet_index={packet_index}")
            parts.append(f"packet_total={packet_total}")
        if packet_bytes is not None:
            parts.append(f"packet_bytes={packet_bytes}")
        if send_attempt is not None:
            parts.append(f"send_attempt={send_attempt}")
        return " ".join(parts)

    def _recover_radio(self) -> None:
        self._safe_close_radio()
        attempt = 0
        delays = self.reconnect_backoff_seconds or (0.0,)
        while True:
            delay = delays[min(attempt, len(delays) - 1)]
            if delay > 0:
                self.sleep_fn(delay)
            try:
                self.radio = self.radio_factory()
            except Exception as exc:
                attempt += 1
                self.logger.warning(
                    "radio reconnect attempt %s failed on the configured path: %s",
                    attempt,
                    exc,
                )
                continue

            self.logger.info("radio reconnect succeeded on the configured path")
            return

    def _safe_close_radio(self) -> None:
        try:
            self.radio.close()
        except Exception as exc:
            self.logger.warning("radio close failed during recovery: %s", exc)


def load_config(path: Path) -> OracleRuntimeConfig:
    root_dir = path.parent.parent if path.parent.name == "config" else path.parent
    return load_runtime_config(path, root_dir=root_dir)


def build_oracle_bot(
    config_path: Path,
    *,
    logger: logging.Logger | None = None,
) -> OracleBot:
    logger = logger or LOGGER
    config = load_config(config_path)
    config.validate_for_bot()
    logger.info("loaded config %s", config.summary())

    router = build_router(config, logger=logger)
    radio_factory = lambda: build_radio(config, logger=logger)
    radio = radio_factory()
    return OracleBot(
        radio=radio,
        router=router,
        logger=logger,
        radio_factory=radio_factory,
        text_packet_spacing_seconds=config.radio.text_packet_spacing_seconds,
        text_packet_retry_attempts=config.radio.text_packet_retry_attempts,
        text_packet_retry_delay_seconds=config.radio.text_packet_retry_delay_seconds,
        max_text_payload_bytes=config.radio.max_text_payload_bytes,
    )


def build_router(
    config: OracleRuntimeConfig,
    *,
    logger: logging.Logger | None = None,
) -> MessageRouter:
    logger = logger or LOGGER
    retriever = SQLiteRetriever(config.knowledge.index_path)
    fallback_retriever = _build_zim_retriever(config, logger)
    logger.info("loaded retriever index=%s", config.knowledge.index_path)

    llm = _build_llm_runner(config, logger)
    return MessageRouter(
        OracleService(
            retriever=retriever,
            llm=llm,
            reply_config=config.reply,
            fallback_retriever=fallback_retriever,
        )
    )


def build_radio(
    config: OracleRuntimeConfig,
    *,
    logger: logging.Logger | None = None,
) -> RadioClient:
    logger = logger or LOGGER
    if config.radio.transport == "simulated":
        logger.info("using simulated radio transport")
        return DryRunRadio()

    logger.info(
        "using meshtastic radio transport device=%s channel=%s",
        config.radio.device,
        config.radio.channel,
    )
    return MeshtasticRadioClient(
        config.radio.device,
        channel=config.radio.channel,
    )


def _build_llm_runner(
    config: OracleRuntimeConfig,
    logger: logging.Logger,
) -> LLMRunner | None:
    if config.llm.backend == "deterministic":
        logger.info("using deterministic fallback only")
        return None

    try:
        runner = OpenAICompatibleRunner(
            base_url=config.llm.base_url,
            model=config.llm.model,
            api_key=config.llm.api_key,
            timeout_seconds=config.llm.timeout_seconds,
        )
    except ModelUnavailableError as exc:
        logger.warning("%s unavailable: %s", config.llm.backend, exc)
        return None

    logger.info("loaded llm backend=%s", config.llm.backend)
    return runner


def _build_zim_retriever(
    config: OracleRuntimeConfig,
    logger: logging.Logger,
):
    if not config.knowledge.runtime_zim_fallback_enabled:
        return None

    retriever = RuntimeZimRetriever(
        config.knowledge.zim_dir,
        config.knowledge.runtime_zim_allowlist,
        default_limit=config.knowledge.runtime_zim_search_limit,
    )
    logger.info(
        "loaded runtime zim fallback dir=%s allowlist=%s",
        config.knowledge.zim_dir,
        ",".join(config.knowledge.runtime_zim_allowlist),
    )
    return retriever


def _trim_to_utf8_bytes(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if max_bytes <= 0 or len(encoded) <= max_bytes:
        return text

    ellipsis = "..."
    budget = max(max_bytes - len(ellipsis.encode("utf-8")), 0)
    trimmed = text
    while trimmed and len(trimmed.encode("utf-8")) > budget:
        trimmed = trimmed[:-1]
    trimmed = trimmed.rstrip(" .,;:")
    return f"{trimmed or text[:1]}{ellipsis}"


def main() -> None:
    logging.basicConfig(level=os.environ.get("DELPHI_LOG_LEVEL", "INFO"))
    config_path = Path(os.environ.get("DELPHI_CONFIG", "config/oracle.example.yaml"))

    try:
        bot = build_oracle_bot(config_path)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    bot.run_forever()


if __name__ == "__main__":
    main()
