from bot.command_parser import parse_command


def test_parse_explicit_ask_command() -> None:
    command = parse_command("?ask how to purify water")
    assert command.name == "ask"
    assert command.argument == "how to purify water"


def test_parse_explicit_chat_command() -> None:
    command = parse_command("?chat keep me company")
    assert command.name == "chat"
    assert command.argument == "keep me company"


def test_parse_position_aliases() -> None:
    assert parse_command("?where").name == "where"
    assert parse_command("?pos").name == "pos"


def test_bare_text_returns_help() -> None:
    command = parse_command("hypothermia symptoms")
    assert command.name == "help"


def test_missing_argument_returns_help() -> None:
    command = parse_command("?chat")
    assert command.name == "help"


def test_parse_mesh_command() -> None:
    command = parse_command("?mesh")
    assert command.name == "mesh"
    assert command.argument is None
