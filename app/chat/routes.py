"""
HTTP and WebSocket endpoints for chat.

Phone reconnect order (for the mobile team):
    1. remember lastSeen = newest message id the phone already has
    2. open the WebSocket                 -> live messages start arriving
    3. GET /matches/{id}/messages?after=lastSeen
    4. merge both, dedupe by id, sort by id (UUIDv7 is time-ordered)
Never move lastSeen forward from a live message before the fetch in step 3 returns.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from app import auth, swipes
from app.chat.connections import manager
from app.chat.handlers import handle_frame
from app.chat.protocol import send_error
from app.db import db

log = logging.getLogger("spark.chat")
router = APIRouter()


@router.websocket("/ws")
async def chat_socket(ws: WebSocket, token: str):
    # Token in the URL can end up in server logs. Acceptable at demo scale; logged as deferred.
    user_id = auth.user_id_from_token(token)
    if user_id is None:
        await ws.close(code=1008)      # before accept(): rejects the handshake
        return

    await ws.accept()
    manager.add(user_id, ws)
    try:
        while True:
            raw = await ws.receive_text()
            try:
                await handle_frame(user_id, ws, raw)
            except WebSocketDisconnect:
                raise
            except Exception:
                # A bug or DB error in one frame shouldn't drop the whole connection.
                log.exception("error handling frame from %s", user_id)
                await send_error(ws, "server_error")
    except WebSocketDisconnect:
        pass
    finally:
        manager.remove(user_id, ws)    # runs however we leave the loop


@router.get("/matches/{match_id}/messages")
async def history(
    match_id: UUID,
    after: UUID | None = None,
    user_id: UUID = Depends(auth.current_user_id),
):
    """Initial load (no `after`) and catch-up after a reconnect (`after` = last id the phone has)."""
    if await swipes.get_active_partner(match_id, user_id) is None:
        raise HTTPException(status_code=404)

    rows = await db.fetch(
        """
        SELECT id, sender_id, body, read_at
        FROM messages
        WHERE match_id = $1 AND ($2::uuid IS NULL OR id > $2)
        ORDER BY id
        LIMIT 100
        """,
        match_id, after,
    )
    return [dict(row) for row in rows]
