from __future__ import annotations

from core.oracle_service import OracleReply, OracleService

from .command_parser import parse_command
from .radio_interface import IncomingMessage, OutboundMessage


class MessageRouter:
    """Convert incoming radio traffic into oracle responses."""

    def __init__(self, oracle_service: OracleService) -> None:
        self.oracle_service = oracle_service

    def route(self, message: IncomingMessage) -> list[OutboundMessage]:
        if not message.is_direct_message:
            return []

        command = parse_command(message.text)
        reply = self.oracle_service.handle(command)
        return self._to_outbound_messages(message, reply)

    def _to_outbound_messages(
        self, message: IncomingMessage, reply: OracleReply
    ) -> list[OutboundMessage]:
        responses = [
            OutboundMessage(
                destination=message.sender_id,
                text=reply.text,
                channel=message.channel,
            )
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
        return responses
