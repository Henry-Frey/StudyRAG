from __future__ import annotations

import logging
from typing import List

from pydantic import BaseModel

from .chunker import TextChunk

logger = logging.getLogger(__name__)

_DEFAULT_BATCH_SIZE = 32


class EmbeddedChunk(BaseModel):
    text: str
    source_file: str
    page_number: int
    chunk_index: int
    lecture_title: str
    embedding: List[float]

    @classmethod
    def from_chunk(cls, chunk: TextChunk, embedding: List[float]) -> "EmbeddedChunk":
        return cls(
            text=chunk.text,
            source_file=chunk.source_file,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            lecture_title=chunk.lecture_title,
            embedding=embedding,
        )


class DocumentEmbedder:

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model: %s", model_name)
        self._model = SentenceTransformer(model_name)
        self._model_name = model_name
        logger.info("Embedding model loaded: %s", model_name)

    def embed_chunks(
        self,
        chunks: List[TextChunk],
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> List[EmbeddedChunk]:
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

        embedded = [
            EmbeddedChunk.from_chunk(chunk, emb.tolist())
            for chunk, emb in zip(chunks, embeddings)
        ]

        logger.info("Embedding complete: %d chunks", len(embedded))
        return embedded

    def embed_query(self, query: str) -> List[float]:
        logger.debug("Embedding query (length=%d)", len(query))
        return self._model.encode(query, convert_to_numpy=True).tolist()

    @property
    def model_name(self) -> str:
        return self._model_name
