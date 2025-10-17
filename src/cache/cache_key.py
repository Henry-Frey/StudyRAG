"""Helpers for generating consistent cache keys."""
from __future__ import annotations
import hashlib


def make_key(query: str, agent_type: str, collection: str | None) -> str:
    """Return a stable SHA-256 cache key for the given inputs."""
    raw = f"{query.strip().lower()}|{agent_type}|{collection or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()
