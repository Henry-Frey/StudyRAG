from __future__ import annotations

import logging
import re
from typing import List

from src.config import get_settings

logger = logging.getLogger(__name__)


class InvalidInputError(ValueError):
    pass


class InputTooLongError(InvalidInputError):
    pass


class PromptInjectionError(InvalidInputError):
    pass


class InputValidator:
    """Validates user queries before they reach the LLM.

    Runs three passes: length check, injection pattern check, then sanitisation.
    Keeping these separate makes it easy to add new checks later without
    touching the others.
    """

    # Patterns that suggest someone is trying to override the system prompt.
    # Lower-cased for matching — keep this list conservative to avoid false positives.
    INJECTION_PATTERNS: List[str] = [
        "ignore previous instructions",
        "ignore all previous",
        "system prompt",
        "you are now",
        "forget your instructions",
        "disregard",
        "jailbreak",
        "act as",
        "pretend you are",
        "role play as",
        "simulate",
        "bypass",
        "<script>",
        "javascript:",
        "eval(",
        "exec(",
        "import os",
        "import sys",
        "__import__",
        "subprocess",
    ]

    def __init__(self, max_input_length: int | None = None) -> None:
        settings = get_settings()
        self._max_length = max_input_length if max_input_length is not None else settings.max_input_length

    def validate(self, text: str) -> str:
        if not isinstance(text, str):
            raise InvalidInputError("Input must be a string.")

        self._check_length(text)
        self._check_injection(text)
        return self._sanitize(text)

    def _check_length(self, text: str) -> None:
        if len(text) > self._max_length:
            logger.warning(
                "Input rejected: too long (%d chars, max %d)",
                len(text),
                self._max_length,
            )
            raise InputTooLongError(
                f"Input too long: {len(text)} characters (maximum {self._max_length})."
            )

    def _check_injection(self, text: str) -> None:
        lowered = text.lower()
        for pattern in self.INJECTION_PATTERNS:
            if pattern in lowered:
                logger.warning(
                    "Prompt injection blocked: pattern='%s' in input='%.80s'",
                    pattern,
                    text,
                )
                raise PromptInjectionError(
                    f"Input contains a blocked pattern: '{pattern}'."
                )

    @staticmethod
    def _sanitize(text: str) -> str:
        # strip control characters except \t and \n — those are harmless
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # collapse multiple spaces/tabs to one (but preserve newlines)
        sanitized = re.sub(r"[^\S\n]+", " ", sanitized)
        return sanitized.strip()
