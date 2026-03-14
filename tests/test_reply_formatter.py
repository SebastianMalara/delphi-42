from core.reply_formatter import (
    fits_utf8_bytes,
    prefix_text,
    split_prefixed_packets,
    split_text_by_bytes,
    trim_text,
    trim_to_utf8_bytes,
)


def test_split_text_by_bytes_respects_part_limit() -> None:
    parts = split_text_by_bytes(
        "One. Two. Three. Four. Five.",
        max_bytes=10,
        max_parts=2,
    )

    assert len(parts) == 2
    assert all(len(part.encode("utf-8")) <= 10 for part in parts)


def test_trim_text_appends_ellipsis_when_needed() -> None:
    assert trim_text("one two three four", 12).endswith("...")


def test_trim_to_utf8_bytes_keeps_text_within_budget() -> None:
    trimmed = trim_to_utf8_bytes("🤖 one two three four", 16)
    assert len(trimmed.encode("utf-8")) <= 16


def test_split_prefixed_packets_accounts_for_prefix_bytes() -> None:
    packets = split_prefixed_packets(
        "Use reflective material. Keep it in direct sun. Sweep slowly.",
        prefix="🤖 ",
        packet_byte_limit=24,
        max_parts=3,
    )

    assert packets
    assert all(packet.startswith("🤖 ") for packet in packets)
    assert all(fits_utf8_bytes(packet, 24) for packet in packets)


def test_prefix_text_adds_prefix_once() -> None:
    assert prefix_text("hello", "🤖 ") == "🤖 hello"
