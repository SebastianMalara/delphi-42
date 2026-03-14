from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
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
    ordinal: int = 0


class RetrievalConfidence(str, Enum):
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"


@dataclass(frozen=True)
class RetrievalAssessment:
    anchor_terms: tuple[str, ...]
    confidence: RetrievalConfidence
    selected_chunk: RetrievalChunk | None
    context: tuple[RetrievalChunk, ...]
    candidates: tuple[RetrievalChunk, ...]
    best_score: int = 0
    runner_up_score: int = 0
    best_title_overlap: int = 0


class Retriever(Protocol):
    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        ...

    def expand_source_context(
        self,
        seed_chunk: RetrievalChunk,
        limit: int = 2,
    ) -> list[RetrievalChunk]:
        ...


class NullRetriever:
    """Fallback retriever used until a real index is attached."""

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        return []

    def expand_source_context(
        self,
        seed_chunk: RetrievalChunk,
        limit: int = 2,
    ) -> list[RetrievalChunk]:
        return [seed_chunk][:limit]


class KeywordRetriever:
    """Small deterministic retriever for development and tests."""

    def __init__(self, corpus: Sequence[RetrievalChunk]) -> None:
        self.corpus = list(corpus)

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        query_terms = normalized_query_terms(question)
        if not query_terms:
            return []

        scored: list[tuple[int, int, RetrievalChunk]] = []
        for index, chunk in enumerate(self.corpus):
            coverage = score_query_terms(query_terms, chunk.title, chunk.snippet)
            if coverage < minimum_grounding_threshold(query_terms):
                continue
            title_overlap = title_match_count(query_terms, chunk.title)
            score = candidate_score(query_terms, chunk.title, chunk.snippet)
            scored.append(
                (
                    score,
                    index,
                    RetrievalChunk(
                        title=chunk.title,
                        snippet=chunk.snippet,
                        source=chunk.source,
                        matched_terms=max(chunk.matched_terms, coverage),
                        ordinal=chunk.ordinal,
                    ),
                )
            )

        scored.sort(key=lambda item: (-item[0], item[1]))
        requested_limit = max(limit or 3, 1)
        return [chunk for _, _, chunk in scored[:requested_limit]]

    def expand_source_context(
        self,
        seed_chunk: RetrievalChunk,
        limit: int = 2,
    ) -> list[RetrievalChunk]:
        return expand_source_context_from_chunks(seed_chunk, self.corpus, limit=limit)


class SQLiteRetriever:
    """SQLite FTS retriever used by the production runtime."""

    def __init__(self, db_path: Path, default_limit: int = 3) -> None:
        self.db_path = db_path
        self.default_limit = default_limit
        self._validate_index()

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        query_terms = normalized_query_terms(question)
        queries = _question_to_fts_queries(question)
        if not queries or not query_terms:
            return []

        requested_limit = max(limit or self.default_limit, 1)
        candidate_limit = max(requested_limit * 6, 18)
        rows = self._fetch_candidate_rows(queries, candidate_limit)

        ranked_chunks: list[tuple[int, int, float, int, RetrievalChunk]] = []
        for index, (title, source_id, ordinal, text, rank) in enumerate(rows):
            coverage = score_query_terms(query_terms, title, text)
            if coverage < minimum_grounding_threshold(query_terms):
                continue
            title_overlap = title_match_count(query_terms, title)
            score = candidate_score(query_terms, title, text)
            ranked_chunks.append(
                (
                    score,
                    title_overlap,
                    float(rank),
                    index,
                    RetrievalChunk(
                        title=title,
                        snippet=text,
                        source=source_id,
                        matched_terms=coverage,
                        ordinal=int(ordinal),
                    ),
                )
            )

        ranked_chunks.sort(key=lambda item: (-item[0], -item[1], item[2], item[3]))
        return [chunk for _, _, _, _, chunk in ranked_chunks[:requested_limit]]

    def expand_source_context(
        self,
        seed_chunk: RetrievalChunk,
        limit: int = 2,
    ) -> list[RetrievalChunk]:
        if limit <= 1:
            return [seed_chunk]

        neighbors: list[RetrievalChunk] = []
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                """
                SELECT title, source_id, ordinal, text
                FROM chunks
                WHERE source_id = ?
                  AND ordinal IN (?, ?)
                ORDER BY ABS(ordinal - ?), ordinal
                LIMIT ?
                """,
                (
                    seed_chunk.source,
                    seed_chunk.ordinal - 1,
                    seed_chunk.ordinal + 1,
                    seed_chunk.ordinal,
                    max(limit - 1, 0),
                ),
            ).fetchall()

        for title, source_id, ordinal, text in rows:
            neighbors.append(
                RetrievalChunk(
                    title=title,
                    snippet=text,
                    source=source_id,
                    matched_terms=seed_chunk.matched_terms,
                    ordinal=int(ordinal),
                )
            )

        return expand_source_context_from_chunks(seed_chunk, neighbors, limit=limit)

    def _fetch_candidate_rows(
        self,
        queries: Sequence[str],
        candidate_limit: int,
    ) -> list[tuple[str, str, int, str, float]]:
        seen: set[tuple[str, int]] = set()
        rows: list[tuple[str, str, int, str, float]] = []
        with sqlite3.connect(self.db_path) as connection:
            for query in queries:
                fetched = connection.execute(
                    """
                    SELECT title, source_id, ordinal, text, bm25(chunks) AS rank
                    FROM chunks
                    WHERE chunks MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (query, candidate_limit),
                ).fetchall()
                for title, source_id, ordinal, text, rank in fetched:
                    key = (str(source_id), int(ordinal))
                    if key in seen:
                        continue
                    seen.add(key)
                    rows.append((title, source_id, int(ordinal), text, float(rank)))
                if len(rows) >= candidate_limit:
                    break
        return rows

    def _validate_index(self) -> None:
        if not self.db_path.exists():
            raise FileNotFoundError(f"SQLite index not found: {self.db_path}")

        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='chunks'"
            ).fetchone()
        if row is None:
            raise ValueError(f"SQLite index is missing required 'chunks' table: {self.db_path}")


def assess_retrieval(
    question: str,
    chunks: Sequence[RetrievalChunk],
    *,
    context_limit: int = 3,
    context_expander=None,
) -> RetrievalAssessment:
    anchor_terms = normalized_query_terms(question)
    if not anchor_terms:
        return RetrievalAssessment(
            anchor_terms=(),
            confidence=RetrievalConfidence.WEAK,
            selected_chunk=None,
            context=(),
            candidates=(),
        )

    scored = _score_candidates(anchor_terms, chunks)
    if not scored:
        return RetrievalAssessment(
            anchor_terms=anchor_terms,
            confidence=RetrievalConfidence.WEAK,
            selected_chunk=None,
            context=(),
            candidates=(),
        )

    by_source: list[_ScoredCandidate] = []
    seen_sources: set[str] = set()
    for candidate in scored:
        if candidate.chunk.source in seen_sources:
            continue
        by_source.append(candidate)
        seen_sources.add(candidate.chunk.source)

    best = by_source[0]
    runner_up_score = by_source[1].score if len(by_source) > 1 else 0
    confidence = classify_retrieval_confidence(
        anchor_terms,
        best.coverage,
        best.title_overlap,
        best.score,
        runner_up_score,
    )
    selected = best.chunk
    if callable(context_expander):
        context = tuple(context_expander(selected, limit=context_limit))
    else:
        context = tuple(expand_source_context_from_chunks(selected, chunks, limit=context_limit))

    return RetrievalAssessment(
        anchor_terms=anchor_terms,
        confidence=confidence,
        selected_chunk=selected,
        context=context,
        candidates=tuple(candidate.chunk for candidate in by_source[:context_limit]),
        best_score=best.score,
        runner_up_score=runner_up_score,
        best_title_overlap=best.title_overlap,
    )


def classify_retrieval_confidence(
    anchor_terms: Sequence[str],
    coverage: int,
    title_overlap: int,
    best_score: int,
    runner_up_score: int,
) -> RetrievalConfidence:
    required_coverage = required_anchor_coverage(anchor_terms)
    if coverage < required_coverage:
        return RetrievalConfidence.WEAK

    strong_title_requirement = 1 if len(anchor_terms) <= 2 else min(required_coverage, 2)
    if (
        title_overlap >= strong_title_requirement
        and (runner_up_score == 0 or best_score - runner_up_score >= 2)
    ):
        return RetrievalConfidence.STRONG

    if title_overlap >= 1 or len(anchor_terms) >= 3:
        return RetrievalConfidence.MEDIUM

    return RetrievalConfidence.WEAK


def required_anchor_coverage(anchor_terms: Sequence[str]) -> int:
    if not anchor_terms:
        return 0
    if len(anchor_terms) == 1:
        return 1
    if len(anchor_terms) <= 3:
        return 2
    return 3


def minimum_grounding_threshold(query_terms: Sequence[str]) -> int:
    return required_anchor_coverage(query_terms)


def candidate_score(query_terms: Sequence[str], title: str, snippet: str) -> int:
    coverage = score_query_terms(query_terms, title, snippet)
    title_overlap = title_match_count(query_terms, title)
    snippet_overlap = snippet_match_count(query_terms, snippet)
    return (coverage * 10) + (title_overlap * 4) + snippet_overlap


def title_match_count(query_terms: Sequence[str], title: str) -> int:
    if not query_terms:
        return 0
    title_tokens = normalized_text_tokens(title)
    return sum(1 for token in query_terms if token in title_tokens)


def snippet_match_count(query_terms: Sequence[str], snippet: str) -> int:
    if not query_terms:
        return 0
    snippet_tokens = normalized_text_tokens(snippet)
    return sum(1 for token in query_terms if token in snippet_tokens)


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
    return list(
        assess_retrieval(
            question,
            chunks,
            context_limit=max(len(chunks), 1),
        ).candidates
    )


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]{2,}")
QUESTION_STOPWORDS = {
    "a",
    "about",
    "am",
    "an",
    "and",
    "are",
    "at",
    "be",
    "been",
    "being",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "get",
    "got",
    "had",
    "has",
    "have",
    "he",
    "help",
    "her",
    "here",
    "hers",
    "him",
    "his",
    "how",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "just",
    "may",
    "maybe",
    "me",
    "might",
    "my",
    "need",
    "of",
    "on",
    "or",
    "our",
    "ours",
    "please",
    "really",
    "say",
    "she",
    "should",
    "tell",
    "than",
    "that",
    "the",
    "their",
    "them",
    "there",
    "these",
    "they",
    "this",
    "those",
    "to",
    "us",
    "want",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "will",
    "with",
    "would",
    "you",
    "your",
    "yours",
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


def expand_source_context_from_chunks(
    seed_chunk: RetrievalChunk,
    chunks: Sequence[RetrievalChunk],
    *,
    limit: int = 2,
) -> list[RetrievalChunk]:
    same_source = sorted(
        (
            RetrievalChunk(
                title=chunk.title,
                snippet=chunk.snippet,
                source=chunk.source,
                matched_terms=max(chunk.matched_terms, seed_chunk.matched_terms),
                ordinal=chunk.ordinal,
            )
            for chunk in chunks
            if chunk.source == seed_chunk.source
        ),
        key=lambda chunk: (abs(chunk.ordinal - seed_chunk.ordinal), chunk.ordinal),
    )
    ordered: list[RetrievalChunk] = [seed_chunk]
    seen = {(seed_chunk.source, seed_chunk.ordinal)}
    for chunk in same_source:
        key = (chunk.source, chunk.ordinal)
        if key in seen:
            continue
        ordered.append(chunk)
        seen.add(key)
        if len(ordered) >= limit:
            break
    ordered.sort(key=lambda chunk: chunk.ordinal)
    return ordered[:limit]


def _question_to_fts_queries(question: str) -> tuple[str, ...]:
    tokens = raw_query_terms(question)
    if not tokens:
        return ()

    quoted = [f'"{token}"' for token in tokens]
    if len(quoted) == 1:
        return (quoted[0],)
    return (" AND ".join(quoted), " OR ".join(quoted))


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


@dataclass(frozen=True)
class _ScoredCandidate:
    score: int
    coverage: int
    title_overlap: int
    chunk: RetrievalChunk


def _score_candidates(
    anchor_terms: Sequence[str],
    chunks: Sequence[RetrievalChunk],
) -> list[_ScoredCandidate]:
    required = minimum_grounding_threshold(anchor_terms)
    ranked: list[_ScoredCandidate] = []
    for chunk in chunks:
        coverage = score_query_terms(anchor_terms, chunk.title, chunk.snippet)
        if coverage < required:
            continue
        title_overlap = title_match_count(anchor_terms, chunk.title)
        score = candidate_score(anchor_terms, chunk.title, chunk.snippet)
        ranked.append(
            _ScoredCandidate(
                score=score,
                coverage=coverage,
                title_overlap=title_overlap,
                chunk=RetrievalChunk(
                    title=chunk.title,
                    snippet=chunk.snippet,
                    source=chunk.source,
                    matched_terms=max(chunk.matched_terms, coverage),
                    ordinal=chunk.ordinal,
                ),
            )
        )
    ranked.sort(
        key=lambda item: (
            -item.score,
            -item.coverage,
            -item.title_overlap,
            item.chunk.ordinal,
            item.chunk.source,
        )
    )
    return ranked
