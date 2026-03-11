from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class IncomingMessage:
    sender_id: str
    text: str
    channel: int = 0
    is_direct_message: bool = True


@dataclass(frozen=True)
class OutboundMessage:
    destination: str
    text: str
    channel: int = 0
    send_position: bool = False


@dataclass
class DryRunRadio:
    """In-memory transport for local development and tests."""

    inbox: list[IncomingMessage] = field(default_factory=list)
    sent: list[OutboundMessage] = field(default_factory=list)

    def receive(self) -> list[IncomingMessage]:
        messages = list(self.inbox)
        self.inbox.clear()
        return messages

    def send(self, message: OutboundMessage) -> None:
        self.sent.append(message)
