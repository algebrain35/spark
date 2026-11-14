"""Swipes module: other modules call these service functions, never the tables."""

from app.swipes.service import get_active_partner, publish_match_unmatched

__all__ = ["get_active_partner", "publish_match_unmatched"]
