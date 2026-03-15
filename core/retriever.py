from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Callable, Sequence, Protocol


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


class KiwixDependencyError(RuntimeError):
    """Raised when the optional Kiwix runtime dependencies are unavailable."""


class NullRetriever:
    """Fallback retriever used until a real archive is attached."""

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        return []


class KeywordRetriever:
    """Small deterministic retriever for development and tests."""

    def __init__(self, chunks: Sequence[RetrievalChunk]) -> None:
        self.chunks = list(chunks)

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        query_terms = normalized_query_terms(question)
        ranked = _score_candidates(query_terms, self.chunks)
        return [item.chunk for item in ranked[: max(limit, 0)]]


class KiwixRetriever:
    """Kiwix-backed retriever that searches allowlisted ZIM archives directly."""

    def __init__(
        self,
        zim_dir: Path,
        allowlist: Sequence[str],
        *,
        default_limit: int = 3,
        search_limit: int = 3,
        search_fn: Callable[[str, str], tuple[int, list[object]]] | None = None,
        read_fn: Callable[[str, str], str] | None = None,
    ) -> None:
        self.zim_dir = zim_dir
        self.allowlist = tuple(allowlist)
        self.default_limit = default_limit
        self.search_limit = search_limit

        if search_fn is None or read_fn is None:
            try:
                from llm_tools_kiwix import kiwix_read, kiwix_search
            except ImportError as exc:
                raise KiwixDependencyError(
                    "llm_tools_kiwix is not installed; install the optional Kiwix dependency."
                ) from exc
            search_fn = search_fn or kiwix_search
            read_fn = read_fn or kiwix_read

        self._search_fn = search_fn
        self._read_fn = read_fn

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        query_terms = normalized_query_terms(question)
        if not query_terms:
            return []

        requested_limit = max(limit or self.default_limit, 1)
        candidates: list[RetrievalChunk] = []
        for filename in self.allowlist:
            zim_path = str((self.zim_dir / filename).resolve())
            _, article_paths = self._search_fn(zim_path, question)
            for article_path in self._normalize_article_paths(article_paths)[: self.search_limit]:
                article_text = self._read_fn(zim_path, article_path)
                if not article_text or _looks_like_kiwix_error(article_text):
                    continue
                candidates.extend(
                    _article_chunks(
                        archive_name=filename,
                        article_path=article_path,
                        article_text=article_text,
                        query_terms=query_terms,
                    )
                )

        ranked = _score_candidates(query_terms, candidates)
        candidate_limit = max(requested_limit * 6, 12)
        return [item.chunk for item in ranked[:candidate_limit]]

    def _normalize_article_paths(self, article_paths: Sequence[object]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for item in article_paths:
            path = _result_path(item)
            if not path or path in seen:
                continue
            normalized.append(path)
            seen.add(path)
        return normalized


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
        context = tuple(candidate.chunk for candidate in by_source[:context_limit])

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
    "while",
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


def _article_chunks(
    *,
    archive_name: str,
    article_path: str,
    article_text: str,
    query_terms: Sequence[str],
) -> list[RetrievalChunk]:
    title = _path_to_title(article_path)
    normalized_text = " ".join(article_text.strip().split())
    if not normalized_text:
        return []

    sentences = [chunk.strip() for chunk in re.split(r"(?<=[.!?])\s+", normalized_text) if chunk.strip()]
    if not sentences:
        sentences = [normalized_text]

    chunks: list[RetrievalChunk] = []
    window_size = 2
    for index in range(len(sentences)):
        window = _trim_retrieval_snippet(" ".join(sentences[index : index + window_size]).strip())
        if not window:
            continue
        coverage = score_query_terms(query_terms, title, window)
        if coverage <= 0:
            continue
        chunks.append(
            RetrievalChunk(
                title=title,
                snippet=window,
                source=f"{archive_name}:{article_path}",
                matched_terms=coverage,
                ordinal=index,
            )
        )
    if chunks:
        return chunks

    return [
        RetrievalChunk(
            title=title,
            snippet=_trim_retrieval_snippet(normalized_text),
            source=f"{archive_name}:{article_path}",
            matched_terms=score_query_terms(query_terms, title, normalized_text),
            ordinal=0,
        )
    ]


def _trim_retrieval_snippet(text: str, max_chars: int = 420) -> str:
    normalized = " ".join(text.strip().split())
    if len(normalized) <= max_chars:
        return normalized
    cutoff = normalized[:max_chars].rstrip()
    if " " in cutoff:
        cutoff = cutoff.rsplit(" ", maxsplit=1)[0]
    return cutoff.rstrip(" ,;:") + "..."


def _path_to_title(article_path: str) -> str:
    stem = Path(article_path).stem.replace("_", " ")
    return re.sub(r"(?<!^)(?=[A-Z])", " ", stem)


def _result_path(item: object) -> str:
    if isinstance(item, str):
        return item.strip()

    for attribute in ("path", "full_path", "url", "href"):
        value = getattr(item, attribute, None)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return str(item).strip()


def _looks_like_kiwix_error(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered.startswith("error") or lowered.startswith("an unexpected error")
