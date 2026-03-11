from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class RetrievalChunk:
    title: str
    snippet: str
    source: str


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
        tokens = {token.lower() for token in question.split() if token.strip()}
        scored: list[tuple[int, RetrievalChunk]] = []

        for chunk in self.corpus:
            haystack = f"{chunk.title} {chunk.snippet}".lower()
            score = sum(1 for token in tokens if token in haystack)
            if score:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:limit]]
