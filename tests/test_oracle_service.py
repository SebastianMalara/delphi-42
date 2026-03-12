from bot.command_parser import ParsedCommand
from core.llm_runner import ModelUnavailableError
from core.oracle_service import OracleService, ReplyMode
from core.retriever import KeywordRetriever, RetrievalChunk


class UnavailableRunner:
    def generate(self, prompt: str, max_words: int = 40) -> str:
        raise ModelUnavailableError("backend offline")


class VerboseRunner:
    def generate(self, prompt: str, max_words: int = 40) -> str:
        return "one two three four five six"


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


def test_model_output_is_truncated_to_word_budget() -> None:
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
        llm=VerboseRunner(),
        max_words=4,
    ).handle(ParsedCommand(name="ask", argument="how do i signal"))
    assert reply.mode is ReplyMode.MODEL
    assert reply.text.split() == ["one", "two", "three", "four..."]
