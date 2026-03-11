from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from .chunker import TextChunk, chunk_text
from .zim_extract import ExtractedDocument


class SQLiteIndexBuilder:
    """Build a simple FTS5 index from extracted plaintext chunks."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def build(self, chunks: list[TextChunk]) -> int:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5("
                "source_id, ordinal UNINDEXED, text)"
            )
            connection.execute("DELETE FROM chunks")
            connection.executemany(
                "INSERT INTO chunks(source_id, ordinal, text) VALUES (?, ?, ?)",
                [(chunk.source_id, chunk.ordinal, chunk.text) for chunk in chunks],
            )
            connection.commit()
        return len(chunks)


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
        chunks.extend(chunk_text(document.source_id, document.text))
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
