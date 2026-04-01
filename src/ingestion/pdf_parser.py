"""PDF text extraction via PyMuPDF."""
from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# pages with less text than this are probably cover images or blank slides
_MIN_PAGE_TEXT_LENGTH = 10


@dataclass
class ParsedPage:
    text: str
    page_number: int
    source_file: str
    lecture_title: str


class PDFParser:

    def parse_pdf(self, file_path: Path) -> list[ParsedPage]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")

        logger.info("Parsing PDF file: %s", file_path)
        try:
            import fitz
            doc = fitz.open(str(file_path))
            return self._extract_pages(doc, file_path.name)
        except Exception as exc:
            logger.error("Failed to parse PDF %s: %s", file_path, exc)
            raise RuntimeError(f"Failed to parse PDF {file_path}: {exc}") from exc

    def parse_pdf_bytes(self, content: bytes, filename: str) -> list[ParsedPage]:
        """Used for uploads — avoids writing to disk."""
        logger.info("Parsing PDF from bytes: filename=%s, size=%d B", filename, len(content))
        try:
            import fitz
            doc = fitz.open(stream=io.BytesIO(content), filetype="pdf")
            return self._extract_pages(doc, filename)
        except Exception as exc:
            logger.error("Failed to parse PDF bytes (%s): %s", filename, exc)
            raise RuntimeError(f"Failed to parse PDF bytes ({filename}): {exc}") from exc

    def _extract_pages(self, doc: object, filename: str) -> list[ParsedPage]:
        lecture_title = self._extract_lecture_title(filename)
        pages: list[ParsedPage] = []

        for page_index in range(len(doc)):  # type: ignore[arg-type]
            try:
                page = doc[page_index]  # type: ignore[index]
                text: str = page.get_text().strip()  # type: ignore[attr-defined]

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
        """Turn a filename into a readable title, e.g. 'intro_to_ML.pdf' -> 'intro to ML'."""
        stem = Path(filename).stem
        title = re.sub(r"[_\-]+", " ", stem)
        return re.sub(r"\s+", " ", title).strip()
