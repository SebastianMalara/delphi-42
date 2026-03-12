import logging
from pathlib import Path

from bot.message_router import MessageRouter
from bot.oracle_bot import OracleBot, build_oracle_bot
from bot.radio_interface import DryRunRadio, IncomingMessage
from core.oracle_service import OracleService
from core.retriever import KeywordRetriever, RetrievalChunk
from ingest.build_index import SQLiteIndexBuilder, build_chunks
from ingest.zim_extract import ExtractedDocument


def test_oracle_bot_process_inbox_logs_metadata_only() -> None:
    radio = DryRunRadio(
        inbox=[
            IncomingMessage(
                sender_id="node-1",
                text="how do i purify water",
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

    assert len(events) == 1
    assert "kind=text" in events[0]
    assert "mode=deterministic_fallback" in events[0]
    assert "purify water" not in events[0]
    assert radio.sent[0].destination == "node-1"


def test_build_oracle_bot_bootstraps_from_config(
    tmp_path: Path,
    monkeypatch,
) -> None:
    documents = [
        ExtractedDocument(
            title="Water Purification",
            source_id="water.txt",
            text="Boil water for one minute before drinking.",
        )
    ]
    index_path = tmp_path / "data/index/oracle.db"
    SQLiteIndexBuilder(index_path).build(build_chunks(documents))

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
node_name: test-node
radio:
  device: /dev/ttyUSB0
  channel: 1
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "bot.oracle_bot.MeshtasticRadioClient",
        lambda device_path, channel=0: DryRunRadio(),
    )

    bot = build_oracle_bot(config_path, logger=logging.getLogger("test.bootstrap"))

    assert isinstance(bot.radio, DryRunRadio)


def test_build_oracle_bot_uses_simulated_transport_from_config(tmp_path: Path) -> None:
    documents = [
        ExtractedDocument(
            title="Water Purification",
            source_id="water.txt",
            text="Boil water for one minute before drinking.",
        )
    ]
    index_path = tmp_path / "data/index/oracle.db"
    SQLiteIndexBuilder(index_path).build(build_chunks(documents))

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
node_name: test-node
radio:
  transport: simulated
  device: ""
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
llm:
  backend: deterministic
""".strip(),
        encoding="utf-8",
    )

    bot = build_oracle_bot(config_path, logger=logging.getLogger("test.simulated"))

    assert isinstance(bot.radio, DryRunRadio)


def test_build_oracle_bot_wires_runtime_zim_fallback_when_enabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    documents = [
        ExtractedDocument(
            title="Water Purification",
            source_id="water.txt",
            text="Boil water for one minute before drinking.",
        )
    ]
    index_path = tmp_path / "data/index/oracle.db"
    SQLiteIndexBuilder(index_path).build(build_chunks(documents))

    zim_dir = tmp_path / "data/library/zim"
    zim_dir.mkdir(parents=True)
    (zim_dir / "medical.zim").write_bytes(b"zim")

    config_path = tmp_path / "oracle.yaml"
    config_path.write_text(
        f"""
node_name: test-node
radio:
  device: /dev/ttyUSB0
knowledge:
  plaintext_dir: data/library/plaintext
  index_path: {index_path}
  zim_dir: {zim_dir}
  runtime_zim_fallback_enabled: true
  runtime_zim_allowlist:
    - medical.zim
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
        "bot.oracle_bot.RuntimeZimRetriever",
        lambda zim_dir, allowlist, default_limit=3: KeywordRetriever(
            [
                RetrievalChunk(
                    title="Fallback",
                    snippet="Fallback knowledge from ZIM.",
                    source=f"{allowlist[0]}:A/Fallback.html",
                )
            ]
        ),
    )

    bot = build_oracle_bot(config_path, logger=logging.getLogger("test.zim-bootstrap"))

    assert isinstance(bot.radio, DryRunRadio)
