from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtractedDocument:
    title: str
    source_id: str
    text: str


class ZimExtractor:
    """Placeholder interface for wiring a real ZIM extraction tool."""

    def extract(self, source_path: Path) -> list[ExtractedDocument]:
        raise NotImplementedError(
            "Connect this class to zimdump, Kiwix tooling, or another offline extractor."
        )
