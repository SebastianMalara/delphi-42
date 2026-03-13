from core.llm_runner import AnswerDraft
from core.reply_formatter import derive_short_answer, format_answer_packets, split_text, trim_text


def test_format_answer_packets_deduplicates_identical_short_and_long() -> None:
    packets = format_answer_packets(
        AnswerDraft(
            short_answer="Boil water for one minute before drinking.",
            extended_answer="Boil water for one minute before drinking.",
        ),
        short_max_chars=120,
        continuation_max_chars=600,
        max_continuation_packets=3,
    )

    assert packets == ("Boil water for one minute before drinking.",)


def test_format_answer_packets_numbers_multiple_continuations() -> None:
    packets = format_answer_packets(
        AnswerDraft(
            short_answer="Use reflective material.",
            extended_answer=(
                "Use reflective material to improve daytime visibility. "
                "Keep it in direct sun. Sweep it slowly. "
                "Repeat the motion until rescuers notice you."
            ),
        ),
        short_max_chars=40,
        continuation_max_chars=45,
        max_continuation_packets=3,
    )

    assert len(packets) >= 2
    assert packets[0] == "Use reflective material."
    assert any(packet.startswith("1/") for packet in packets[1:])


def test_split_text_respects_part_limit() -> None:
    parts = split_text(
        "One. Two. Three. Four. Five.",
        max_chars=10,
        max_parts=2,
    )

    assert len(parts) == 2
    assert all(len(part) <= 10 for part in parts)


def test_trim_text_appends_ellipsis_when_needed() -> None:
    assert trim_text("one two three four", 12).endswith("...")


def test_derive_short_answer_uses_first_sentence() -> None:
    short = derive_short_answer(
        "Clean the wound. Cover it with a sterile dressing.",
        max_chars=24,
    )

    assert short == "Clean the wound."
