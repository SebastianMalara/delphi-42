from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


MESHTASTIC_BROADCAST_ID = "^all"
MESHTASTIC_BROADCAST_NUM = 0xFFFFFFFF


class RadioTransportError(RuntimeError):
    """Raised when the radio transport cannot send, receive, or initialize."""


class PositionUnavailableError(RadioTransportError):
    """Raised when the local node cannot provide a private position packet."""


class RadioClient(Protocol):
    def receive(self) -> list["IncomingMessage"]:
        ...

    def send_text(self, message: "OutboundMessage") -> None:
        ...

    def send_position(self, message: "OutboundMessage") -> None:
        ...

    def close(self) -> None:
        ...


@dataclass(frozen=True)
class MeshPacketMetrics:
    rx_rssi: int | None = None
    rx_snr: float | None = None
    hop_start: int | None = None
    hop_limit: int | None = None
    rx_time: int | None = None
    to_id: str | None = None


@dataclass(frozen=True)
class IncomingMessage:
    sender_id: str
    text: str
    channel: int = 0
    is_direct_message: bool = True
    packet_id: str | None = None
    mesh: MeshPacketMetrics | None = None


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

    def queue_message(self, message: IncomingMessage) -> None:
        self.inbox.append(message)

    def send_text(self, message: OutboundMessage) -> None:
        self.sent.append(message)

    def send_position(self, message: OutboundMessage) -> None:
        self.sent.append(
            OutboundMessage(
                destination=message.destination,
                text=message.text,
                channel=message.channel,
                send_position=True,
            )
        )

    def close(self) -> None:
        return None


class MeshtasticRadioClient:
    """Meshtastic serial adapter with a small queue-based polling API."""

    def __init__(
        self,
        device_path: str,
        channel: int = 0,
        *,
        interface_factory: Callable[..., Any] | None = None,
        pubsub_module: Any | None = None,
    ) -> None:
        self.device_path = device_path
        self.channel = channel
        self._queue: deque[IncomingMessage] = deque()

        if interface_factory is None or pubsub_module is None:
            try:
                from pubsub import pub
                import meshtastic.serial_interface
            except ImportError as exc:
                raise RuntimeError(
                    "Meshtastic support requires the optional bot dependencies."
                ) from exc
            interface_factory = interface_factory or meshtastic.serial_interface.SerialInterface
            pubsub_module = pubsub_module or pub

        self._pubsub = pubsub_module
        self._callback = self._handle_receive
        try:
            self._interface = interface_factory(devPath=device_path)
        except Exception as exc:
            raise RadioTransportError(
                f"Failed to open Meshtastic interface on {device_path}"
            ) from exc
        self._pubsub.subscribe(self._callback, "meshtastic.receive")

    def receive(self) -> list[IncomingMessage]:
        messages = list(self._queue)
        self._queue.clear()
        return messages

    def send_text(self, message: OutboundMessage) -> None:
        try:
            self._interface.sendText(
                message.text,
                destinationId=message.destination,
                channelIndex=message.channel,
            )
        except Exception as exc:
            raise RadioTransportError("Meshtastic sendText failed") from exc

    def send_position(self, message: OutboundMessage) -> None:
        position = self._current_position()
        try:
            self._interface.sendPosition(
                destinationId=message.destination,
                channelIndex=message.channel,
                **position,
            )
        except Exception as exc:
            raise RadioTransportError("Meshtastic sendPosition failed") from exc

    def close(self) -> None:
        try:
            self._pubsub.unsubscribe(self._callback, "meshtastic.receive")
        except Exception:
            pass
        try:
            self._interface.close()
        except Exception:
            pass

    def _handle_receive(self, packet: dict, interface: Any) -> None:
        text = (
            packet.get("decoded", {}).get("text")
            or packet.get("decoded", {}).get("payload")
            or ""
        )
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")
        if not isinstance(text, str) or not text.strip():
            return

        is_direct_message = self._is_direct_message(packet, interface)
        self._queue.append(
            IncomingMessage(
                sender_id=str(packet.get("fromId") or packet.get("from") or "unknown"),
                text=text.strip(),
                channel=int(packet.get("channel", self.channel)),
                is_direct_message=is_direct_message,
                packet_id=str(packet.get("id")) if packet.get("id") is not None else None,
                mesh=MeshPacketMetrics(
                    rx_rssi=_optional_int(packet.get("rxRssi")),
                    rx_snr=_optional_float(packet.get("rxSnr")),
                    hop_start=_optional_int(packet.get("hopStart")),
                    hop_limit=_optional_int(packet.get("hopLimit")),
                    rx_time=_optional_int(packet.get("rxTime")),
                    to_id=str(packet.get("toId")) if packet.get("toId") is not None else None,
                ),
            )
        )

    def _is_direct_message(self, packet: dict, interface: Any) -> bool:
        destination_id = packet.get("toId")
        destination_num = packet.get("to")
        if destination_id and destination_id != MESHTASTIC_BROADCAST_ID:
            return True
        if destination_num is None or destination_num == MESHTASTIC_BROADCAST_NUM:
            return False
        local_node_num = getattr(getattr(interface, "localNode", None), "nodeNum", None)
        return destination_num == local_node_num

    def _current_position(self) -> dict[str, float]:
        local_node = getattr(self._interface, "localNode", None)
        if local_node is None:
            raise PositionUnavailableError(
                "Meshtastic local node is unavailable; cannot send position"
            )

        nodes_by_num = getattr(self._interface, "nodesByNum", {}) or {}
        node_info = nodes_by_num.get(local_node.nodeNum, {})
        position = node_info.get("position", {})
        latitude = position.get("latitude")
        longitude = position.get("longitude")
        if latitude is None or longitude is None:
            raise PositionUnavailableError(
                "Meshtastic local node does not have a position fix"
            )

        altitude = position.get("altitude")
        precision_bits = position.get("precisionBits", 13)

        payload: dict[str, float] = {
            "latitude": latitude,
            "longitude": longitude,
            "precisionBits": precision_bits,
        }
        if altitude is not None:
            payload["altitude"] = altitude
        return payload


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
