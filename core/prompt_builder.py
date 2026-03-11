from __future__ import annotations

from typing import Sequence

from .retriever import RetrievalChunk


def build_prompt(
    question: str,
    context_chunks: Sequence[RetrievalChunk],
    max_words: int = 40,
) -> str:
    """Build a compact grounding prompt for a local model."""
    if context_chunks:
        context_lines = [
            f"- {chunk.title} ({chunk.source}): {chunk.snippet}"
            for chunk in context_chunks
        ]
    else:
        context_lines = ["(no matching passages)"]

    context_block = "\n".join(context_lines)
    return (
        "You are Delphi-42, an offline oracle node.\n"
        f"Word limit: {max_words} words.\n"
        "Only answer from the provided local context.\n"
        "If the context is insufficient, say that the archive does not contain a grounded answer.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question:\n{question}\n"
    )
