"""Tests for BaseAgent._sanitize_query."""
from tests.test_base_agent import ConcreteAgent


def test_strips_whitespace():
    agent = ConcreteAgent()
    assert agent._sanitize_query("  hello  ") == "hello"


def test_collapses_spaces():
    agent = ConcreteAgent()
    assert agent._sanitize_query("foo   bar") == "foo bar"


def test_newlines_collapsed():
    agent = ConcreteAgent()
    assert agent._sanitize_query("foo\n\nbar") == "foo bar"
