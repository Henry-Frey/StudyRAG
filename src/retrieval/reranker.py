"""Cross-encoder reranker for improving retrieval precision."""
from __future__ import annotations

import logging
from typing import List

from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Reranks retrieved chunks using a cross-encoder model.

    A cross-encoder jointly encodes the query and each candidate chunk, giving
    a more accurate relevance signal than the bi-encoder used during retrieval.

    Args:
        model_name: HuggingFace cross-encoder model identifier (e.g.
            ``"cross-encoder/ms-marco-MiniLM-L-6-v2"``).
    """

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        logger.info("Loading cross-encoder reranker: %s", model_name)
        self._model = CrossEncoder(model_name)
        self._model_name = model_name
        logger.info("Cross-encoder reranker loaded: %s", model_name)

    def rerank(
        self,
        query: str,
        chunks: List[RetrievedChunk],
        top_k: int = 5,
    ) -> List[RetrievedChunk]:
        """Rerank *chunks* by their cross-encoder score for *query*.

        Scores each (query, chunk.text) pair using the cross-encoder.  The
        top-*top_k* chunks, sorted by descending score, are returned with their
        ``reranker_score`` field populated.

        Args:
            query: The user's query text.
            chunks: Candidate chunks from the bi-encoder retrieval step.
            top_k: Number of chunks to return after reranking.

        Returns:
            Up to *top_k* :class:`RetrievedChunk` objects sorted by
            ``reranker_score`` (highest first).
        """
        if not chunks:
            return []

        pairs = [(query, chunk.text) for chunk in chunks]
        logger.debug("Reranking %d chunks for query (len=%d)", len(pairs), len(query))

        try:
            scores: list[float] = self._model.predict(pairs).tolist()
        except Exception as exc:
            logger.error("Cross-encoder prediction failed: %s", exc)
            # Fall back to original ordering
            return chunks[:top_k]

        # Attach reranker scores and sort
        scored: list[tuple[float, RetrievedChunk]] = []
        for score, chunk in zip(scores, chunks):
            updated = chunk.model_copy(update={"reranker_score": float(score)})
            scored.append((float(score), updated))

        scored.sort(key=lambda x: x[0], reverse=True)
        reranked = [chunk for _, chunk in scored[:top_k]]

        logger.info(
            "Reranking complete: %d candidates -> %d results (top score=%.4f)",
            len(chunks),
            len(reranked),
            scored[0][0] if scored else 0.0,
        )
        return reranked

    @property
    def model_name(self) -> str:
        """Name of the underlying cross-encoder model."""
        return self._model_name
