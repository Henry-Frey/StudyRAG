"""Quiz agent: generates Multiple-Choice questions from lecture materials."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.agents.base_agent import AgentResponse, BaseAgent
from src.llm.local_llm import LocalLLM, PromptTemplateManager
from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class QuizAgent(BaseAgent):
    """Generates 3-5 Multiple-Choice questions in German from lecture materials.

    The LLM is instructed to return valid JSON.  If JSON parsing fails the raw
    text is returned in the ``answer`` field so the user still gets useful output.

    Args:
        llm: Loaded :class:`LocalLLM` instance.
        max_tokens: Maximum tokens for the LLM response (default 2048).
    """

    def __init__(self, llm: LocalLLM, max_tokens: int = 2048) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

    # ------------------------------------------------------------------
    # BaseAgent interface
    # ------------------------------------------------------------------

    @property
    def name(self) -> str:
        return "Quizmaster"

    @property
    def description(self) -> str:
        return "Generiert Multiple-Choice-Fragen zu Themen aus den Vorlesungsmaterialien"

    @property
    def agent_type(self) -> str:
        return "quiz"

    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse:
        """Generate MC questions for topic *query*.

        Args:
            query: The topic or question prompt.
            retrieved_chunks: Context chunks from retrieval + reranking.

        Returns:
            :class:`AgentResponse` with ``quiz_data`` populated when JSON
            parsing succeeds, otherwise raw LLM text in ``answer``.
        """
        logger.info("QuizAgent.run: topic='%s', chunks=%d", query, len(retrieved_chunks))

        context = self._format_context(retrieved_chunks)
        prompt = PromptTemplateManager.get_quiz_prompt(topic=query, context=context)

        try:
            response = self._llm.generate(prompt=prompt, max_tokens=self._max_tokens)
            raw_text = response.text.strip()
            logger.info("QuizAgent LLM response: %d chars", len(raw_text))
        except Exception as exc:
            logger.error("QuizAgent LLM error: %s", exc)
            return AgentResponse(
                answer=f"Fehler bei der Quiz-Generierung: {exc}",
                sources=self._extract_sources(retrieved_chunks),
                agent_name=self.name,
                agent_type=self.agent_type,
            )

        quiz_data: Optional[Dict[str, Any]] = self._parse_quiz_json(raw_text)
        sources = self._extract_sources(retrieved_chunks)

        if quiz_data is not None:
            answer = self._format_quiz_text(quiz_data)
            return AgentResponse(
                answer=answer,
                sources=sources,
                agent_name=self.name,
                agent_type=self.agent_type,
                quiz_data=quiz_data,
            )
        else:
            # Graceful fallback: return raw text
            logger.warning("QuizAgent: JSON parsing failed, returning raw text")
            return AgentResponse(
                answer=raw_text,
                sources=sources,
                agent_name=self.name,
                agent_type=self.agent_type,
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse_quiz_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Attempt to extract and parse JSON from the LLM output.

        Searches for the first ``{`` … ``}`` block in *raw_text* to handle
        models that prepend or append prose to their JSON.

        Args:
            raw_text: Raw LLM output string.

        Returns:
            Parsed quiz dict (with a ``"questions"`` key) or ``None``.
        """
        # Try direct parse first
        try:
            data = json.loads(raw_text)
            if "questions" in data:
                return data
        except json.JSONDecodeError:
            pass

        # Try to extract a JSON block
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(raw_text[start:end])
                if "questions" in data:
                    return data
            except json.JSONDecodeError:
                pass

        logger.debug("Could not parse quiz JSON from: %s", raw_text[:200])
        return None

    @staticmethod
    def _format_quiz_text(quiz_data: Dict[str, Any]) -> str:
        """Render quiz questions as human-readable markdown text.

        Args:
            quiz_data: Parsed quiz dict.

        Returns:
            Markdown-formatted string.
        """
        lines: list[str] = ["## Quiz-Fragen\n"]
        for i, q in enumerate(quiz_data.get("questions", []), start=1):
            lines.append(f"**Frage {i}:** {q.get('question', '')}\n")
            for opt in q.get("options", []):
                lines.append(f"- {opt}")
            correct_idx = q.get("correct", 0)
            options = q.get("options", [])
            correct_text = options[correct_idx] if correct_idx < len(options) else "N/A"
            lines.append(f"\n*Richtige Antwort: {correct_text}*")
            explanation = q.get("explanation", "")
            if explanation:
                lines.append(f"*Erklärung: {explanation}*")
            source = q.get("source", "")
            if source:
                lines.append(f"*Quelle: {source}*")
            lines.append("")
        return "\n".join(lines)
