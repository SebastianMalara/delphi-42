from bot.command_parser import ParsedCommand
from core.llm_runner import AnswerDraft, ModelExecutionError, ModelUnavailableError
from core.oracle_service import OracleService, ReplyMode
from core.retriever import KeywordRetriever, RetrievalChunk, Retriever
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


class CollapsedStructuredRunner:
    def generate(self, prompt: str) -> AnswerDraft:
        return AnswerDraft(
            short_answer="Use portable water purification devices.",
            extended_answer="Use portable water purification devices.",
        )


class CollapsedStructuredThenLongRunner:
    def generate(self, prompt: str) -> AnswerDraft:
        return AnswerDraft(
            short_answer="Use portable water purification devices.",
            extended_answer="Use portable water purification devices.",
        )

    def generate_long_answer(self, prompt: str) -> str:
        return (
            "Use portable water purification devices. "
            "Filter cloudy water first if the device requires clear input. "
            "Then follow the treatment steps exactly and store the water in a clean container."
        )


class StaticRetriever:
    def __init__(self, chunks: list[RetrievalChunk]) -> None:
        self.chunks = chunks

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        return self.chunks[:limit]


class UnstructuredThenLongRunner:
    def generate(self, prompt: str) -> AnswerDraft:
        raise ModelExecutionError("OpenAI-compatible API did not return the required SHORT/LONG format")

    def generate_long_answer(self, prompt: str) -> str:
        return (
            "Clean the wound. "
            "Apply steady pressure if it is bleeding. "
            "Cover it with a sterile dressing and watch for infection."
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
    assert reply.retrieval_source == "zim"


def test_ask_rejects_weak_sqlite_hit_and_uses_stronger_zim_context() -> None:
    primary_retriever: Retriever = StaticRetriever(
        [
            RetrievalChunk(
                title="Water Storage",
                snippet="Store water safely after treatment.",
                source="water-storage.txt",
                matched_terms=1,
            )
        ]
    )
    fallback_retriever: Retriever = StaticRetriever(
        [
            RetrievalChunk(
                title="Water Purification",
                snippet="Boil water for one minute before drinking.",
                source="medical.zim:A/WaterPurification.html",
                matched_terms=2,
            )
        ]
    )

    reply = OracleService(
        retriever=primary_retriever,
        fallback_retriever=fallback_retriever,
    ).handle(ParsedCommand(name="ask", argument="how do i purify water"))

    assert reply.mode is ReplyMode.DETERMINISTIC_FALLBACK
    assert "Boil water" in reply.text
    assert reply.retrieval_source in {"zim", "sqlite+zim"}
    assert reply.retrieval_sources[0] == "medical.zim:A/WaterPurification.html"


def test_ask_returns_no_grounded_answer_for_weak_retrieval() -> None:
    retriever: Retriever = StaticRetriever(
        [
            RetrievalChunk(
                title="Transit Notes",
                snippet="To travel at dawn, move light and stay aware.",
                source="notes.txt",
                matched_terms=1,
            )
        ]
    )

    reply = OracleService(retriever=retriever).handle(
        ParsedCommand(name="ask", argument="how to clean a wound")
    )

    assert reply.mode is ReplyMode.NO_GROUNDED_ANSWER
    assert reply.retrieval_hits == 0


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


def test_model_long_answer_fallback_recovers_from_unstructured_output() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Wound Care",
                snippet="Clean the wound with safe water and cover it with a sterile dressing.",
                source="medical.zim:A/WoundCare.html",
            )
        ]
    )
    reply = OracleService(
        retriever=retriever,
        llm=UnstructuredThenLongRunner(),
        reply_config=ReplyConfig(
            short_max_chars=24,
            continuation_max_chars=50,
            max_continuation_packets=3,
        ),
    ).handle(ParsedCommand(name="ask", argument="how to clean a wound"))

    assert reply.mode is ReplyMode.MODEL_LONG_FALLBACK
    assert len(reply.packets) >= 2
    assert reply.packets[0] == "Clean the wound."
    assert any("sterile dressing" in packet for packet in reply.packets[1:])


def test_collapsed_structured_answer_uses_long_answer_recovery() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Water Purification",
                snippet=(
                    "Use portable water purification devices when boiling is not practical. "
                    "Filter cloudy water first if the device requires clear input. "
                    "Then follow the treatment steps exactly and store the water in a clean container."
                ),
                source="medical.zim:A/WaterPurification.html",
            )
        ]
    )
    reply = OracleService(
        retriever=retriever,
        llm=CollapsedStructuredThenLongRunner(),
        reply_config=ReplyConfig(
            short_max_chars=40,
            continuation_max_chars=70,
            max_continuation_packets=3,
        ),
    ).handle(ParsedCommand(name="ask", argument="how to purify water"))

    assert reply.mode is ReplyMode.MODEL_LONG_FALLBACK
    assert len(reply.packets) >= 2
    assert reply.packets[0] == "Use portable water purification devices."
    assert any("Filter cloudy water first" in packet for packet in reply.packets[1:])


def test_collapsed_structured_answer_uses_deterministic_context_recovery() -> None:
    retriever = KeywordRetriever(
        [
            RetrievalChunk(
                title="Water Purification",
                snippet=(
                    "Use portable water purification devices when boiling is not practical. "
                    "Filter cloudy water first if the device requires clear input. "
                    "Then follow the treatment steps exactly and store the water in a clean container."
                ),
                source="medical.zim:A/WaterPurification.html",
            )
        ]
    )
    reply = OracleService(
        retriever=retriever,
        llm=CollapsedStructuredRunner(),
        reply_config=ReplyConfig(
            short_max_chars=40,
            continuation_max_chars=70,
            max_continuation_packets=3,
        ),
    ).handle(ParsedCommand(name="ask", argument="how to purify water"))

    assert reply.mode is ReplyMode.DETERMINISTIC_FALLBACK
    assert len(reply.packets) >= 2
    assert reply.packets[0] == "Use portable water purification..."
    assert any("Filter cloudy water first" in packet for packet in reply.packets[1:])
