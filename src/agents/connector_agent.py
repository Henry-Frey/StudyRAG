from __future__ import annotations

import logging
from typing import List

from src.agents.base_agent import AgentResponse, BaseAgent
from src.llm.local_llm import LocalLLM, PromptTemplateManager
from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class ConnectorAgent(BaseAgent):
    """Finds connections between concepts across multiple lectures.

    Uses top_k * 2 chunks (set by the caller in routes.py) to cast a wider
    net than the other agents.
    """

    def __init__(self, llm: LocalLLM, max_tokens: int = 1536) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

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

    def _build_grouped_context(self, chunks: List[RetrievedChunk]) -> str:
        """Group chunks by lecture so the LLM can see clear source boundaries."""
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
