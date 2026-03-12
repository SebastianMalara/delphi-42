from __future__ import annotations

import argparse
import os
import sqlite3
import tempfile
from pathlib import Path

from .chunker import TextChunk, chunk_text
from .zim_extract import ExtractedDocument


class SQLiteIndexBuilder:
    """Build a simple FTS5 index from extracted plaintext chunks."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def build(self, chunks: list[TextChunk]) -> int:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        temp_db = self._temp_db_path()
        with sqlite3.connect(temp_db) as connection:
            connection.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5("
                "title, source_id UNINDEXED, ordinal UNINDEXED, text)"
            )
            connection.executemany(
                "INSERT INTO chunks(title, source_id, ordinal, text) VALUES (?, ?, ?, ?)",
                [
                    (chunk.title, chunk.source_id, chunk.ordinal, chunk.text)
                    for chunk in chunks
                ],
            )
            connection.commit()
        os.replace(temp_db, self.db_path)
        return len(chunks)

    def _temp_db_path(self) -> Path:
        with tempfile.NamedTemporaryFile(
            prefix=f"{self.db_path.stem}.",
            suffix=self.db_path.suffix or ".db",
            dir=self.db_path.parent,
            delete=False,
        ) as handle:
            return Path(handle.name)


def load_plaintext_documents(input_dir: Path) -> list[ExtractedDocument]:
    documents: list[ExtractedDocument] = []
    for path in sorted(input_dir.rglob("*.txt")):
        documents.append(
            ExtractedDocument(
                title=path.stem,
                source_id=str(path.relative_to(input_dir)),
                text=path.read_text(encoding="utf-8"),
            )
        )
    return documents


def build_chunks(documents: list[ExtractedDocument]) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for document in documents:
        chunks.extend(
            chunk_text(document.source_id, document.text, title=document.title)
        )
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Delphi-42 local text index.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Directory of .txt files.")
    parser.add_argument("--db", type=Path, required=True, help="Output SQLite database path.")
    args = parser.parse_args()

    if not args.input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {args.input_dir}")

    documents = load_plaintext_documents(args.input_dir)
    chunks = build_chunks(documents)
    total = SQLiteIndexBuilder(args.db).build(chunks)
    print(f"Indexed {len(documents)} documents into {total} chunks at {args.db}")


if __name__ == "__main__":
    main()
