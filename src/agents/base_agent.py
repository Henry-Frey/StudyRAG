"""Abstract base class for all StudyRAG agents."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel

from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class SourceReference(BaseModel):
    """Lightweight reference to a source used in an agent response."""

    file_name: str
    page_number: int
    relevance_score: float
    lecture_title: str


class AgentResponse(BaseModel):
    """Structured response from any StudyRAG agent."""

    answer: str
    sources: List[SourceReference]
    agent_name: str
    agent_type: str
    quiz_data: Optional[dict] = None  # populated only by QuizAgent


class BaseAgent(ABC):
    """Abstract base for all StudyRAG agents.

    Sub-classes must implement :pyattr:`name`, :pyattr:`description`,
    :pyattr:`agent_type`, and :meth:`run`.
    """

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name (in German)."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of the agent's purpose (in German)."""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Machine-readable agent type identifier."""

    @abstractmethod
    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse:
        """Execute the agent for *query* using *retrieved_chunks* as context.

        Args:
            query: The user's question or request.
            retrieved_chunks: Reranked context chunks from the retrieval pipeline.

        Returns:
            :class:`AgentResponse` with the agent's answer and cited sources.
        """

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format retrieved chunks into a numbered context string.

        Each chunk is rendered as::

            [1] Quelle: lecture_title (source_file, Seite page_number)
            chunk text…

        Args:
            chunks: Retrieved and (optionally) reranked chunks.

        Returns:
            Multi-line context string ready for inclusion in a prompt.
        """
        if not chunks:
            return "Keine relevanten Quellen gefunden."

        lines: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            lines.append(
                f"[{idx}] Quelle: {chunk.lecture_title} "
                f"({chunk.source_file}, Seite {chunk.page_number})"
            )
            lines.append(chunk.text)
            lines.append("")  # blank separator

        return "\n".join(lines).strip()

    def _extract_sources(self, chunks: List[RetrievedChunk]) -> List[SourceReference]:
        """Extract unique source references from a list of retrieved chunks.

        Deduplicates by (source_file, page_number), keeping the highest score.

        Args:
            chunks: Retrieved chunks.

        Returns:
            Deduplicated list of :class:`SourceReference` objects.
        """
        seen: dict[tuple[str, int], SourceReference] = {}

        for chunk in chunks:
            key = (chunk.source_file, chunk.page_number)
            score = chunk.reranker_score if chunk.reranker_score is not None else chunk.score
            if key not in seen or score > seen[key].relevance_score:
                seen[key] = SourceReference(
                    file_name=chunk.source_file,
                    page_number=chunk.page_number,
                    relevance_score=round(score, 4),
                    lecture_title=chunk.lecture_title,
                )

        return list(seen.values())
