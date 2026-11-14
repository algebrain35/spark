"""The sockets held by THIS worker process."""

from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # A set per user: phone + tablet, or an old socket overlapping a reconnect.
        # Each socket only ever removes itself, so open/close order doesn't matter.
        self._by_user: dict[UUID, set[WebSocket]] = defaultdict(set)

    def add(self, user_id: UUID, ws: WebSocket) -> None:
        self._by_user[user_id].add(ws)

    def remove(self, user_id: UUID, ws: WebSocket) -> None:
        sockets = self._by_user.get(user_id)
        if sockets is None:
            return
        sockets.discard(ws)
        if not sockets:
            del self._by_user[user_id]

    async def send_to_user(self, user_id: UUID, payload: dict) -> None:
        # Copy first: other coroutines may add/remove while we're paused at an await.
        for ws in list(self._by_user.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:
                # One dead socket must not stop delivery to the others,
                # or crash the caller (another user's handler, or the listener).
                self.remove(user_id, ws)


manager = ConnectionManager()
