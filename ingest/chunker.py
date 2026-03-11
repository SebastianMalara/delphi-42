from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    source_id: str
    ordinal: int
    text: str


def chunk_text(source_id: str, text: str, max_chars: int = 420) -> list[TextChunk]:
    """Split extracted text into compact chunks suitable for local indexing."""
    normalized_paragraphs = [
        " ".join(paragraph.split())
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]

    if not normalized_paragraphs:
        return []

    chunks: list[TextChunk] = []
    current_parts: list[str] = []
    current_length = 0

    def flush() -> None:
        nonlocal current_parts, current_length
        if not current_parts:
            return
        chunks.append(
            TextChunk(
                source_id=source_id,
                ordinal=len(chunks),
                text=" ".join(current_parts),
            )
        )
        current_parts = []
        current_length = 0

    for paragraph in normalized_paragraphs:
        if len(paragraph) > max_chars:
            flush()
            for split_paragraph in _split_long_paragraph(paragraph, max_chars):
                chunks.append(
                    TextChunk(
                        source_id=source_id,
                        ordinal=len(chunks),
                        text=split_paragraph,
                    )
                )
            continue

        projected = current_length + len(paragraph) + (1 if current_parts else 0)
        if current_parts and projected > max_chars:
            flush()

        current_parts.append(paragraph)
        current_length += len(paragraph) + (1 if current_parts[:-1] else 0)

    flush()
    return chunks


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    pieces: list[str] = []
    current_words: list[str] = []
    current_length = 0

    for word in paragraph.split():
        projected = current_length + len(word) + (1 if current_words else 0)
        if current_words and projected > max_chars:
            pieces.append(" ".join(current_words))
            current_words = [word]
            current_length = len(word)
            continue

        current_words.append(word)
        current_length = projected

    if current_words:
        pieces.append(" ".join(current_words))

    return pieces
