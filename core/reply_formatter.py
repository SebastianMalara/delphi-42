from __future__ import annotations

import re

from .llm_runner import AnswerDraft


def format_answer_packets(
    draft: AnswerDraft,
    *,
    short_max_chars: int,
    continuation_max_chars: int,
    max_continuation_packets: int,
) -> tuple[str, ...]:
    short = _normalize(draft.short_answer) or _normalize(draft.extended_answer)
    first_packet = trim_text(short, short_max_chars)

    extended = _normalize(draft.extended_answer)
    if not extended or max_continuation_packets == 0:
        return (first_packet,)

    parts = split_text(
        extended,
        max_chars=continuation_max_chars,
        max_parts=max_continuation_packets,
    )
    if not parts:
        return (first_packet,)

    if parts and parts[0] == first_packet:
        parts = parts[1:]
    if not parts:
        return (first_packet,)

    if len(parts) == 1:
        return (first_packet, parts[0])

    numbered: list[str] = []
    total = len(parts)
    for idx, part in enumerate(parts, start=1):
        prefix = f"{idx}/{total} "
        payload = trim_text(part, continuation_max_chars - len(prefix))
        numbered.append(f"{prefix}{payload}")

    return (first_packet, *numbered)


def derive_short_answer(text: str, *, max_chars: int) -> str:
    normalized = _normalize(text)
    if not normalized:
        return ""

    sentences = [chunk for chunk in re.split(r"(?<=[.!?])\s+", normalized) if chunk]
    first = sentences[0] if sentences else normalized
    return trim_text(first, max_chars)


def split_text(text: str, *, max_chars: int, max_parts: int) -> list[str]:
    if max_parts <= 0:
        return []

    normalized = _normalize(text)
    if not normalized:
        return []
    if len(normalized) <= max_chars:
        return [normalized]

    sentences = [chunk for chunk in re.split(r"(?<=[.!?])\s+", normalized) if chunk]
    if not sentences:
        sentences = [normalized]

    parts: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        candidate = sentence if not current else f"{current} {sentence}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            parts.append(current)
            current = ""
            if len(parts) == max_parts:
                return _trim_final_part(parts, max_chars)

        if len(sentence) <= max_chars:
            current = sentence
            continue

        for fragment in _split_long_fragment(sentence, max_chars):
            parts.append(fragment)
            if len(parts) == max_parts:
                return _trim_final_part(parts, max_chars)

    if current:
        parts.append(current)

    return _trim_final_part(parts[:max_parts], max_chars)


def trim_text(text: str, max_chars: int) -> str:
    normalized = _normalize(text)
    if len(normalized) <= max_chars:
        return normalized

    if max_chars <= 3:
        return normalized[:max_chars]

    cutoff = normalized[: max_chars - 3].rstrip()
    if " " in cutoff:
        cutoff = cutoff.rsplit(" ", maxsplit=1)[0]
    cutoff = cutoff.rstrip(".,;: ")
    return (cutoff or normalized[: max_chars - 3]).rstrip() + "..."


def _normalize(text: str) -> str:
    return " ".join(text.strip().split())


def _split_long_fragment(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    parts: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current:
            parts.append(current)
        if len(word) > max_chars:
            parts.append(trim_text(word, max_chars))
            current = ""
        else:
            current = word

    if current:
        parts.append(current)
    return parts


def _trim_final_part(parts: list[str], max_chars: int) -> list[str]:
    if not parts:
        return []
    if len(parts[-1]) > max_chars:
        parts[-1] = trim_text(parts[-1], max_chars)
    return parts
