"""SummarizerAgent - produces a concise summary of retrieved chunks."""
from __future__ import annotations
from typing import List

from src.agents.base_agent import AgentResponse, BaseAgent
from src.retrieval.vector_store import RetrievedChunk


class SummarizerAgent(BaseAgent):
    """Summarises lecture material into bullet-point notes."""

    @property
    def name(self) -> str:
        return "Zusammenfasser"

    @property
    def description(self) -> str:
        return "Erstellt kompakte Zusammenfassungen aus Vorlesungsmaterialien."

    @property
    def agent_type(self) -> str:
        return "summarizer"

    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse:
        context = self._format_context(retrieved_chunks)
        sources = self._extract_sources(retrieved_chunks)
        summary = f"[Zusammenfassung zu: {query}]\n\n{context[:500]}"
        return AgentResponse(
            answer=summary,
            sources=sources,
            agent_name=self.name,
            agent_type=self.agent_type,
        )
