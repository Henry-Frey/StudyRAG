from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.agents.base_agent import AgentResponse, BaseAgent
from src.llm.local_llm import LocalLLM, PromptTemplateManager
from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class QuizAgent(BaseAgent):
    """Generates MC questions from lecture material.

    The LLM is instructed to return JSON. If that fails we still return the
    raw text so the user gets something useful.
    """

    def __init__(self, llm: LocalLLM, max_tokens: int = 2048) -> None:
        self._llm = llm
        self._max_tokens = max_tokens

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
            logger.warning("QuizAgent: JSON parsing failed, returning raw text")
            return AgentResponse(
                answer=raw_text,
                sources=sources,
                agent_name=self.name,
                agent_type=self.agent_type,
            )

    def _parse_quiz_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Try direct parse first, then look for a JSON block inside the text.

        Models often wrap their JSON in prose, so we scan for the outermost { }.
        """
        try:
            data = json.loads(raw_text)
            if "questions" in data:
                return data
        except json.JSONDecodeError:
            pass

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
        """Render quiz as markdown — used as the plain-text fallback in the response."""
        lines: list[str] = ["## Quiz-Fragen\n"]
        for i, q in enumerate(quiz_data.get("questions", []), start=1):
            lines.append(f"**Frage {i}:** {q.get('question', '')}\n")
            for opt in q.get("options", []):
                lines.append(f"- {opt}")
            correct_idx = q.get("correct", 0)
            options = q.get("options", [])
            correct_text = options[correct_idx] if correct_idx < len(options) else "N/A"
            lines.append(f"\n*Richtige Antwort: {correct_text}*")
            if explanation := q.get("explanation", ""):
                lines.append(f"*Erklärung: {explanation}*")
            if source := q.get("source", ""):
                lines.append(f"*Quelle: {source}*")
            lines.append("")
        return "\n".join(lines)
