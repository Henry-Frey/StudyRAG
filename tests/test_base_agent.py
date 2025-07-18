"""Unit tests for BaseAgent helpers."""
import pytest
from unittest.mock import MagicMock, patch
from src.agents.base_agent import BaseAgent, AgentResponse, SourceReference
from src.retrieval.vector_store import RetrievedChunk


class ConcreteAgent(BaseAgent):
    @property
    def name(self): return "test"
    @property
    def description(self): return "test agent"
    @property
    def agent_type(self): return "test"
    def run(self, query, retrieved_chunks): return None


def make_chunk(file, page, score):
    c = MagicMock(spec=RetrievedChunk)
    c.source_file = file
    c.page_number = page
    c.score = score
    c.reranker_score = None
    c.lecture_title = "Lecture"
    c.text = "sample text"
    return c


def test_format_context_empty():
    agent = ConcreteAgent()
    result = agent._format_context([])
    assert "Keine" in result


def test_extract_sources_deduplication():
    agent = ConcreteAgent()
    chunks = [make_chunk("a.pdf", 1, 0.8), make_chunk("a.pdf", 1, 0.9)]
    sources = agent._extract_sources(chunks)
    assert len(sources) == 1
    assert sources[0].relevance_score == 0.9


def test_truncate_context():
    agent = ConcreteAgent()
    long_text = "x" * 5000
    result = agent._truncate_context(long_text, max_chars=4000)
    assert len(result) < 5000
    assert "truncated" in result
