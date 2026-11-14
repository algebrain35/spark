"""
Cross-worker delivery through Redis.

Every worker runs one listener (started from `lifespan`). It receives:
  - "chat:user:{id}" messages (pattern subscription -> type "pmessage")
  - domain events like "match.unmatched" (plain subscription -> type "message")
and delivers each to the sockets THIS worker holds. Listeners only ever call
manager.send_to_user, never publish again, or every worker would re-publish
and users would get one copy per worker.

The listener must run in the web process, next to the sockets. Don't move it
into the background-worker process.
"""

import asyncio
import contextlib
import json
import logging
from uuid import UUID

from app.chat.connections import manager
from app.events import MATCH_UNMATCHED
from app.redis_client import r

log = logging.getLogger("spark.chat")

CHANNEL_PREFIX = "chat:user:"


async def publish_to_user(user_id: UUID, payload: dict) -> None:
    try:
        await r.publish(f"{CHANNEL_PREFIX}{user_id}", json.dumps(payload))
    except Exception:
        # Whatever is being published is already saved, so the recipient gets it on
        # their next catch-up fetch. Only live delivery is lost (same trade-off as
        # match.created). Raising here would make the sender retry and duplicate it.
        log.exception("publish failed for user %s", user_id)


async def listen_forever() -> None:
    """One per worker. Delivers published messages to the sockets this worker holds."""
    while True:
        pubsub = r.pubsub()
        try:
            await pubsub.psubscribe(f"{CHANNEL_PREFIX}*")
            await pubsub.subscribe(MATCH_UNMATCHED)
            async for msg in pubsub.listen():
                try:
                    if msg["type"] == "pmessage":
                        await on_user_message(msg)
                    elif msg["type"] == "message" and msg["channel"] == MATCH_UNMATCHED:
                        await on_unmatched(msg)
                    # anything else is a subscribe confirmation, so ignore it
                except (ValueError, KeyError):     # bad UUID, bad JSON, missing field
                    log.warning("ignoring malformed message on %s", msg.get("channel"))
        except Exception:
            # Redis restarted or the connection dropped. Without this loop the task
            # would die quietly and this worker would never deliver chat again.
            log.exception("chat listener crashed; reconnecting")
        finally:
            await pubsub.aclose()
        await asyncio.sleep(1)


async def on_user_message(msg: dict) -> None:
    user_id = UUID(msg["channel"].removeprefix(CHANNEL_PREFIX))
    await manager.send_to_user(user_id, json.loads(msg["data"]))


async def on_unmatched(msg: dict) -> None:
    event = json.loads(msg["data"])
    closed = {"type": "chat_closed", "match_id": event["match_id"]}
    for uid in (event["user_a"], event["user_b"]):
        await manager.send_to_user(UUID(uid), closed)   # local sockets only


@contextlib.asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(listen_forever())   # runs in the background; startup continues
    yield                                           # the worker serves requests while paused here
    task.cancel()                                   # shutdown: stop the listener cleanly
    with contextlib.suppress(asyncio.CancelledError):
        await task
