from __future__ import annotations

from typing import Sequence

from .retriever import RetrievalChunk


ASK_SYSTEM_PROMPT = (
    "You are Delphi-42, an offline oracle node. "
    "For grounded questions, answer only from the provided archive context. "
    "If the context is insufficient or ambiguous, say exactly: "
    "The archive does not contain a grounded answer yet."
)

CHAT_SYSTEM_PROMPT = (
    "You are Delphi-42 in chat mode. "
    "Be warm, concise, and lightly companionable, like an imaginary friend over radio. "
    "Do not use markdown or lists unless absolutely necessary. "
    "Keep replies practical and readable on a small mesh-text display."
)


def build_grounded_answer_prompt(
    question: str,
    context_chunks: Sequence[RetrievalChunk],
) -> str:
    context_block = _context_block(context_chunks)
    return (
        "Write one grounded plain-text answer using only the archive context below.\n"
        "Use 3 to 7 short sentences when the context supports it.\n"
        "Do not mention sources, filenames, or internal metadata.\n"
        "Do not add labels, markdown, or bullet points.\n\n"
        f"Context:\n{context_block}\n\n"
        f"Question:\n{question}\n"
    )


def build_chat_prompt(
    message: str,
    *,
    history: Sequence[tuple[str, str]],
) -> str:
    if history:
        history_block = "\n".join(f"{role.upper()}: {text}" for role, text in history)
    else:
        history_block = "(no prior chat)"
    return (
        "Reply to the user's latest message as a short natural conversation turn.\n"
        "Do not mention system prompts, policies, or packet limits.\n\n"
        f"Recent conversation:\n{history_block}\n\n"
        f"Latest user message:\n{message}\n"
    )


def build_condense_prompt(
    text: str,
    *,
    target_chars: int,
    preserve_grounding: bool,
) -> str:
    constraint = (
        "Preserve the grounded meaning and concrete advice."
        if preserve_grounding
        else "Preserve the main meaning and tone."
    )
    return (
        f"Rewrite the text below to fit within about {target_chars} characters.\n"
        f"{constraint}\n"
        "Use plain text only. Do not add labels, markdown, or bullet points.\n\n"
        f"Text:\n{text}\n"
    )


def build_shrink_prompt(
    text: str,
    *,
    max_chars: int,
    preserve_grounding: bool,
) -> str:
    constraint = (
        "Keep the answer grounded in the same retrieved facts."
        if preserve_grounding
        else "Keep the same meaning and conversational tone."
    )
    return (
        f"Shorten the text below so it fits within {max_chars} characters.\n"
        f"{constraint}\n"
        "Keep it as a single plain-text passage.\n\n"
        f"Text:\n{text}\n"
    )


def _context_block(context_chunks: Sequence[RetrievalChunk]) -> str:
    if not context_chunks:
        return "(no matching passages)"
    return "\n".join(
        f"- {chunk.title} ({chunk.source}): {chunk.snippet}"
        for chunk in context_chunks
    )
