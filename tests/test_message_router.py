from bot.message_router import MessageRouter
from bot.radio_interface import IncomingMessage
from core.oracle_service import OracleService, ReplyMode
from core.retriever import KeywordRetriever, RetrievalChunk


def test_message_router_ignores_public_messages() -> None:
    router = MessageRouter(OracleService())

    routed = router.route(
        IncomingMessage(
            sender_id="node-1",
            text="ask water",
            is_direct_message=False,
        )
    )

    assert routed is None


def test_message_router_emits_private_position_packet() -> None:
    router = MessageRouter(OracleService())

    routed = router.route(
        IncomingMessage(
            sender_id="node-1",
            text="where",
            is_direct_message=True,
        )
    )

    assert routed is not None
    assert routed.reply.mode is ReplyMode.POSITION
    assert len(routed.messages) == 2
    assert routed.messages[1].send_position is True


def test_message_router_routes_grounded_ask_reply() -> None:
    router = MessageRouter(
        OracleService(
            retriever=KeywordRetriever(
                [
                    RetrievalChunk(
                        title="Shelter",
                        snippet="Pitch camp above the flood line.",
                        source="guide",
                    )
                ]
            )
        )
    )

    routed = router.route(
        IncomingMessage(
            sender_id="node-1",
            text="safe camp placement",
            is_direct_message=True,
        )
    )

    assert routed is not None
    assert routed.reply.mode is ReplyMode.DETERMINISTIC_FALLBACK
    assert routed.messages[0].destination == "node-1"
    assert "flood line" in routed.messages[0].text
