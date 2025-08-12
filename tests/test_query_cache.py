"""Tests for in-memory query cache."""
from src.cache.query_cache import get, set, clear


def test_set_and_get():
    clear()
    set("k1", {"answer": "hello"})
    assert get("k1") == {"answer": "hello"}


def test_miss_returns_none():
    clear()
    assert get("missing") is None


def test_clear():
    set("k", {"x": 1})
    clear()
    assert get("k") is None
