from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.oracle_service import OracleService

from .message_router import MessageRouter
from .radio_interface import DryRunRadio, IncomingMessage


@dataclass(frozen=True)
class OracleBotConfig:
    node_name: str = "delphi-42"
    response_word_limit: int = 40
    broadcast_interval_minutes: int = 90
    broadcast_messages: tuple[str, ...] = (
        "THE ORACLE LISTENS. SEND DM FOR COUNSEL.",
        "ASH NODE AWAKE.",
        "SEEK WISDOM IN PRIVATE.",
    )


def load_config(path: Path) -> OracleBotConfig:
    if not path.exists():
        return OracleBotConfig()

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    broadcasts = data.get("broadcasts", {})
    return OracleBotConfig(
        node_name=data.get("node_name", "delphi-42"),
        response_word_limit=data.get("llm", {}).get("max_words", 40),
        broadcast_interval_minutes=broadcasts.get("interval_minutes", 90),
        broadcast_messages=tuple(
            broadcasts.get(
                "messages",
                [
                    "THE ORACLE LISTENS. SEND DM FOR COUNSEL.",
                    "ASH NODE AWAKE.",
                    "SEEK WISDOM IN PRIVATE.",
                ],
            )
        ),
    )


class OracleBot:
    """Starter bot loop for local development."""

    def __init__(self, radio: DryRunRadio, router: MessageRouter) -> None:
        self.radio = radio
        self.router = router

    def process_inbox(self) -> list[str]:
        delivery_log: list[str] = []
        for message in self.radio.receive():
            for response in self.router.route(message):
                self.radio.send(response)
                delivery_log.append(
                    f"to={response.destination} channel={response.channel} text={response.text}"
                )
        return delivery_log


def main() -> None:
    config_path = Path(os.environ.get("DELPHI_CONFIG", "config/oracle.example.yaml"))
    config = load_config(config_path)

    radio = DryRunRadio(
        inbox=[
            IncomingMessage(
                sender_id="demo-node",
                text="ask how to purify water",
            )
        ]
    )
    router = MessageRouter(OracleService(max_words=config.response_word_limit))
    bot = OracleBot(radio=radio, router=router)

    print(f"Loaded config for {config.node_name} from {config_path}")
    for event in bot.process_inbox():
        print(event)


if __name__ == "__main__":
    main()
