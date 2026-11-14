"""
The one shared Redis client. Swipes publishes events with it; chat publishes and subscribes.

Named redis_client.py (not redis.py) so it can never shadow the `redis` package.
Closed on shutdown in app/main.py.
"""

import redis.asyncio as redis

from app.settings import REDIS_URL

r = redis.from_url(REDIS_URL, decode_responses=True)
