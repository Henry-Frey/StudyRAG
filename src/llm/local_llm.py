"""llama-cpp-python wrapper for local GGUF inference."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Iterator, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMResponse(BaseModel):
    text: str
    tokens_used: int
    generation_time_ms: float


class LocalLLM:

    def __init__(
        self,
        model_path: str,
        n_gpu_layers: int = -1,
        n_ctx: int = 4096,
        temperature: float = 0.1,
    ) -> None:
        self._model_path = Path(model_path)
        self._n_gpu_layers = n_gpu_layers
        self._n_ctx = n_ctx
        self._default_temperature = temperature
        self._llm: Optional[object] = None

        if not self._model_path.exists():
            logger.warning(
                "LLM model file not found at '%s'. "
                "generate() will raise until the file is available.",
                self._model_path,
            )
        else:
            self._load_model()

    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: Optional[float] = None,
    ) -> LLMResponse:
        self._ensure_loaded()
        temp = temperature if temperature is not None else self._default_temperature

        logger.debug("Generating (max_tokens=%d, temperature=%.2f)", max_tokens, temp)
        t0 = time.perf_counter()

        output = self._llm(  # type: ignore[operator]
            prompt,
            max_tokens=max_tokens,
            temperature=temp,
            echo=False,
        )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        text: str = output["choices"][0]["text"]
        tokens_used: int = output.get("usage", {}).get("total_tokens", 0)

        logger.info("Generation complete: %d tokens in %.0f ms", tokens_used, elapsed_ms)
        return LLMResponse(text=text, tokens_used=tokens_used, generation_time_ms=elapsed_ms)

    def generate_stream(self, prompt: str, max_tokens: int = 1024) -> Iterator[str]:
        self._ensure_loaded()
        logger.debug("Starting streaming generation (max_tokens=%d)", max_tokens)

        for chunk in self._llm(  # type: ignore[operator]
            prompt,
            max_tokens=max_tokens,
            temperature=self._default_temperature,
            stream=True,
            echo=False,
        ):
            if token_text := chunk["choices"][0]["text"]:
                yield token_text

    def is_loaded(self) -> bool:
        return self._llm is not None

    def _load_model(self) -> None:
        try:
            from llama_cpp import Llama  # type: ignore

            logger.info("Loading LLM from '%s'…", self._model_path)
            self._llm = Llama(
                model_path=str(self._model_path),
                n_gpu_layers=self._n_gpu_layers,
                n_ctx=self._n_ctx,
                verbose=False,
            )
            logger.info("LLM loaded successfully")
        except Exception as exc:
            logger.error("Failed to load LLM: %s", exc)
            raise RuntimeError(f"Failed to load LLM model: {exc}") from exc

    def _ensure_loaded(self) -> None:
        if self._llm is None:
            if not self._model_path.exists():
                raise RuntimeError(
                    f"Model file not found: {self._model_path}. "
                    "Download the model and set LLM_MODEL_PATH correctly."
                )
            self._load_model()


class PromptTemplateManager:
    """Builds Mistral-Instruct [INST]…[/INST] prompts for each agent type."""

    _EXPLAINER_SYSTEM = (
        "Du bist ein hilfreicher Lernassistent für Studenten. "
        "Erkläre Konzepte ausschließlich auf Basis der bereitgestellten Quellen. "
        "Wenn die Antwort nicht in den Quellen zu finden ist, sage dies ehrlich. "
        "Zitiere immer die verwendeten Quellen (Dateiname und Seitenzahl). "
        "Antworte auf Deutsch, klar und strukturiert."
    )

    _QUIZ_SYSTEM = (
        "Du bist ein Prüfungsvorbereitungs-Assistent. "
        "Erstelle 3-5 Multiple-Choice-Fragen zu dem angegebenen Thema "
        "ausschließlich basierend auf den bereitgestellten Vorlesungsmaterialien. "
        "Jede Frage hat genau 4 Antwortoptionen (A-D), wobei genau eine korrekt ist. "
        "Antworte NUR mit einem validen JSON-Objekt in folgendem Format:\n"
        '{"questions": [{"question": "...", "options": ["A) ...", "B) ...", "C) ...", "D) ..."], '
        '"correct": 0, "explanation": "...", "source": "..."}]}\n'
        "correct ist der 0-basierte Index der richtigen Antwort."
    )

    _CONNECTOR_SYSTEM = (
        "Du bist ein analytischer Lernassistent, der Querverbindungen zwischen "
        "Konzepten aus verschiedenen Vorlesungen findet. "
        "Analysiere die bereitgestellten Materialien aus verschiedenen Vorlesungen "
        "und zeige auf, welche Konzepte miteinander zusammenhängen, sich ergänzen "
        "oder kontrastieren. "
        "Strukturiere deine Antwort mit klaren Abschnitten für jede Verbindung. "
        "Zitiere die Quellen (Vorlesungstitel und Seite) für jede Verbindung. "
        "Antworte auf Deutsch."
    )

    @classmethod
    def get_explainer_prompt(cls, query: str, context: str) -> str:
        user_message = (
            f"{cls._EXPLAINER_SYSTEM}\n\n"
            f"Kontext aus den Vorlesungsmaterialien:\n{context}\n\n"
            f"Frage: {query}"
        )
        return f"[INST] {user_message} [/INST]"

    @classmethod
    def get_quiz_prompt(cls, topic: str, context: str) -> str:
        user_message = (
            f"{cls._QUIZ_SYSTEM}\n\n"
            f"Vorlesungsmaterial:\n{context}\n\n"
            f"Erstelle Multiple-Choice-Fragen zum Thema: {topic}"
        )
        return f"[INST] {user_message} [/INST]"

    @classmethod
    def get_connector_prompt(cls, query: str, context: str) -> str:
        user_message = (
            f"{cls._CONNECTOR_SYSTEM}\n\n"
            f"Materialien aus verschiedenen Vorlesungen:\n{context}\n\n"
            f"Anfrage: {query}"
        )
        return f"[INST] {user_message} [/INST]"
