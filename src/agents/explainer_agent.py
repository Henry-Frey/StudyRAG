"""Explainer agent: explains concepts based on lecture materials."""
from __future__ import annotations

import logging
from typing import List

from src.agents.base_agent import AgentResponse, BaseAgent, SourceReference
from src.llm.local_llm import LocalLLM, PromptTemplateManager
from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class ExplainerAgent(BaseAgent):
    """Explains concepts from lecture materials in German, always citing sources.

    Args:
        llm: Loaded :class:`LocalLLM` instance.
        max_tokens: Maximum tokens for LLM response (default 1024).
    """

    def __init__(self, llm: LocalLLM, max_tokens: int = 1024) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "Erklärer"

    @property
    def description(self) -> str:
        return "Erklärt Konzepte basierend auf den Vorlesungsmaterialien mit Quellenangaben"

    @property
    def agent_type(self) -> str:
        return "explainer"

    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse:
        """Generate an explanation for *query* using *retrieved_chunks*.

        Args:
            query: The student's question.
            retrieved_chunks: Context chunks from the retrieval + reranking step.

        Returns:
            :class:`AgentResponse` with the explanation and cited sources.
        """
        logger.info("ExplainerAgent.run: query='%s', chunks=%d", query, len(retrieved_chunks))

        context = self._format_context(retrieved_chunks)
        prompt = PromptTemplateManager.get_explainer_prompt(query=query, context=context)

        try:
            response = self._llm.generate(prompt=prompt, max_tokens=self._max_tokens)
            answer = response.text.strip()
            logger.info(
                "ExplainerAgent generated response: %d chars, %d tokens",
                len(answer),
                response.tokens_used,
            )
        except Exception as exc:
            logger.error("ExplainerAgent LLM error: %s", exc)
            answer = (
                "Entschuldigung, es ist ein Fehler bei der Antwortgenerierung aufgetreten. "
                f"Details: {exc}"
            )

        sources = self._extract_sources(retrieved_chunks)
        return AgentResponse(
            answer=answer,
            sources=sources,
            agent_name=self.name,
            agent_type=self.agent_type,
        )
