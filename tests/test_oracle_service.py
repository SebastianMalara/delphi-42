from bot.command_parser import ParsedCommand
from core.llm_runner import AnswerDraft, ModelUnavailableError
from core.oracle_service import OracleService, ReplyMode
from core.retriever import KeywordRetriever, RetrievalChunk
from core.runtime_config import ReplyConfig


class UnavailableRunner:
    def generate(self, prompt: str) -> AnswerDraft:
        raise ModelUnavailableError("backend offline")


class StructuredRunner:
    def generate(self, prompt: str) -> AnswerDraft:
        return AnswerDraft(
            short_answer="Use reflective material.",
            extended_answer=(
                "Use reflective material to improve daytime visibility. "
                "Keep it in direct sun. Sweep it slowly to catch attention."
            ),
        )


def test_where_shares_private_position() -> None:
    reply = OracleService().handle(ParsedCommand(name="where"))
    assert reply.share_position is True
    assert reply.mode is ReplyMode.POSITION
    assert "position" in reply.text.lower()


def test_ask_returns_deterministic_grounded_response() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Water Purification",
                snippet="Boil water for one minute before drinking.",
                source="field-guide",
            )
        ]
    )
    reply = OracleService(retriever=retriever).handle(
        ParsedCommand(name="ask", argument="how do I purify water")
    )
    assert "Boil water" in reply.text
    assert reply.mode is ReplyMode.DETERMINISTIC_FALLBACK
    assert reply.retrieval_hits == 1


def test_ask_returns_no_grounded_answer_when_retrieval_is_empty() -> None:
    reply = OracleService().handle(ParsedCommand(name="ask", argument="unknown question"))
    assert reply.mode is ReplyMode.NO_GROUNDED_ANSWER
    assert "grounded answer" in reply.text


def test_ask_falls_back_when_model_is_unavailable() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Shelter",
                snippet="Use dry insulation layers to reduce heat loss overnight.",
                source="survival-guide",
            )
        ]
    )
    reply = OracleService(retriever=retriever, llm=UnavailableRunner()).handle(
        ParsedCommand(name="ask", argument="dry insulation for warmth")
    )
    assert reply.mode is ReplyMode.DETERMINISTIC_FALLBACK
    assert "dry insulation layers" in reply.text
    assert len(reply.packets) == 1


def test_ask_uses_zim_fallback_retriever_when_sqlite_misses() -> None:
    fallback_retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Water Purification",
                snippet="Boil water for one minute before drinking.",
                source="medical.zim:A/Water.html",
            )
        ]
    )
    reply = OracleService(
        retriever=KeywordRetriever([]),
        fallback_retriever=fallback_retriever,
    ).handle(ParsedCommand(name="ask", argument="how do i purify water"))

    assert reply.mode is ReplyMode.DETERMINISTIC_FALLBACK
    assert "Boil water" in reply.text
    assert reply.retrieval_hits == 1


def test_model_output_is_formatted_into_bounded_packets() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Signal",
                snippet="Use reflective material to improve daytime visibility.",
                source="field-guide",
            )
        ]
    )
    reply = OracleService(
        retriever=retriever,
        llm=StructuredRunner(),
        reply_config=ReplyConfig(
            short_max_chars=24,
            continuation_max_chars=50,
            max_continuation_packets=2,
        ),
    ).handle(ParsedCommand(name="ask", argument="how do i signal"))
    assert reply.mode is ReplyMode.MODEL
    assert len(reply.packets) == 3
    assert len(reply.packets[0]) <= 24
    assert all(len(packet) <= 50 for packet in reply.packets[1:])
