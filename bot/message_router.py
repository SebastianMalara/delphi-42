from __future__ import annotations

from dataclasses import dataclass

from core.oracle_service import OracleReply, OracleService

from .command_parser import parse_command
from .radio_interface import IncomingMessage, OutboundMessage


@dataclass(frozen=True)
class RoutedReply:
    inbound: IncomingMessage
    reply: OracleReply
    messages: tuple[OutboundMessage, ...]


class MessageRouter:
    """Convert incoming radio traffic into oracle responses."""

    def __init__(self, oracle_service: OracleService) -> None:
        self.oracle_service = oracle_service

    def route(self, message: IncomingMessage) -> RoutedReply | None:
        if not message.is_direct_message:
            return None

        command = parse_command(message.text)
        reply = self.oracle_service.handle(
            command,
            sender_id=message.sender_id,
            incoming_message=message,
        )
        return RoutedReply(
            inbound=message,
            reply=reply,
            messages=self._to_outbound_messages(message, reply),
        )

    def _to_outbound_messages(
        self, message: IncomingMessage, reply: OracleReply
    ) -> tuple[OutboundMessage, ...]:
        responses = [
            OutboundMessage(
                destination=message.sender_id,
                text=packet,
                channel=message.channel,
            )
            for packet in reply.packets
        ]
        if reply.share_position:
            responses.append(
                OutboundMessage(
                    destination=message.sender_id,
                    text="[private position packet]",
                    channel=message.channel,
                    send_position=True,
                )
            )
        return tuple(responses)
