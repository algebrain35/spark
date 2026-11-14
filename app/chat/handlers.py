"""What the server does with each frame a phone sends."""

import json
from uuid import UUID

from fastapi import WebSocket
from pydantic import ValidationError

from app import swipes
from app.chat.protocol import ReadFrame, SendFrame, send_error
from app.chat.pubsub import publish_to_user
from app.db import db


async def handle_frame(user_id: UUID, ws: WebSocket, raw: str) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await send_error(ws, "bad_json")
        return
    if not isinstance(data, dict):
        await send_error(ws, "bad_frame")
        return

    entry = FRAME_TYPES.get(data.get("type"))
    if entry is None:
        await send_error(ws, "unknown_type", data.get("client_msg_id"))
        return

    model, handler = entry
    try:
        frame = model.model_validate(data)
    except ValidationError:
        await send_error(ws, "invalid_frame", data.get("client_msg_id"))
        return
    await handler(user_id, ws, frame)


async def handle_send(user_id: UUID, ws: WebSocket, frame: SendFrame) -> None:
    # Is this user in the match, and is it still active? Blocking also unmatches,
    # so this one check covers blocks too.
    partner_id = await swipes.get_active_partner(frame.match_id, user_id)
    if partner_id is None:
        await send_error(ws, "invalid_match", frame.client_msg_id)
        return

    # Save first: the ack is a promise that the message is stored,
    # and the UUIDv7 id comes from the database.
    msg_id = await db.fetchval(
        "INSERT INTO messages (match_id, sender_id, body) VALUES ($1, $2, $3) RETURNING id",
        frame.match_id, user_id, frame.body,
    )

    # Build the outgoing message from trusted values, never from the client's frame.
    out = {
        "type": "message",
        "id": str(msg_id),
        "match_id": str(frame.match_id),
        "sender_id": str(user_id),
        "body": frame.body,
    }

    # Publish before acking, so a sender who disconnects mid-ack doesn't block delivery.
    await publish_to_user(partner_id, out)
    await publish_to_user(user_id, out)     # the sender's other devices

    # TODO: enqueue a push notification for partner_id (design rule 3: via the worker queue)

    await ws.send_json({"type": "ack", "client_msg_id": frame.client_msg_id, "id": str(msg_id)})


async def handle_read(user_id: UUID, ws: WebSocket, frame: ReadFrame) -> None:
    partner_id = await swipes.get_active_partner(frame.match_id, user_id)
    if partner_id is None:
        await send_error(ws, "invalid_match")
        return

    status = await db.execute(
        """
        UPDATE messages SET read_at = now()
        WHERE match_id = $1
          AND sender_id <> $2        -- only the other person's messages
          AND id <= $3               -- only what the reader actually saw
          AND read_at IS NULL        -- keep the first read time; resending is harmless
        """,
        frame.match_id, user_id, frame.up_to,
    )
    if status == "UPDATE 0":
        return          # nothing newly read, so don't notify anyone

    out = {
        "type": "read",
        "match_id": str(frame.match_id),
        "reader_id": str(user_id),
        "up_to": str(frame.up_to),
    }
    await publish_to_user(partner_id, out)   # Alice's "read" ticks
    await publish_to_user(user_id, out)      # clears the unread badge on Bob's other devices


# frame "type" -> (model to validate with, handler). Add new frame types here.
FRAME_TYPES = {
    "send": (SendFrame, handle_send),
    "read": (ReadFrame, handle_read),
}
