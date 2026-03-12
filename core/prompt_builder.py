from __future__ import annotations

from typing import Sequence

from .retriever import RetrievalChunk


def build_prompt(
    question: str,
    context_chunks: Sequence[RetrievalChunk],
    short_max_chars: int = 120,
    continuation_max_chars: int = 600,
    max_continuation_packets: int = 3,
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
        "Only answer from the provided local context.\n"
        "If the context is insufficient, say that the archive does not contain a grounded answer.\n\n"
        "Return exactly this format:\n"
        "SHORT: <one-line direct answer>\n"
        "LONG:\n"
        "<full grounded answer>\n\n"
        f"SHORT must target {short_max_chars} characters or less.\n"
        f"LONG must be suitable for splitting into at most {max_continuation_packets} packets of {continuation_max_chars} characters.\n"
        "Do not include markdown, bullet lists, or extra headings.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question:\n{question}\n"
    )
