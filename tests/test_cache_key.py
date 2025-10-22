"""Tests for cache key generation."""
from src.cache.cache_key import make_key


def test_same_inputs_same_key():
    k1 = make_key("hello", "explainer", "col1")
    k2 = make_key("hello", "explainer", "col1")
    assert k1 == k2


def test_different_inputs_different_keys():
    k1 = make_key("hello", "explainer", None)
    k2 = make_key("world", "explainer", None)
    assert k1 != k2


def test_key_is_hex_string():
    k = make_key("q", "t", None)
    int(k, 16)  # should not raise
