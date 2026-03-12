from __future__ import annotations

from pathlib import Path
import re
from typing import Sequence

from ingest.chunker import chunk_text
from ingest.html_normalizer import normalize_html_to_text

from .retriever import RetrievalChunk, Retriever


class RuntimeZimRetriever(Retriever):
    """Fallback retriever that searches curated local ZIM archives directly."""

    def __init__(
        self,
        zim_dir: Path,
        allowlist: Sequence[str],
        default_limit: int = 3,
        archive_opener=None,
    ) -> None:
        self.zim_dir = zim_dir
        self.allowlist = tuple(allowlist)
        self.default_limit = default_limit
        self.archive_opener = archive_opener or self._open_archive
        self.archives = [
            (filename, self.archive_opener(self.zim_dir / filename))
            for filename in self.allowlist
        ]

    def search(self, question: str, limit: int = 3) -> list[RetrievalChunk]:
        tokens = _tokenize(question)
        if not tokens:
            return []

        article_budget = min(limit or self.default_limit, self.default_limit)
        article_reads = 0
        candidate_chunks: list[tuple[int, int, RetrievalChunk]] = []

        for filename, archive in self.archives:
            if article_reads >= article_budget:
                break

            remaining = article_budget - article_reads
            for article_path in _search_paths(archive, question, remaining):
                if article_reads >= article_budget:
                    break

                title, raw_content = _read_article(archive, article_path)
                normalized = normalize_html_to_text(raw_content)
                if not normalized.strip():
                    continue

                source_id = f"{filename}:{article_path}"
                for chunk in chunk_text(source_id, normalized, title=title):
                    haystack = f"{title} {chunk.text}".lower()
                    score = sum(1 for token in tokens if token in haystack)
                    if score:
                        candidate_chunks.append(
                            (
                                score,
                                len(candidate_chunks),
                                RetrievalChunk(
                                    title=title,
                                    snippet=chunk.text,
                                    source=source_id,
                                    matched_terms=score,
                                ),
                            )
                        )

                article_reads += 1

        candidate_chunks.sort(key=lambda item: (-item[0], item[1]))
        return [chunk for _, _, chunk in candidate_chunks[:article_budget]]

    def _open_archive(self, source_path: Path):
        try:
            from libzim.reader import Archive
        except ImportError as exc:
            raise RuntimeError(
                "Runtime ZIM fallback requires the optional 'libzim' dependency."
            ) from exc
        return Archive(source_path)


def _search_paths(archive, question: str, limit: int) -> list[str]:
    if hasattr(archive, "search_paths"):
        return list(archive.search_paths(question, limit))

    try:
        from libzim.search import Query, Searcher
    except ImportError as exc:
        raise RuntimeError(
            "Runtime ZIM search requires the optional 'libzim' dependency."
        ) from exc

    searcher = Searcher(archive)
    search = searcher.search(Query().set_query(question))
    estimated_matches = search.getEstimatedMatches()
    if estimated_matches <= 0:
        return []

    return [str(result) for result in search.getResults(0, min(limit, estimated_matches))]


def _read_article(archive, article_path: str) -> tuple[str, str]:
    if hasattr(archive, "read_article"):
        article = archive.read_article(article_path)
        if isinstance(article, tuple):
            return article[0], article[1]
        return article["title"], article["content"]

    entry = archive.get_entry_by_path(article_path)
    item = entry.get_item()
    title = str(getattr(item, "title", "") or _path_to_title(article_path))
    raw_content = getattr(item, "content", b"")

    if isinstance(raw_content, bytes):
        return title, raw_content.decode("utf-8", errors="ignore")

    try:
        return title, bytes(raw_content).decode("utf-8", errors="ignore")
    except Exception:
        return title, str(raw_content)


def _path_to_title(article_path: str) -> str:
    return Path(article_path).stem.replace("_", " ")


def _tokenize(text: str) -> set[str]:
    return {token.lower() for token in re.findall(r"[A-Za-z0-9_]{2,}", text)}
