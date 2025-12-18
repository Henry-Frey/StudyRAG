"""Shared base class and response types for all agents."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel

from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class SourceReference(BaseModel):
    file_name: str
    page_number: int
    relevance_score: float
    lecture_title: str


class AgentResponse(BaseModel):
    answer: str
    sources: List[SourceReference]
    agent_name: str
    agent_type: str
    quiz_data: Optional[dict] = None  # only populated by QuizAgent


class BaseAgent(ABC):

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def agent_type(self) -> str: ...

    @abstractmethod
    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse: ...

    def _format_context(self, chunks: List[RetrievedChunk]) -> str:
        """Format chunks into a numbered context block for prompt injection."""
        if not chunks:
            return "Keine relevanten Quellen gefunden."

        lines: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            lines.append(
                f"[{idx}] Quelle: {chunk.lecture_title} "
                f"({chunk.source_file}, Seite {chunk.page_number})"
            )
            lines.append(chunk.text)
            lines.append("")

        return "\n".join(lines).strip()

    def _extract_sources(self, chunks: List[RetrievedChunk]) -> List[SourceReference]:
        """Deduplicate by (file, page), keeping the highest relevance score."""
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

    def _truncate_context(self, context: str, max_chars: int = 4000) -> str:
        """Truncate context to avoid exceeding model context window."""
        if len(context) <= max_chars:
            return context
        return context[:max_chars] + "\n... [truncated]"

    def _build_prompt_header(self, query: str) -> str:
        """Return a standardised prompt header with the user query."""
        return f"Frage des Studierenden: {query}\n\nRelevante Quellen:\n"

    def _score_threshold_filter(self, chunks, threshold: float = 0.3):
        """Drop chunks below a minimum relevance threshold."""
        return [
            c for c in chunks
            if (c.reranker_score if c.reranker_score is not None else c.score) >= threshold
        ]

    def _sanitize_query(self, query: str) -> str:
        """Strip leading/trailing whitespace and collapse internal whitespace."""
        import re
        return re.sub(r"\s+", " ", query).strip()
