"""PDF parsing utilities using PyMuPDF (fitz)."""
from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_MIN_PAGE_TEXT_LENGTH = 10


@dataclass
class ParsedPage:
    """Represents a single parsed page from a PDF document."""

    text: str
    page_number: int
    source_file: str
    lecture_title: str


class PDFParser:
    """Parses PDF files into a list of :class:`ParsedPage` objects.

    Uses PyMuPDF (fitz) for extraction.  Pages with fewer than
    ``_MIN_PAGE_TEXT_LENGTH`` characters of text are silently skipped.
    """

    def parse_pdf(self, file_path: Path) -> list[ParsedPage]:
        """Parse a PDF file from disk.

        Args:
            file_path: Absolute or relative path to the PDF.

        Returns:
            Ordered list of :class:`ParsedPage` instances (empty pages excluded).

        Raises:
            FileNotFoundError: If *file_path* does not exist.
            RuntimeError: If PyMuPDF cannot open the file.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.info("Parsing PDF file: %s", file_path)
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(str(file_path))
            return self._extract_pages(doc, file_path.name)
        except Exception as exc:
            logger.error("Failed to parse PDF %s: %s", file_path, exc)
            raise RuntimeError(f"Failed to parse PDF {file_path}: {exc}") from exc

    def parse_pdf_bytes(self, content: bytes, filename: str) -> list[ParsedPage]:
        """Parse a PDF from raw bytes (e.g. an HTTP upload).

        Args:
            content: Raw PDF bytes.
            filename: Original filename used for title extraction.

        Returns:
            Ordered list of :class:`ParsedPage` instances.

        Raises:
            RuntimeError: If PyMuPDF cannot open the byte stream.
        """
        logger.info("Parsing PDF from bytes: filename=%s, size=%d B", filename, len(content))
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=io.BytesIO(content), filetype="pdf")
            return self._extract_pages(doc, filename)
        except Exception as exc:
            logger.error("Failed to parse PDF bytes (%s): %s", filename, exc)
            raise RuntimeError(f"Failed to parse PDF bytes ({filename}): {exc}") from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_pages(self, doc: object, filename: str) -> list[ParsedPage]:  # noqa: ANN001
        """Extract text from every page of an open fitz document."""
        lecture_title = self._extract_lecture_title(filename)
        pages: list[ParsedPage] = []

        for page_index in range(len(doc)):  # type: ignore[arg-type]
            try:
                page = doc[page_index]  # type: ignore[index]
                text: str = page.get_text()  # type: ignore[attr-defined]
                text = text.strip()

                if len(text) < _MIN_PAGE_TEXT_LENGTH:
                    logger.debug(
                        "Skipping page %d of %s (text too short: %d chars)",
                        page_index + 1,
                        filename,
                        len(text),
                    )
                    continue

                pages.append(
                    ParsedPage(
                        text=text,
                        page_number=page_index + 1,
                        source_file=filename,
                        lecture_title=lecture_title,
                    )
                )
            except Exception as exc:
                logger.warning("Error extracting page %d from %s: %s", page_index + 1, filename, exc)

        logger.info("Extracted %d pages from %s", len(pages), filename)
        return pages

    def _extract_lecture_title(self, filename: str) -> str:
        """Derive a human-readable lecture title from a filename.

        Strips the file extension, then replaces underscores and hyphens with
        spaces, and normalises multiple spaces.

        Examples::

            "Introduction_to_ML.pdf"  -> "Introduction to ML"
            "lecture-03-neural-nets.pdf" -> "lecture 03 neural nets"
        """
        stem = Path(filename).stem
        title = re.sub(r"[_\-]+", " ", stem)
        title = re.sub(r"\s+", " ", title).strip()
        return title
