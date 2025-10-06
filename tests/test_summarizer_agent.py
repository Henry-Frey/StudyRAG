"""Tests for SummarizerAgent."""
from unittest.mock import MagicMock
from src.agents.summarizer_agent import SummarizerAgent
from src.retrieval.vector_store import RetrievedChunk


def make_chunk(text="hello", score=0.7):
    c = MagicMock(spec=RetrievedChunk)
    c.source_file = "lec.pdf"
    c.page_number = 1
    c.score = score
    c.reranker_score = None
    c.lecture_title = "Lecture 1"
    c.text = text
    return c


def test_summarizer_returns_response():
    agent = SummarizerAgent()
    resp = agent.run("Was ist ein Neuronales Netz?", [make_chunk()])
    assert resp.agent_type == "summarizer"
    assert len(resp.answer) > 0


def test_summarizer_empty_chunks():
    agent = SummarizerAgent()
    resp = agent.run("Test", [])
    assert resp.sources == []
