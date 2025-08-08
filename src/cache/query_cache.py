"""Simple in-memory LRU cache for query results."""
from __future__ import annotations
from typing import Optional


_cache: dict = {}
_MAX_SIZE = 256


def get(key: str) -> Optional[dict]:
    return _cache.get(key)


def set(key: str, value: dict) -> None:
    if len(_cache) >= _MAX_SIZE:
        oldest = next(iter(_cache))
        del _cache[oldest]
    _cache[key] = value


def clear() -> None:
    _cache.clear()
