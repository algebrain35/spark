"""
Frames the phone sends, and the error frame the server sends back.

Phone -> server
    {"type": "send", "match_id": "...", "body": "hey!", "client_msg_id": "..."}
    {"type": "read", "match_id": "...", "up_to": "<newest message id Bob has seen>"}

Server -> phone
    {"type": "ack",         "client_msg_id": "...", "id": "..."}
    {"type": "message",     "id": "...", "match_id": "...", "sender_id": "...", "body": "..."}
    {"type": "read",        "match_id": "...", "reader_id": "...", "up_to": "..."}
    {"type": "chat_closed", "match_id": "..."}
    {"type": "error",       "reason": "...", "client_msg_id": "..."}
"""

from typing import Literal
from uuid import UUID

from fastapi import WebSocket
from pydantic import BaseModel, Field


class SendFrame(BaseModel):
    type: Literal["send"]
    match_id: UUID
    body: str = Field(min_length=1, max_length=2000)   # spec section 4
    client_msg_id: str | None = None                   # lets the phone match the ack to its message


class ReadFrame(BaseModel):
    type: Literal["read"]
    match_id: UUID
    up_to: UUID     # only what Bob actually saw, not "everything in the chat"


async def send_error(ws: WebSocket, reason: str, client_msg_id=None) -> None:
    await ws.send_json({"type": "error", "reason": reason, "client_msg_id": client_msg_id})
