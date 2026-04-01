from __future__ import annotations

import logging
from typing import List

from src.retrieval.vector_store import RetrievedChunk

logger = logging.getLogger(__name__)


class CrossEncoderReranker:
    """Re-scores retrieved chunks with a cross-encoder for higher precision.

    The bi-encoder used during retrieval is fast but approximate; the
    cross-encoder reads query + chunk together and gives a better relevance
    signal at the cost of being slower (run on top-k only, not the full index).
    """

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        logger.info("Loading cross-encoder reranker: %s", model_name)
        self._model = CrossEncoder(model_name)
        self._model_name = model_name
        logger.info("Cross-encoder reranker loaded: %s", model_name)

    def rerank(self, query: str, chunks: List[RetrievedChunk], top_k: int = 5) -> List[RetrievedChunk]:
        """Score every (query, chunk) pair and return the top_k by score.

        Note: cross-encoder scores are raw logits (unbounded), not probabilities.
        Don't display them as percentages.
        """
        if not chunks:
            return []

        pairs = [(query, chunk.text) for chunk in chunks]
        logger.debug("Reranking %d chunks for query (len=%d)", len(pairs), len(query))

        try:
            scores: list[float] = self._model.predict(pairs).tolist()
        except Exception as exc:
            logger.error("Cross-encoder prediction failed: %s", exc)
            return chunks[:top_k]

        scored = [
            (float(score), chunk.model_copy(update={"reranker_score": float(score)}))
            for score, chunk in zip(scores, chunks)
        ]
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
        return self._model_name
