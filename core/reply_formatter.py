from __future__ import annotations

import re


def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())


def trim_text(text: str, max_chars: int) -> str:
    normalized = normalize_text(text)
    if max_chars <= 0:
        return ""
    if len(normalized) <= max_chars:
        return normalized
    if max_chars <= 3:
        return normalized[:max_chars]

    cutoff = normalized[: max_chars - 3].rstrip()
    if " " in cutoff:
        cutoff = cutoff.rsplit(" ", maxsplit=1)[0]
    cutoff = cutoff.rstrip(".,;: ")
    return (cutoff or normalized[: max_chars - 3]).rstrip() + "..."


def trim_to_utf8_bytes(text: str, max_bytes: int) -> str:
    normalized = normalize_text(text)
    encoded = normalized.encode("utf-8")
    if max_bytes <= 0 or len(encoded) <= max_bytes:
        return normalized

    ellipsis = "..."
    budget = max(max_bytes - len(ellipsis.encode("utf-8")), 0)
    trimmed = normalized
    while trimmed and len(trimmed.encode("utf-8")) > budget:
        trimmed = trimmed[:-1]
    trimmed = trimmed.rstrip(" .,;:")
    return f"{trimmed or normalized[:1]}{ellipsis}"


def split_text_by_bytes(text: str, *, max_bytes: int, max_parts: int) -> list[str]:
    normalized = normalize_text(text)
    if not normalized or max_parts <= 0:
        return []
    if max_bytes <= 0 or len(normalized.encode("utf-8")) <= max_bytes:
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
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
            continue

        if current:
            parts.append(current)
            current = ""
            if len(parts) == max_parts:
                return _trim_final_part(parts, max_bytes)

        if len(sentence.encode("utf-8")) <= max_bytes:
            current = sentence
            continue

        for fragment in _split_long_fragment_by_bytes(sentence, max_bytes):
            parts.append(fragment)
            if len(parts) == max_parts:
                return _trim_final_part(parts, max_bytes)

    if current:
        parts.append(current)

    return _trim_final_part(parts[:max_parts], max_bytes)


def prefix_text(text: str, prefix: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return normalize_text(prefix)
    return f"{prefix}{normalized}"


def split_prefixed_packets(
    text: str,
    *,
    prefix: str,
    packet_byte_limit: int,
    max_parts: int,
) -> list[str]:
    payload_limit = packet_payload_budget(prefix, packet_byte_limit)
    parts = split_text_by_bytes(text, max_bytes=payload_limit, max_parts=max_parts)
    return [prefix_text(part, prefix) for part in parts]


def packet_payload_budget(prefix: str, packet_byte_limit: int) -> int:
    if packet_byte_limit <= 0:
        return 0
    return max(packet_byte_limit - len(prefix.encode("utf-8")), 1)


def fits_utf8_bytes(text: str, max_bytes: int) -> bool:
    return max_bytes <= 0 or len(normalize_text(text).encode("utf-8")) <= max_bytes


def first_sentence(text: str) -> str:
    normalized = normalize_text(text)
    if not normalized:
        return ""
    sentences = [chunk for chunk in re.split(r"(?<=[.!?])\s+", normalized) if chunk]
    return sentences[0] if sentences else normalized


def _split_long_fragment_by_bytes(text: str, max_bytes: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    parts: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate.encode("utf-8")) <= max_bytes:
            current = candidate
            continue

        if current:
            parts.append(current)
        if len(word.encode("utf-8")) > max_bytes:
            parts.append(trim_to_utf8_bytes(word, max_bytes))
            current = ""
        else:
            current = word

    if current:
        parts.append(current)
    return parts


def _trim_final_part(parts: list[str], max_bytes: int) -> list[str]:
    if not parts:
        return []
    if max_bytes > 0 and len(parts[-1].encode("utf-8")) > max_bytes:
        parts[-1] = trim_to_utf8_bytes(parts[-1], max_bytes)
    return parts
