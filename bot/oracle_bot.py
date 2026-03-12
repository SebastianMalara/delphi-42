from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from core.llm_runner import LlamaCppRunner, ModelUnavailableError
from core.oracle_service import OracleService
from core.retriever import SQLiteRetriever
from core.runtime_config import ConfigError, OracleRuntimeConfig, load_runtime_config

from .message_router import MessageRouter, RoutedReply
from .radio_interface import MeshtasticRadioClient, OutboundMessage, RadioClient


LOGGER = logging.getLogger("delphi42.bot")


class OracleBot:
    """Long-running bot loop for the Delphi-42 runtime."""

    def __init__(
        self,
        radio: RadioClient,
        router: MessageRouter,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self.radio = radio
        self.router = router
        self.logger = logger or LOGGER

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
                self.process_inbox()
                time.sleep(poll_interval_seconds)
        finally:
            self.radio.close()

    def _deliver(self, routed: RoutedReply) -> list[str]:
        events: list[str] = []
        for response in routed.messages:
            if response.send_position:
                self.radio.send_position(response)
                delivery_kind = "position"
            else:
                self.radio.send_text(response)
                delivery_kind = "text"

            event = (
                f"to={response.destination} channel={response.channel} "
                f"kind={delivery_kind} mode={routed.reply.mode.value} "
                f"hits={routed.reply.retrieval_hits}"
            )
            self.logger.info(event)
            events.append(event)
        return events


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

    retriever = SQLiteRetriever(config.knowledge.index_path)
    logger.info("loaded config %s", config.summary())
    logger.info("loaded retriever index=%s", config.knowledge.index_path)

    llm = _build_llm_runner(config, logger)
    router = MessageRouter(
        OracleService(
            retriever=retriever,
            llm=llm,
            max_words=config.llm.max_words,
        )
    )
    radio = MeshtasticRadioClient(
        config.radio.device,
        channel=config.radio.channel,
    )
    return OracleBot(radio=radio, router=router, logger=logger)


def _build_llm_runner(
    config: OracleRuntimeConfig,
    logger: logging.Logger,
) -> LlamaCppRunner | None:
    if config.llm.backend == "deterministic":
        logger.info("using deterministic fallback only")
        return None

    try:
        runner = LlamaCppRunner(config.llm.model_path)
    except ModelUnavailableError as exc:
        logger.warning("llama.cpp unavailable: %s", exc)
        return None

    logger.info("loaded llm backend=%s", config.llm.backend)
    return runner


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
