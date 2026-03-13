from bot.radio_interface import (
    MESHTASTIC_BROADCAST_ID,
    MeshtasticRadioClient,
    OutboundMessage,
    PositionUnavailableError,
    RadioTransportError,
)


class StubPubSub:
    def __init__(self) -> None:
        self.callbacks: dict[str, object] = {}

    def subscribe(self, callback, topic: str) -> None:
        self.callbacks[topic] = callback

    def unsubscribe(self, callback, topic: str) -> None:
        self.callbacks.pop(topic, None)


class StubLocalNode:
    nodeNum = 42


class StubInterface:
    def __init__(self, devPath: str) -> None:
        self.devPath = devPath
        self.localNode = StubLocalNode()
        self.nodesByNum = {
            42: {
                "position": {
                    "latitude": 45.0,
                    "longitude": 11.0,
                    "altitude": 100,
                    "precisionBits": 9,
                }
            }
        }
        self.text_messages: list[dict] = []
        self.position_messages: list[dict] = []
        self.closed = False

    def sendText(self, text: str, destinationId: str, channelIndex: int) -> None:
        self.text_messages.append(
            {
                "text": text,
                "destinationId": destinationId,
                "channelIndex": channelIndex,
            }
        )

    def sendPosition(self, **kwargs) -> None:
        self.position_messages.append(kwargs)

    def close(self) -> None:
        self.closed = True


class NoPositionStubInterface(StubInterface):
    def __init__(self, devPath: str) -> None:
        super().__init__(devPath)
        self.nodesByNum = {42: {"position": {}}}


class FailingSendInterface(StubInterface):
    def sendText(self, text: str, destinationId: str, channelIndex: int) -> None:
        raise RuntimeError("serial write failed")


def test_meshtastic_radio_client_normalizes_packets_and_sends_responses() -> None:
    pubsub = StubPubSub()
    interface = StubInterface("/dev/ttyUSB0")
    client = MeshtasticRadioClient(
        "/dev/ttyUSB0",
        channel=3,
        interface_factory=lambda devPath: interface,
        pubsub_module=pubsub,
    )

    receive_callback = pubsub.callbacks["meshtastic.receive"]
    receive_callback(
        {
            "fromId": "!abcd",
            "toId": "!local",
            "channel": 3,
            "id": 7,
            "decoded": {"text": "ask water"},
        },
        interface,
    )
    receive_callback(
        {
            "fromId": "!abcd",
            "toId": MESHTASTIC_BROADCAST_ID,
            "channel": 3,
            "decoded": {"text": "public message"},
        },
        interface,
    )

    messages = client.receive()

    assert messages[0].sender_id == "!abcd"
    assert messages[0].is_direct_message is True
    assert messages[1].is_direct_message is False

    client.send_text(
        OutboundMessage(
            destination="!abcd",
            text="reply",
            channel=3,
        )
    )
    client.send_position(
        OutboundMessage(
            destination="!abcd",
            text="[private position packet]",
            channel=3,
            send_position=True,
        )
    )
    client.close()

    assert interface.text_messages == [
        {"text": "reply", "destinationId": "!abcd", "channelIndex": 3}
    ]
    assert interface.position_messages == [
        {
            "destinationId": "!abcd",
            "channelIndex": 3,
            "latitude": 45.0,
            "longitude": 11.0,
            "altitude": 100,
            "precisionBits": 9,
        }
    ]
    assert interface.closed is True


def test_meshtastic_radio_client_raises_position_unavailable_without_fix() -> None:
    pubsub = StubPubSub()
    interface = NoPositionStubInterface("/dev/ttyUSB0")
    client = MeshtasticRadioClient(
        "/dev/ttyUSB0",
        channel=3,
        interface_factory=lambda devPath: interface,
        pubsub_module=pubsub,
    )

    try:
        try:
            client.send_position(
                OutboundMessage(
                    destination="!abcd",
                    text="[private position packet]",
                    channel=3,
                    send_position=True,
                )
            )
        except PositionUnavailableError as exc:
            assert "position fix" in str(exc)
        else:
            raise AssertionError("expected PositionUnavailableError")
    finally:
        client.close()


def test_meshtastic_radio_client_wraps_send_failures() -> None:
    pubsub = StubPubSub()
    interface = FailingSendInterface("/dev/ttyUSB0")
    client = MeshtasticRadioClient(
        "/dev/ttyUSB0",
        channel=3,
        interface_factory=lambda devPath: interface,
        pubsub_module=pubsub,
    )

    try:
        try:
            client.send_text(
                OutboundMessage(
                    destination="!abcd",
                    text="reply",
                    channel=3,
                )
            )
        except RadioTransportError as exc:
            assert "sendText failed" in str(exc)
        else:
            raise AssertionError("expected RadioTransportError")
    finally:
        client.close()
