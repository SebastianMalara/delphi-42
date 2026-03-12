from __future__ import annotations

import logging
import os
from pathlib import Path

from core.runtime_config import ConfigError

from .message_router import MessageRouter
from .oracle_bot import OracleBot, build_router, load_config
from .radio_interface import DryRunRadio, IncomingMessage


LOGGER = logging.getLogger("delphi42.dev_console")

HELP_TEXT = """Commands:
  <text>            Send a direct message from the current sender.
  /dm <text>        Send an explicit direct message.
  /public <text>    Send a public message and verify it is ignored.
  /sender <id>      Change the simulated sender ID.
  /channel <n>      Change the simulated channel.
  /reset            Clear the simulated inbox and sent history.
  /help             Show this help.
  /quit             Exit the console.
"""


def build_dev_console(config_path: Path) -> tuple[OracleBot, DryRunRadio, MessageRouter]:
    config = load_config(config_path)
    config.validate_for_bot()
    if config.radio.transport != "simulated":
        raise ConfigError("bot.dev_console requires radio.transport to be 'simulated'.")

    radio = DryRunRadio()
    router = build_router(config, logger=LOGGER)
    bot = OracleBot(radio=radio, router=router, logger=LOGGER)
    return bot, radio, router


def main() -> None:
    logging.basicConfig(level=os.environ.get("DELPHI_LOG_LEVEL", "INFO"))
    config_path = Path(os.environ.get("DELPHI_CONFIG", "config/oracle.dev.yaml"))

    try:
        bot, radio, _ = build_dev_console(config_path)
    except (ConfigError, FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc

    sender_id = "dev-node"
    channel = 0
    print(f"Delphi-42 dev console using {config_path}")
    print(HELP_TEXT)

    while True:
        try:
            raw = input(f"{sender_id}@ch{channel}> ").strip()
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            break

        if not raw:
            continue
        if raw in {"/quit", "/exit"}:
            break
        if raw == "/help":
            print(HELP_TEXT)
            continue
        if raw == "/reset":
            radio.inbox.clear()
            radio.sent.clear()
            print("Simulated inbox and sent history cleared.")
            continue
        if raw.startswith("/sender "):
            sender_id = raw.partition(" ")[2].strip() or sender_id
            print(f"Sender set to {sender_id}.")
            continue
        if raw.startswith("/channel "):
            value = raw.partition(" ")[2].strip()
            try:
                channel = int(value)
            except ValueError:
                print("Channel must be an integer.")
                continue
            print(f"Channel set to {channel}.")
            continue

        is_direct_message = True
        text = raw
        if raw.startswith("/dm "):
            text = raw.partition(" ")[2].strip()
        elif raw.startswith("/public "):
            text = raw.partition(" ")[2].strip()
            is_direct_message = False

        if not text:
            print("Message text must not be empty.")
            continue

        sent_before = len(radio.sent)
        radio.queue_message(
            IncomingMessage(
                sender_id=sender_id,
                text=text,
                channel=channel,
                is_direct_message=is_direct_message,
            )
        )
        events = bot.process_inbox()
        new_messages = radio.sent[sent_before:]

        if not new_messages:
            print("[no outbound packets]")
            if events:
                for event in events:
                    print(f"[event] {event}")
            continue

        for message in new_messages:
            kind = "POSITION" if message.send_position else "TEXT"
            payload = message.text if not message.send_position else "[private position packet]"
            print(f"{kind} -> {message.destination} [ch {message.channel}] {payload}")


if __name__ == "__main__":
    main()
