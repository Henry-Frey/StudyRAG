"""Connector agent: finds cross-connections between lecture concepts."""
from __future__ import annotations

import logging
from typing import List

from src.agents.base_agent import AgentResponse, BaseAgent
from src.llm.local_llm import LocalLLM, PromptTemplateManager
from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class ConnectorAgent(BaseAgent):
    """Identifies connections between concepts across different lecture materials.

    This agent deliberately uses a larger set of retrieved chunks (``top_k * 2``)
    so that it can draw from diverse sources when finding cross-topic connections.

    Args:
        llm: Loaded :class:`LocalLLM` instance.
        max_tokens: Maximum tokens for the LLM response (default 1536).
        top_k_multiplier: Multiplier applied to the caller-supplied chunk count
            to encourage broader retrieval.  Not used directly here (the caller
            should pass more chunks), but documented for clarity.
    """

    def __init__(self, llm: LocalLLM, max_tokens: int = 1536) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "Vernetzer"

    @property
    def description(self) -> str:
        return "Findet Querverbindungen zwischen Konzepten aus verschiedenen Vorlesungen"

    @property
    def agent_type(self) -> str:
        return "connector"

    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse:
        """Find cross-connections for *query* using *retrieved_chunks*.

        The agent groups chunks by lecture title in the context prompt to make
        cross-lecture connections more explicit for the LLM.

        Args:
            query: The student's question about concept relationships.
            retrieved_chunks: Context chunks – ideally from multiple lectures
                (``top_k * 2`` recommended).

        Returns:
            :class:`AgentResponse` describing cross-topic connections.
        """
        logger.info(
            "ConnectorAgent.run: query='%s', chunks=%d", query, len(retrieved_chunks)
        )

        context = self._build_grouped_context(retrieved_chunks)
        prompt = PromptTemplateManager.get_connector_prompt(query=query, context=context)

        try:
            response = self._llm.generate(prompt=prompt, max_tokens=self._max_tokens)
            answer = response.text.strip()
            logger.info(
                "ConnectorAgent generated response: %d chars, %d tokens",
                len(answer),
                response.tokens_used,
            )
        except Exception as exc:
            logger.error("ConnectorAgent LLM error: %s", exc)
            answer = (
                "Entschuldigung, bei der Analyse der Querverbindungen ist ein Fehler aufgetreten. "
                f"Details: {exc}"
            )

        sources = self._extract_sources(retrieved_chunks)
        return AgentResponse(
            answer=answer,
            sources=sources,
            agent_name=self.name,
            agent_type=self.agent_type,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_grouped_context(self, chunks: List[RetrievedChunk]) -> str:
        """Group chunks by lecture title for a more structured context prompt.

        Args:
            chunks: Retrieved chunks (ideally from multiple lectures).

        Returns:
            Multi-section context string with one section per lecture.
        """
        if not chunks:
            return "Keine relevanten Quellen gefunden."

        groups: dict[str, list[RetrievedChunk]] = {}
        for chunk in chunks:
            groups.setdefault(chunk.lecture_title, []).append(chunk)

        sections: list[str] = []
        for lecture_title, lecture_chunks in groups.items():
            sections.append(f"=== {lecture_title} ===")
            for idx, chunk in enumerate(lecture_chunks, start=1):
                sections.append(
                    f"[{idx}] ({chunk.source_file}, Seite {chunk.page_number})"
                )
                sections.append(chunk.text)
                sections.append("")
            sections.append("")

        return "\n".join(sections).strip()
