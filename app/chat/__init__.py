"""
Chat module. Owns the `messages` table and all WebSocket connections.

Public surface for the rest of the app: `router` and `lifespan`. Nothing else.

Import direction inside this package (never reverse it):
    routes -> handlers -> pubsub -> connections
    protocol can be imported from anywhere
"""

from app.chat.pubsub import lifespan
from app.chat.routes import router

__all__ = ["router", "lifespan"]
