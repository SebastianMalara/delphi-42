import logging
from pathlib import Path

import pytest

from bot.message_router import MessageRouter
from bot.oracle_bot import OracleBot, POSITION_UNAVAILABLE_TEXT, build_oracle_bot
from bot.radio_interface import (
    DryRunRadio,
    IncomingMessage,
    OutboundMessage,
    PositionUnavailableError,
    RadioTransportError,
)
from core.oracle_service import OracleService
from core.retriever import KeywordRetriever, RetrievalChunk
from core.runtime_config import ReplyConfig


def test_oracle_bot_process_inbox_logs_metadata_only() -> None:
    radio = DryRunRadio(
        inbox=[
            IncomingMessage(
                sender_id="node-1",
                text="?ask how do i purify water",
            )
        ]
    )
    router = MessageRouter(
        OracleService(
            retriever=KeywordRetriever(
                [
                    RetrievalChunk(
                        title="Water Purification",
                        snippet="Boil water for one minute before drinking.",
                        source="field-guide",
                    )
                ]
            )
        )
    )
    bot = OracleBot(radio=radio, router=router, logger=logging.getLogger("test.bot"))

    events = bot.process_inbox()

    assert len(events) == 2
    assert "kind=text" in events[0]
    assert "command=ask" in events[0]
    assert "purify water" not in events[0]
    assert "status=delivery_complete" in events[1]
    assert radio.sent[0].destination == "node-1"


def test_build_oracle_bot_bootstraps_from_config(tmp_path: Path, monkeypatch) -> None:
    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)
    (zim_dir / "medicine.zim").write_bytes(b"zim")

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
node_name: test-node
radio:
  device: /dev/ttyUSB0
  channel: 1
knowledge:
  zim_dir: {zim_dir}
  zim_allowlist:
    - medicine.zim
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "bot.oracle_bot.MeshtasticRadioClient",
        lambda device_path, channel=0: DryRunRadio(),
    )
    monkeypatch.setattr(
        "bot.oracle_bot.KiwixRetriever",
        lambda *args, **kwargs: KeywordRetriever(
            [
                RetrievalChunk(
                    title="Water Purification",
                    snippet="Boil water for one minute before drinking.",
                    source="medical.zim:A/WaterPurification.html",
                )
            ]
        ),
    )

    bot = build_oracle_bot(config_path, logger=logging.getLogger("test.bootstrap"))

    assert isinstance(bot.radio, DryRunRadio)


class PositionUnavailableRadio(DryRunRadio):
    def send_position(self, message: OutboundMessage) -> None:
        raise PositionUnavailableError("Meshtastic local node does not have a position fix")


class FailingReceiveRadio(DryRunRadio):
    def __init__(self) -> None:
        super().__init__()
        self.closed = False

    def receive(self) -> list[IncomingMessage]:
        raise RadioTransportError("receive failed")

    def close(self) -> None:
        self.closed = True


class StopLoop(RuntimeError):
    pass


def _build_test_router() -> MessageRouter:
    return MessageRouter(
        OracleService(
            retriever=KeywordRetriever(
                [
                    RetrievalChunk(
                        title="Water Purification",
                        snippet="Boil water for one minute before drinking.",
                        source="field-guide",
                    )
                ]
            )
        )
    )


def test_oracle_bot_returns_text_fallback_when_position_is_unavailable() -> None:
    radio = PositionUnavailableRadio(
        inbox=[
            IncomingMessage(
                sender_id="node-1",
                text="?where",
            )
        ]
    )
    bot = OracleBot(radio=radio, router=MessageRouter(OracleService()))

    events = bot.process_inbox()

    assert [message.text for message in radio.sent] == [
        "🤖 Sending a private position packet.",
        POSITION_UNAVAILABLE_TEXT,
    ]
    assert all(message.send_position is False for message in radio.sent)
    assert any("kind=text" in event for event in events)


def test_oracle_bot_run_forever_recovers_after_receive_failure() -> None:
    failing_radio = FailingReceiveRadio()
    recovery_radio = DryRunRadio(
        inbox=[IncomingMessage(sender_id="node-1", text="?ask how do i purify water")]
    )
    sleeps: list[float] = []

    def sleep_fn(seconds: float) -> None:
        sleeps.append(seconds)
        if seconds == 0.5:
            raise StopLoop("done")

    bot = OracleBot(
        radio=failing_radio,
        router=_build_test_router(),
        radio_factory=lambda: recovery_radio,
        sleep_fn=sleep_fn,
        logger=logging.getLogger("test.receive-recovery"),
    )

    with pytest.raises(StopLoop, match="done"):
        bot.run_forever(poll_interval_seconds=0.5)

    assert failing_radio.closed is True
    assert recovery_radio.sent[0].destination == "node-1"
    assert sleeps[:2] == [1.0, 0.5]


def test_oracle_bot_trims_text_packets_to_byte_budget() -> None:
    radio = DryRunRadio(
        inbox=[IncomingMessage(sender_id="node-1", text="?ask how do i purify water")]
    )
    router = MessageRouter(
        OracleService(
            retriever=KeywordRetriever(
                [
                    RetrievalChunk(
                        title="Water Purification",
                        snippet="Boil water for one minute before drinking.",
                        source="field-guide",
                    )
                ]
            ),
            reply_config=ReplyConfig(
                short_max_chars=100,
                condensed_max_chars=120,
                max_total_packets=2,
            ),
        )
    )
    bot = OracleBot(
        radio=radio,
        router=router,
        max_text_payload_bytes=20,
    )

    bot.process_inbox()

    assert len(radio.sent[0].text.encode("utf-8")) <= 20
    assert radio.sent[0].text.endswith("...")
