from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import sqlite3
from typing import Protocol, Sequence


@dataclass(frozen=True)
class RetrievalChunk:
    title: str
    snippet: str
    source: str
    matched_terms: int = 0


class Retriever(Protocol):
    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        ...


class NullRetriever:
    """Fallback retriever used until a real index is attached."""

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        return []


class KeywordRetriever:
    """Small deterministic retriever for development and tests."""

    def __init__(self, corpus: Sequence[RetrievalChunk]) -> None:
        self.corpus = list(corpus)

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        query_terms = normalized_query_terms(question)
        threshold = minimum_grounding_threshold(query_terms)
        if not query_terms:
            return []

        scored: list[tuple[int, int, RetrievalChunk]] = []
        for index, chunk in enumerate(self.corpus):
            score = score_query_terms(query_terms, chunk.title, chunk.snippet)
            if score < threshold:
                continue
            scored.append(
                (
                    score,
                    index,
                    RetrievalChunk(
                        title=chunk.title,
                        snippet=chunk.snippet,
                        source=chunk.source,
                        matched_terms=score,
                    ),
                )
            )

        scored.sort(key=lambda item: (-item[0], item[1]))
        requested_limit = limit or 3
        return [chunk for _, _, chunk in scored[:requested_limit]]


class SQLiteRetriever:
    """SQLite FTS retriever used by the production runtime."""

    def __init__(self, db_path: Path, default_limit: int = 3) -> None:
        self.db_path = db_path
        self.default_limit = default_limit
        self._validate_index()

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        query_terms = normalized_query_terms(question)
        query = _question_to_fts_query(question)
        if not query:
            return []

        requested_limit = limit or self.default_limit
        candidate_limit = max(requested_limit * 8, 12)
        threshold = minimum_grounding_threshold(query_terms)
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT title, source_id, text, bm25(chunks) AS rank
                FROM chunks
                WHERE chunks MATCH ?
                ORDER BY rank
                LIMIT ?
                """,
                (query, candidate_limit),
            ).fetchall()

        ranked_chunks: list[tuple[int, float, int, RetrievalChunk]] = []
        for index, (title, source_id, text, rank) in enumerate(rows):
            matched_terms = score_query_terms(query_terms, title, text)
            if matched_terms < threshold:
                continue
            ranked_chunks.append(
                (
                    matched_terms,
                    float(rank),
                    index,
                    RetrievalChunk(
                        title=title,
                        snippet=text,
                        source=source_id,
                        matched_terms=matched_terms,
                    ),
                )
            )

        ranked_chunks.sort(key=lambda item: (-item[0], item[1], item[2]))
        return [chunk for _, _, _, chunk in ranked_chunks[:requested_limit]]

    def _validate_index(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite index not found: {self.db_path}")

        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'"
            ).fetchone()
        if row is None:
            raise ValueError(f"SQLite index is missing required 'chunks' table: {self.db_path}")


def _question_to_fts_query(question: str) -> str:
    tokens = raw_query_terms(question)
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in tokens)


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]{2,}")
QUESTION_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "be",
    "by",
    "do",
    "for",
    "how",
    "i",
    "in",
    "is",
    "me",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "where",
    "who",
    "why",
}


def raw_query_terms(text: str) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                token
                for token in _raw_tokens(text)
                if token not in QUESTION_STOPWORDS
            }
        )
    )


def normalized_query_terms(text: str) -> tuple[str, ...]:
    return tuple(sorted({_normalize_token(token) for token in raw_query_terms(text)}))


def minimum_grounding_threshold(query_terms: Sequence[str]) -> int:
    if not query_terms:
        return 0
    if len(query_terms) == 1:
        return 1
    if len(query_terms) == 2:
        return 2
    return 2


def score_query_terms(query_terms: Sequence[str], *text_parts: str) -> int:
    if not query_terms:
        return 0
    haystack_tokens = normalized_text_tokens(" ".join(text_parts))
    return sum(1 for token in query_terms if token in haystack_tokens)


def normalized_text_tokens(text: str) -> set[str]:
    return {_normalize_token(token) for token in _raw_tokens(text)}


def grounded_retrieval_chunks(
    question: str,
    chunks: Sequence[RetrievalChunk],
) -> list[RetrievalChunk]:
    query_terms = normalized_query_terms(question)
    threshold = minimum_grounding_threshold(query_terms)
    grounded: list[tuple[int, int, RetrievalChunk]] = []
    for index, chunk in enumerate(chunks):
        score = score_query_terms(query_terms, chunk.title, chunk.snippet)
        if score < threshold:
            continue
        grounded.append(
            (
                score,
                index,
                RetrievalChunk(
                    title=chunk.title,
                    snippet=chunk.snippet,
                    source=chunk.source,
                    matched_terms=score,
                ),
            )
        )
    grounded.sort(key=lambda item: (-item[0], item[1]))
    return [chunk for _, _, chunk in grounded]


def _raw_tokens(text: str) -> set[str]:
    return {token.lower() for token in TOKEN_PATTERN.findall(text)}


def _normalize_token(token: str) -> str:
    normalized = token.lower()
    replacements = (
        ("ification", "ify"),
        ("ization", "ize"),
        ("isation", "ise"),
        ("ation", "ate"),
    )
    for suffix, replacement in replacements:
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 1:
            normalized = normalized[: -len(suffix)] + replacement
            break

    for suffix in ("ing", "ed", "es", "s"):
        if normalized.endswith(suffix) and len(normalized) > len(suffix) + 2:
            normalized = normalized[: -len(suffix)]
            break

    return normalized
