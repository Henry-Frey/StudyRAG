"""Tests for the agent implementations."""
from __future__ import annotations

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base_agent import AgentResponse, BaseAgent, SourceReference
from src.retrieval.vector_store import RetrievedChunk


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_chunks(n: int = 3) -> List[RetrievedChunk]:
    """Create *n* dummy RetrievedChunk objects."""
    return [
        RetrievedChunk(
            text=f"Chunk {i}: Some relevant content about topic {i}.",
            source_file=f"lecture_{i}.pdf",
            page_number=i + 1,
            chunk_index=i,
            lecture_title=f"Lecture {i}",
            score=0.9 - i * 0.1,
            collection_name="test",
        )
        for i in range(n)
    ]


def _make_llm_mock(response_text: str) -> MagicMock:
    """Create a mock LocalLLM that returns *response_text*."""
    from src.llm.local_llm import LLMResponse

    llm = MagicMock()
    llm.generate.return_value = LLMResponse(
        text=response_text,
        tokens_used=100,
        generation_time_ms=50.0,
    )
    return llm


# ---------------------------------------------------------------------------
# BaseAgent helper methods
# ---------------------------------------------------------------------------


class ConcreteAgent(BaseAgent):
    """Minimal concrete implementation for testing base class methods."""

    @property
    def name(self) -> str:
        return "TestAgent"

    @property
    def description(self) -> str:
        return "A test agent"

    @property
    def agent_type(self) -> str:
        return "test"

    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse:
        return AgentResponse(
            answer="test",
            sources=[],
            agent_name=self.name,
            agent_type=self.agent_type,
        )


class TestBaseAgentHelpers:
    """Tests for BaseAgent._format_context and _extract_sources."""

    def setup_method(self) -> None:
        self.agent = ConcreteAgent()

    def test_format_context_single_chunk(self) -> None:
        chunks = _make_chunks(1)
        context = self.agent._format_context(chunks)
        assert "[1]" in context
        assert chunks[0].text in context
        assert chunks[0].lecture_title in context

    def test_format_context_multiple_chunks(self) -> None:
        chunks = _make_chunks(3)
        context = self.agent._format_context(chunks)
        assert "[1]" in context
        assert "[2]" in context
        assert "[3]" in context

    def test_format_context_empty(self) -> None:
        context = self.agent._format_context([])
        assert "keine" in context.lower() or "no" in context.lower() or "nicht" in context.lower()

    def test_extract_sources_deduplicates(self) -> None:
        """Two chunks from the same page should produce one SourceReference."""
        chunks = [
            RetrievedChunk(
                text="text a",
                source_file="file.pdf",
                page_number=1,
                chunk_index=0,
                lecture_title="Lecture",
                score=0.9,
                collection_name="col",
            ),
            RetrievedChunk(
                text="text b",
                source_file="file.pdf",
                page_number=1,
                chunk_index=1,
                lecture_title="Lecture",
                score=0.7,
                collection_name="col",
            ),
        ]
        sources = self.agent._extract_sources(chunks)
        assert len(sources) == 1
        assert sources[0].relevance_score == 0.9  # keeps highest score

    def test_extract_sources_multiple_pages(self) -> None:
        chunks = _make_chunks(3)
        sources = self.agent._extract_sources(chunks)
        assert len(sources) == 3


# ---------------------------------------------------------------------------
# ExplainerAgent tests
# ---------------------------------------------------------------------------


class TestExplainerAgent:
    """Tests for ExplainerAgent."""

    def test_formats_response_correctly(self) -> None:
        """ExplainerAgent should return a valid AgentResponse with expected fields."""
        from src.agents.explainer_agent import ExplainerAgent

        llm = _make_llm_mock("Das ist eine Erklärung des Konzepts.")
        agent = ExplainerAgent(llm=llm)
        chunks = _make_chunks(2)

        response = agent.run("Was ist Machine Learning?", chunks)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "Erklärer"
        assert response.agent_type == "explainer"
        assert "Erklärung" in response.answer
        assert len(response.sources) > 0

    def test_handles_llm_error_gracefully(self) -> None:
        """If the LLM raises an exception, the agent should return an error message."""
        from src.agents.explainer_agent import ExplainerAgent

        llm = MagicMock()
        llm.generate.side_effect = RuntimeError("LLM not loaded")
        agent = ExplainerAgent(llm=llm)
        chunks = _make_chunks(1)

        response = agent.run("query", chunks)
        assert isinstance(response, AgentResponse)
        assert len(response.answer) > 0  # Should contain error message
        assert "Fehler" in response.answer or "fehler" in response.answer.lower()

    def test_agent_name_and_type(self) -> None:
        from src.agents.explainer_agent import ExplainerAgent

        llm = _make_llm_mock("answer")
        agent = ExplainerAgent(llm=llm)
        assert agent.name == "Erklärer"
        assert agent.agent_type == "explainer"


# ---------------------------------------------------------------------------
# QuizAgent tests
# ---------------------------------------------------------------------------


VALID_QUIZ_JSON = json.dumps(
    {
        "questions": [
            {
                "question": "Was ist Overfitting?",
                "options": [
                    "A) Das Modell lernt zu viel",
                    "B) Das Modell passt sich zu stark an Trainingsdaten an",
                    "C) Das Modell hat zu wenige Parameter",
                    "D) Das Modell ignoriert Trainingsdaten",
                ],
                "correct": 1,
                "explanation": "Overfitting bedeutet, dass das Modell Rauschen lernt.",
                "source": "lecture_1.pdf, Seite 5",
            }
        ]
    }
)


class TestQuizAgent:
    """Tests for QuizAgent."""

    def test_parses_valid_json(self) -> None:
        """QuizAgent should populate quiz_data when LLM returns valid JSON."""
        from src.agents.quiz_agent import QuizAgent

        llm = _make_llm_mock(VALID_QUIZ_JSON)
        agent = QuizAgent(llm=llm)
        chunks = _make_chunks(2)

        response = agent.run("Overfitting", chunks)

        assert isinstance(response, AgentResponse)
        assert response.quiz_data is not None
        assert "questions" in response.quiz_data
        assert len(response.quiz_data["questions"]) == 1

    def test_handles_invalid_json_gracefully(self) -> None:
        """QuizAgent should fall back to raw text when JSON parsing fails."""
        from src.agents.quiz_agent import QuizAgent

        llm = _make_llm_mock("This is not JSON at all, just plain text response.")
        agent = QuizAgent(llm=llm)
        chunks = _make_chunks(1)

        response = agent.run("topic", chunks)

        assert isinstance(response, AgentResponse)
        assert response.quiz_data is None
        assert len(response.answer) > 0

    def test_parses_json_with_prose_preamble(self) -> None:
        """QuizAgent should extract JSON even when surrounded by prose text."""
        from src.agents.quiz_agent import QuizAgent

        preamble = "Sure, here are your questions:\n"
        raw = preamble + VALID_QUIZ_JSON + "\nHope this helps!"
        llm = _make_llm_mock(raw)
        agent = QuizAgent(llm=llm)

        response = agent.run("topic", _make_chunks(1))
        assert response.quiz_data is not None

    def test_agent_name_and_type(self) -> None:
        from src.agents.quiz_agent import QuizAgent

        llm = _make_llm_mock("{}")
        agent = QuizAgent(llm=llm)
        assert agent.name == "Quizmaster"
        assert agent.agent_type == "quiz"

    def test_handles_llm_error(self) -> None:
        from src.agents.quiz_agent import QuizAgent

        llm = MagicMock()
        llm.generate.side_effect = RuntimeError("GPU out of memory")
        agent = QuizAgent(llm=llm)

        response = agent.run("topic", _make_chunks(1))
        assert isinstance(response, AgentResponse)
        assert "Fehler" in response.answer


# ---------------------------------------------------------------------------
# ConnectorAgent tests
# ---------------------------------------------------------------------------


class TestConnectorAgent:
    """Tests for ConnectorAgent."""

    def test_connector_runs_successfully(self) -> None:
        """ConnectorAgent should return a valid AgentResponse."""
        from src.agents.connector_agent import ConnectorAgent

        answer_text = "Es gibt Verbindungen zwischen Konzept A aus Vorlesung 1 und Konzept B aus Vorlesung 2."
        llm = _make_llm_mock(answer_text)
        agent = ConnectorAgent(llm=llm)

        # Create chunks from two different lectures
        chunks = [
            RetrievedChunk(
                text="Konzept A: Gradient Descent",
                source_file="ml.pdf",
                page_number=3,
                chunk_index=0,
                lecture_title="Machine Learning",
                score=0.85,
                collection_name="ml",
            ),
            RetrievedChunk(
                text="Konzept B: Optimierung in der Statistik",
                source_file="stats.pdf",
                page_number=7,
                chunk_index=1,
                lecture_title="Statistik",
                score=0.80,
                collection_name="stats",
            ),
        ]

        response = agent.run("Verbindungen zwischen ML und Statistik", chunks)

        assert isinstance(response, AgentResponse)
        assert response.agent_name == "Vernetzer"
        assert response.agent_type == "connector"
        assert answer_text in response.answer
        assert len(response.sources) == 2  # one per unique (file, page) pair

    def test_connector_groups_context_by_lecture(self) -> None:
        """_build_grouped_context should include lecture titles as section headers."""
        from src.agents.connector_agent import ConnectorAgent

        llm = _make_llm_mock("answer")
        agent = ConnectorAgent(llm=llm)

        chunks = [
            RetrievedChunk(
                text="content1",
                source_file="a.pdf",
                page_number=1,
                chunk_index=0,
                lecture_title="Lecture A",
                score=0.9,
                collection_name="col",
            ),
            RetrievedChunk(
                text="content2",
                source_file="b.pdf",
                page_number=2,
                chunk_index=1,
                lecture_title="Lecture B",
                score=0.8,
                collection_name="col",
            ),
        ]

        context = agent._build_grouped_context(chunks)
        assert "=== Lecture A ===" in context
        assert "=== Lecture B ===" in context

    def test_connector_handles_llm_error(self) -> None:
        from src.agents.connector_agent import ConnectorAgent

        llm = MagicMock()
        llm.generate.side_effect = RuntimeError("Timeout")
        agent = ConnectorAgent(llm=llm)

        response = agent.run("query", _make_chunks(2))
        assert isinstance(response, AgentResponse)
        assert "Fehler" in response.answer
