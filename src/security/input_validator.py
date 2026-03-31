"""Input validation and prompt-injection detection."""
from __future__ import annotations

import logging
import re
from typing import List

from src.config import get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class InvalidInputError(ValueError):
    """Raised for any malformed or unacceptable input."""


class InputTooLongError(InvalidInputError):
    """Raised when the input exceeds the configured maximum length."""


class PromptInjectionError(InvalidInputError):
    """Raised when a prompt-injection pattern is detected."""


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


class InputValidator:
    """Validates and sanitises user-supplied text.

    Performs three checks in sequence:

    1. Length check – rejects texts longer than ``max_input_length``.
    2. Injection check – rejects texts that match any known injection pattern.
    3. Sanitisation – strips control characters and normalises whitespace.

    Class attribute ``INJECTION_PATTERNS`` lists lower-cased substrings
    that are blocked outright.
    """

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self, text: str) -> str:
        """Validate and sanitise *text*.

        Args:
            text: Raw user input string.

        Returns:
            Sanitised version of *text*.

        Raises:
            InputTooLongError: If *text* exceeds ``max_input_length``.
            PromptInjectionError: If a known injection pattern is detected.
            InvalidInputError: For other validation failures.
        """
        if not isinstance(text, str):
            raise InvalidInputError("Input must be a string.")

        self._check_length(text)
        self._check_injection(text)
        return self._sanitize(text)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _check_length(self, text: str) -> None:
        """Raise :class:`InputTooLongError` if *text* is too long."""
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
        """Raise :class:`PromptInjectionError` if any injection pattern matches."""
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
        """Strip dangerous characters and normalise whitespace.

        - Removes ASCII control characters (0x00-0x08, 0x0B, 0x0C, 0x0E-0x1F, 0x7F).
        - Preserves newline (0x0A) and tab (0x09) as harmless whitespace.
        - Normalises runs of whitespace (excluding newlines) to single spaces.

        Args:
            text: Validated input text.

        Returns:
            Sanitised string.
        """
        # Remove control chars except \t and \n
        sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Collapse multiple spaces/tabs into one space (but keep newlines)
        sanitized = re.sub(r"[^\S\n]+", " ", sanitized)
        return sanitized.strip()
