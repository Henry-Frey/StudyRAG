from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel

from .pdf_parser import ParsedPage

logger = logging.getLogger(__name__)


class TextChunk(BaseModel):
    text: str
    source_file: str
    page_number: int
    chunk_index: int
    lecture_title: str


class TextChunker:
    """Splits pages into overlapping chunks using LangChain's RecursiveCharacterTextSplitter.

    Recursive splitting tries paragraph breaks first, then sentences, then words —
    so chunks stay semantically coherent rather than cutting mid-sentence.
    """

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50) -> None:
        # langchain_text_splitters is the package name since langchain 0.2
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
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

        logger.info("Chunking complete: %d pages -> %d chunks", len(pages), len(chunks))
        return chunks
