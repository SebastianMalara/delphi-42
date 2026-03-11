from bot.command_parser import ParsedCommand
from core.oracle_service import OracleService
from core.retriever import KeywordRetriever, RetrievalChunk


def test_where_shares_private_position() -> None:
    reply = OracleService().handle(ParsedCommand(name="where"))
    assert reply.share_position is True
    assert "position" in reply.text.lower()


def test_ask_returns_grounded_response() -> None:
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
