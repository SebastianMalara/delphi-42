from bot.command_parser import parse_command


def test_parse_explicit_ask_command() -> None:
    command = parse_command("ask how to purify water")
    assert command.name == "ask"
    assert command.argument == "how to purify water"


def test_parse_plain_text_as_implicit_question() -> None:
    command = parse_command("hypothermia symptoms")
    assert command.name == "ask"
    assert command.argument == "hypothermia symptoms"


def test_empty_message_returns_help() -> None:
    command = parse_command("   ")
    assert command.name == "help"
