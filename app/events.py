"""
Redis channel names that modules agree on. These are the contract between modules:
publishers and subscribers both import from here, so a typo can't silently break delivery.

Module-private channels (like chat's "chat:user:{id}") stay inside their own module.
"""

MATCH_CREATED = "match.created"        # published by swipes after a match commits
MATCH_UNMATCHED = "match.unmatched"    # published by swipes after unmatch (or block) commits
