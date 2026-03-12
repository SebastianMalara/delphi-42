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
        tokens = _tokenize(question)
        scored: list[tuple[int, RetrievalChunk]] = []

        for chunk in self.corpus:
            haystack = f"{chunk.title} {chunk.snippet}".lower()
            score = sum(1 for token in tokens if token in haystack)
            if score:
                scored.append(
                    (
                        score,
                        RetrievalChunk(
                            title=chunk.title,
                            snippet=chunk.snippet,
                            source=chunk.source,
                            matched_terms=score,
                        ),
                    )
                )

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:limit]]


class SQLiteRetriever:
    """SQLite FTS retriever used by the production runtime."""

    def __init__(self, db_path: Path, default_limit: int = 3) -> None:
        self.db_path = db_path
        self.default_limit = default_limit
        self._validate_index()

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        query = _question_to_fts_query(question)
        if not query:
            return []

        normalized_tokens = _tokenize(question)
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT title, source_id, text
                FROM chunks
                WHERE chunks MATCH ?
                ORDER BY bm25(chunks)
                LIMIT ?
                """,
                (query, limit or self.default_limit),
            ).fetchall()

        chunks: list[RetrievalChunk] = []
        for title, source_id, text in rows:
            matched_terms = sum(
                1 for token in normalized_tokens if token in f"{title} {text}".lower()
            )
            chunks.append(
                RetrievalChunk(
                    title=title,
                    snippet=text,
                    source=source_id,
                    matched_terms=matched_terms,
                )
            )
        return chunks

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
    tokens = sorted(_tokenize(question))
    if not tokens:
        return ""
    return " OR ".join(f'"{token}"' for token in tokens)


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_]{2,}", text)}
