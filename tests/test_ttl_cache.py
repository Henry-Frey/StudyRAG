"""Tests for TTLCache."""
import time
from src.cache.ttl_cache import TTLCache


def test_basic_set_get():
    c = TTLCache(ttl_seconds=60)
    c.set("k", 42)
    assert c.get("k") == 42


def test_expired_returns_none():
    c = TTLCache(ttl_seconds=0)
    c.set("k", 99)
    time.sleep(0.01)
    assert c.get("k") is None


def test_evict_expired():
    c = TTLCache(ttl_seconds=0)
    c.set("a", 1)
    c.set("b", 2)
    time.sleep(0.01)
    removed = c.evict_expired()
    assert removed == 2
