"""Document embedding utilities using SentenceTransformers."""
from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel

from .chunker import TextChunk

logger = logging.getLogger(__name__)

_DEFAULT_BATCH_SIZE = 32


class EmbeddedChunk(BaseModel):
    """A :class:`TextChunk` extended with its dense embedding vector."""

    text: str
    source_file: str
    page_number: int
    chunk_index: int
    lecture_title: str
    embedding: List[float]

    @classmethod
    def from_chunk(cls, chunk: TextChunk, embedding: List[float]) -> "EmbeddedChunk":
        """Create an :class:`EmbeddedChunk` from a :class:`TextChunk` and its embedding."""
        return cls(
            text=chunk.text,
            source_file=chunk.source_file,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            lecture_title=chunk.lecture_title,
            embedding=embedding,
        )


class DocumentEmbedder:
    """Generates dense vector embeddings for text chunks and queries.

    Args:
        model_name: HuggingFace model identifier (e.g.
            ``"sentence-transformers/all-MiniLM-L6-v2"``).
    """

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        logger.info("Embedding model loaded successfully: %s", model_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_chunks(
        self,
        chunks: List[TextChunk],
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> List[EmbeddedChunk]:
        """Embed a list of text chunks in batches.

        Args:
            chunks: Text chunks to embed.
            batch_size: Number of texts sent to the model at once.

        Returns:
            List of :class:`EmbeddedChunk` objects in the same order as *chunks*.
        """
        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]
        logger.info("Embedding %d chunks (batch_size=%d)…", len(texts), batch_size)

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        embedded: List[EmbeddedChunk] = []
        for chunk, embedding in zip(chunks, embeddings):
            embedded.append(EmbeddedChunk.from_chunk(chunk, embedding.tolist()))

        logger.info("Embedding complete: %d chunks embedded", len(embedded))
        return embedded

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query string.

        Args:
            query: The user's query text.

        Returns:
            Dense vector as a plain Python list of floats.
        """
        logger.debug("Embedding query (length=%d)", len(query))
        vector = self._model.encode(query, convert_to_numpy=True)
        return vector.tolist()

    @property
    def model_name(self) -> str:
        """Name of the underlying SentenceTransformer model."""
        return self._model_name
