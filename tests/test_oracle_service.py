from __future__ import annotations

from bot.command_parser import ParsedCommand
from bot.radio_interface import IncomingMessage, MeshPacketMetrics
from core.llm_runner import CHAT_UNAVAILABLE
from core.oracle_service import OracleService, ReplyMode
from core.retriever import KeywordRetriever, RetrievalChunk, Retriever
from core.runtime_config import ReplyConfig


class SequenceRunner:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, system_prompt: str | None = None, temperature: float = 0.0) -> str:
        self.prompts.append(prompt)
        if not self.responses:
            raise AssertionError("Unexpected completion call")
        return self.responses.pop(0)


class StaticRetriever:
    def __init__(self, chunks: list[RetrievalChunk]) -> None:
        self.chunks = chunks

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        return self.chunks[:limit]


def test_ask_returns_no_grounded_answer_when_retrieval_is_empty() -> None:
    reply = OracleService().handle(ParsedCommand(name="ask", argument="unknown question"))
    assert reply.mode is ReplyMode.ASK_NO_GROUNDED_ANSWER
    assert "grounded answer" in reply.text


def test_ask_uses_multi_pass_condensation_chain() -> None:
    retriever: Retriever = StaticRetriever(
        [
            RetrievalChunk(
                title="Water Purification",
                snippet=(
                    "Boil water for one minute before drinking. "
                    "Let it cool in a clean container. "
                    "Keep treated water covered."
                ),
                source="medical.zim:A/WaterPurification.html",
                matched_terms=2,
            )
        ]
    )
    runner = SequenceRunner(
        [
            (
                "Boil water for one minute before drinking. "
                "Let it cool in a clean container. "
                "Keep treated water covered."
            ),
            (
                "Boil water for one minute before drinking. "
                "Let it cool in a clean container and keep it covered."
            ),
            "Boil water first.",
        ]
    )
    reply = OracleService(
        retriever=retriever,
        llm=runner,
        reply_config=ReplyConfig(
            short_max_chars=24,
            condensed_max_chars=80,
            max_total_packets=3,
        ),
        packet_byte_limit=60,
    ).handle(ParsedCommand(name="ask", argument="how do i purify water"))

    assert reply.mode is ReplyMode.ASK_MODEL
    assert reply.packets[0] == "🤖 Boil water first."
    assert len(reply.packets) >= 2
    assert reply.packets[1] != reply.packets[0]


def test_ask_falls_back_to_deterministic_bundle_without_model() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Shelter",
                snippet="Use dry insulation layers to reduce heat loss overnight.",
                source="field-guide",
            )
        ]
    )
    reply = OracleService(retriever=retriever).handle(
        ParsedCommand(name="ask", argument="dry insulation for warmth")
    )
    assert reply.mode is ReplyMode.ASK_DETERMINISTIC_FALLBACK
    assert "🤖" in reply.text


def test_ask_shrinks_short_answer_before_trimming() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Signal",
                snippet="Use reflective material to improve daytime visibility.",
                source="field-guide",
            )
        ]
    )
    runner = SequenceRunner(
        [
            "Use reflective material to improve daytime visibility.",
            "Use reflective material to improve daytime visibility.",
            "Use reflective material to improve daytime visibility.",
            "Use reflectors.",
        ]
    )
    reply = OracleService(
        retriever=retriever,
        llm=runner,
        reply_config=ReplyConfig(
            short_max_chars=14,
            condensed_max_chars=80,
            max_total_packets=2,
        ),
        packet_byte_limit=22,
    ).handle(ParsedCommand(name="ask", argument="how do i signal"))

    assert reply.shrink_attempts >= 1
    assert len(reply.packets[0].encode("utf-8")) <= 22


def test_chat_uses_sender_memory() -> None:
    runner = SequenceRunner(
        [
            "I'm here with you.",
            "I'm here with you.",
            "I'm here.",
            "Tell me what happened after the rain.",
            "Tell me what happened after the rain.",
            "Tell me more.",
        ]
    )
    service = OracleService(
        llm=runner,
        reply_config=ReplyConfig(
            short_max_chars=24,
            condensed_max_chars=80,
            max_total_packets=2,
        ),
    )

    first = service.handle(
        ParsedCommand(name="chat", argument="stay with me"),
        sender_id="node-1",
    )
    second = service.handle(
        ParsedCommand(name="chat", argument="what should I do now"),
        sender_id="node-1",
    )

    assert first.mode is ReplyMode.CHAT_MODEL
    assert second.mode is ReplyMode.CHAT_MODEL
    assert "USER: stay with me" in runner.prompts[1]
    assert "ASSISTANT: I'm here with you." in runner.prompts[1]


def test_chat_returns_unavailable_without_model() -> None:
    reply = OracleService().handle(
        ParsedCommand(name="chat", argument="keep me company"),
        sender_id="node-1",
    )

    assert reply.mode is ReplyMode.CHAT_UNAVAILABLE
    assert CHAT_UNAVAILABLE in reply.text


def test_mesh_returns_deterministic_packet_stats_without_model() -> None:
    reply = OracleService().handle(
        ParsedCommand(name="mesh"),
        sender_id="node-1",
        incoming_message=IncomingMessage(
            sender_id="!mesh",
            text="?mesh",
            channel=2,
            is_direct_message=True,
            packet_id="77",
            mesh=MeshPacketMetrics(
                rx_rssi=-92,
                rx_snr=5.5,
                hop_start=4,
                hop_limit=1,
                rx_time=123456,
                to_id="!local",
            ),
        ),
    )

    assert reply.mode is ReplyMode.MESH
    assert "RSSI -92 dBm" in reply.text
    assert "SNR 5.5 dB" in reply.text
    assert "hops_used 3" in reply.text
