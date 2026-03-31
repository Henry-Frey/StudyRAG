"""Text chunking utilities using LangChain's RecursiveCharacterTextSplitter."""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel

from .pdf_parser import ParsedPage

logger = logging.getLogger(__name__)


class TextChunk(BaseModel):
    """A single chunk of text derived from a parsed PDF page."""

    text: str
    source_file: str
    page_number: int
    chunk_index: int
    lecture_title: str


class TextChunker:
    """Splits :class:`ParsedPage` objects into overlapping :class:`TextChunk` instances.

    Uses :class:`langchain.text_splitter.RecursiveCharacterTextSplitter` under
    the hood so that natural boundaries (paragraphs, sentences, words) are
    preferred over hard character cuts.

    Args:
        chunk_size: Maximum number of characters per chunk (default 512).
        chunk_overlap: Number of characters shared between adjacent chunks
            (default 50).
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        logger.info(
            "TextChunker initialised: chunk_size=%d, chunk_overlap=%d",
            chunk_size,
            chunk_overlap,
        )

    def chunk(self, pages: List[ParsedPage]) -> List[TextChunk]:
        """Split a list of parsed pages into text chunks.

        Each chunk inherits the metadata (source_file, page_number,
        lecture_title) from its originating page.

        Args:
            pages: Ordered list of :class:`ParsedPage` objects.

        Returns:
            Flat list of :class:`TextChunk` objects across all pages.
        """
        chunks: List[TextChunk] = []
        global_chunk_index = 0

        for page in pages:
            try:
                raw_chunks: list[str] = self._splitter.split_text(page.text)
            except Exception as exc:
                logger.warning(
                    "Failed to split page %d of %s: %s",
                    page.page_number,
                    page.source_file,
                    exc,
                )
                continue

            for raw_chunk in raw_chunks:
                stripped = raw_chunk.strip()
                if not stripped:
                    continue

                chunks.append(
                    TextChunk(
                        text=stripped,
                        source_file=page.source_file,
                        page_number=page.page_number,
                        chunk_index=global_chunk_index,
                        lecture_title=page.lecture_title,
                    )
                )
                global_chunk_index += 1

        logger.info(
            "Chunking complete: %d pages -> %d chunks",
            len(pages),
            len(chunks),
        )
        return chunks
