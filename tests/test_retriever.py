from pathlib import Path

import pytest

from core.retriever import RetrievalChunk, RetrievalConfidence, SQLiteRetriever, assess_retrieval
from ingest.build_index import SQLiteIndexBuilder, build_chunks
from ingest.zim_extract import ExtractedDocument


def test_sqlite_retriever_reads_generated_index(tmp_path: Path) -> None:
    documents = [
        ExtractedDocument(
            title="Water Purification",
            source_id="water.txt",
            text="Boil water for one minute before drinking.\n\nStore clean water safely.",
        )
    ]
    chunks = build_chunks(documents)
    db_path = tmp_path / "oracle.db"
    SQLiteIndexBuilder(db_path).build(chunks)

    results = SQLiteRetriever(db_path).search("how do i purify water")

    assert len(results) == 1
    assert results[0].title == "Water Purification"
    assert results[0].source == "water.txt"
    assert "Boil water" in results[0].snippet
    assert results[0].matched_terms >= 1


def test_sqlite_retriever_requires_existing_index(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        SQLiteRetriever(tmp_path / "missing.db")


def test_sqlite_retriever_ignores_stopword_only_candidates(tmp_path: Path) -> None:
    documents = [
        ExtractedDocument(
            title="Water Purification",
            source_id="water.txt",
            text="Boil water for one minute before drinking.",
        ),
        ExtractedDocument(
            title="Transit Notes",
            source_id="notes.txt",
            text="To travel at dawn, move light and stay aware.",
        ),
    ]
    db_path = tmp_path / "oracle.db"
    SQLiteIndexBuilder(db_path).build(build_chunks(documents))

    results = SQLiteRetriever(db_path).search("how to purify water")

    assert len(results) == 1
    assert results[0].source == "water.txt"


def test_sqlite_retriever_uses_exact_token_overlap_not_substrings(tmp_path: Path) -> None:
    documents = [
        ExtractedDocument(
            title="Alarm Signals",
            source_id="alarm.txt",
            text="An alarm warns nearby teams.",
        ),
        ExtractedDocument(
            title="Broken Arm",
            source_id="arm.txt",
            text="Immobilize the arm with a splint and sling.",
        ),
    ]
    db_path = tmp_path / "oracle.db"
    SQLiteIndexBuilder(db_path).build(build_chunks(documents))

    results = SQLiteRetriever(db_path).search("how to stabilize broken arm")

    assert len(results) == 1
    assert results[0].source == "arm.txt"


def test_assess_retrieval_rejects_ambiguous_wound_query() -> None:
    chunks = [
        RetrievalChunk(
            title="Negative-pressure wound therapy",
            snippet="Negative-pressure wound therapy may support wound closure in supervised settings.",
            source="npwt.txt",
        ),
        RetrievalChunk(
            title="Compartment syndrome",
            snippet="Compartment syndrome requires urgent evaluation and pressure relief.",
            source="compartment.txt",
        ),
    ]

    assessment = assess_retrieval(
        "how to treat a wound it's not closing, I'm alone in the woods",
        chunks,
    )

    assert assessment.confidence is RetrievalConfidence.WEAK
    assert assessment.context == ()
