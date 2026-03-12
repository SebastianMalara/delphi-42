from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .html_normalizer import normalize_html_to_text


@dataclass(frozen=True)
class ExtractedDocument:
    title: str
    source_id: str
    text: str


class ZimDependencyError(RuntimeError):
    """Raised when optional ZIM support is unavailable."""


class ZimExtractor:
    """Extract normalized plaintext documents from a ZIM archive."""

    def __init__(self, archive_opener=None) -> None:
        self.archive_opener = archive_opener or self._open_archive

    def extract(self, source_path: Path) -> list[ExtractedDocument]:
        archive = self.archive_opener(source_path)

        if hasattr(archive, "iter_documents"):
            return list(archive.iter_documents(source_path.name))

        documents: list[ExtractedDocument] = []
        entry_count = getattr(archive, "all_entry_count", 0)

        for entry_index in range(entry_count):
            entry = archive._get_entry_by_id(entry_index)
            if getattr(entry, "is_redirect", False):
                continue

            item = entry.get_item()
            mimetype = str(getattr(item, "mimetype", ""))
            if not mimetype.startswith("text/"):
                continue

            article_path = str(getattr(item, "path", "") or getattr(entry, "path", ""))
            if not article_path:
                continue

            title = str(getattr(item, "title", "") or _path_to_title(article_path))
            text = normalize_html_to_text(_decode_content(getattr(item, "content", b"")))
            if not text.strip():
                continue

            documents.append(
                ExtractedDocument(
                    title=title,
                    source_id=f"{source_path.name}:{article_path}",
                    text=text,
                )
            )

        return documents

    def _open_archive(self, source_path: Path):
        try:
            from libzim.reader import Archive
        except ImportError as exc:
            raise ZimDependencyError(
                "ZIM extraction requires the optional 'libzim' dependency."
            ) from exc
        return Archive(source_path)


def _decode_content(raw_content) -> str:
    if isinstance(raw_content, bytes):
        return raw_content.decode("utf-8", errors="ignore")

    try:
        return bytes(raw_content).decode("utf-8", errors="ignore")
    except Exception:
        return str(raw_content)


def _path_to_title(article_path: str) -> str:
    return Path(article_path).stem.replace("_", " ")
