"""
PARTIAL: only the pieces of the swipes service that the chat module depends on.
Merge these into your real swipes service.
"""

import json
from uuid import UUID

from app.events import MATCH_UNMATCHED
from app.redis_client import r


async def get_active_partner(match_id: UUID, user_id: UUID) -> UUID | None:
    """
    Return the other person's id if `user_id` is in this match and it hasn't been
    unmatched. Return None otherwise.

    Chat relies on blocking ALSO unmatching, so this single check covers blocks.
    """
    raise NotImplementedError   # yours to write: one SELECT on `matches`


async def publish_match_unmatched(match_id: UUID, user_a: UUID, user_b: UUID) -> None:
    """
    Call AFTER the unmatch transaction commits (from unmatch, and from block via safety).
    Publishes a plain fact about matches. Turning it into a chat frame is chat's job.
    """
    await r.publish(MATCH_UNMATCHED, json.dumps({
        "match_id": str(match_id),
        "user_a": str(user_a),
        "user_b": str(user_b),
    }))
