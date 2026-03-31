"""Tests for the retrieval pipeline (vector store and reranker)."""
from __future__ import annotations

from typing import List
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.ingestion.embedder import EmbeddedChunk
from src.retrieval.vector_store import RetrievedChunk


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


DIM = 384  # embedding dimension


def _make_embedding(seed: int = 0) -> List[float]:
    rng = np.random.default_rng(seed)
    vec = rng.random(DIM).astype(np.float32)
    # L2-normalise so cosine distance calculations are well-defined
    vec /= np.linalg.norm(vec) + 1e-9
    return vec.tolist()


def _make_embedded_chunks(n: int = 5) -> List[EmbeddedChunk]:
    return [
        EmbeddedChunk(
            text=f"Chunk text number {i}",
            source_file=f"lecture_{i % 2}.pdf",
            page_number=i + 1,
            chunk_index=i,
            lecture_title=f"Lecture {i % 2}",
            embedding=_make_embedding(i),
        )
        for i in range(n)
    ]


def _make_retrieved_chunks(n: int = 5) -> List[RetrievedChunk]:
    return [
        RetrievedChunk(
            text=f"Retrieved chunk {i}",
            source_file=f"file_{i}.pdf",
            page_number=i + 1,
            chunk_index=i,
            lecture_title=f"Lecture {i}",
            score=float(n - i) / n,  # descending scores
            collection_name="test_col",
        )
        for i in range(n)
    ]


@pytest.fixture
def mock_embedder() -> MagicMock:
    """A mock DocumentEmbedder that returns a fixed query embedding."""
    embedder = MagicMock()
    embedder.embed_query.return_value = _make_embedding(99)
    return embedder


# ---------------------------------------------------------------------------
# ChromaVectorStore tests (using in-memory ChromaDB)
# ---------------------------------------------------------------------------


class TestChromaVectorStore:
    """Integration-style tests using an ephemeral in-memory ChromaDB client."""

    @pytest.fixture
    def in_memory_store(self, mock_embedder: MagicMock, tmp_path):
        """Create a ChromaVectorStore backed by a temporary directory."""
        with patch("chromadb.PersistentClient") as mock_chroma_cls:
            # Use a real ephemeral client instead of mocking deeply
            import chromadb

            real_client = chromadb.EphemeralClient()
            mock_chroma_cls.return_value = real_client

            from src.retrieval.vector_store import ChromaVectorStore

            store = ChromaVectorStore(
                persist_directory=str(tmp_path / "chroma"),
                embedder=mock_embedder,
            )
            yield store

    def test_add_and_query_documents(self, in_memory_store) -> None:
        """Adding chunks and querying should return results."""
        chunks = _make_embedded_chunks(5)
        added = in_memory_store.add_documents(chunks, "test_collection")
        assert added == 5

        results = in_memory_store.query("chunk text", "test_collection", top_k=3)
        assert len(results) <= 3
        assert all(isinstance(r, RetrievedChunk) for r in results)

    def test_query_returns_top_k(self, in_memory_store) -> None:
        """Query should respect the top_k parameter."""
        chunks = _make_embedded_chunks(10)
        in_memory_store.add_documents(chunks, "topk_collection")

        results = in_memory_store.query("text", "topk_collection", top_k=3)
        assert len(results) <= 3

    def test_list_collections_after_add(self, in_memory_store) -> None:
        """After adding documents, the collection should appear in list_collections."""
        chunks = _make_embedded_chunks(3)
        in_memory_store.add_documents(chunks, "my_collection")

        collections = in_memory_store.list_collections()
        assert "my_collection" in collections

    def test_delete_collection(self, in_memory_store) -> None:
        """Deleting a collection should remove it from the list."""
        chunks = _make_embedded_chunks(3)
        in_memory_store.add_documents(chunks, "to_delete")

        success = in_memory_store.delete_collection("to_delete")
        assert success is True
        assert "to_delete" not in in_memory_store.list_collections()

    def test_query_nonexistent_collection_returns_empty(self, in_memory_store) -> None:
        """Querying a collection that doesn't exist should return an empty list."""
        results = in_memory_store.query("anything", "nonexistent", top_k=5)
        assert results == []

    def test_add_empty_chunks_returns_zero(self, in_memory_store) -> None:
        """Adding an empty list should return 0 and not raise."""
        added = in_memory_store.add_documents([], "empty_col")
        assert added == 0

    def test_get_collection_info(self, in_memory_store) -> None:
        """get_collection_info should return name and document_count."""
        chunks = _make_embedded_chunks(4)
        in_memory_store.add_documents(chunks, "info_col")
        info = in_memory_store.get_collection_info("info_col")

        assert info["name"] == "info_col"
        assert info["document_count"] == 4


# ---------------------------------------------------------------------------
# CrossEncoderReranker tests
# ---------------------------------------------------------------------------


class TestCrossEncoderReranker:
    """Tests for CrossEncoderReranker using a mocked CrossEncoder."""

    @patch("sentence_transformers.CrossEncoder")
    def test_reranker_reorders_chunks(self, mock_ce_cls: MagicMock) -> None:
        """Reranker should sort chunks by the cross-encoder's predicted scores."""
        # Assign scores that reverse the original order
        n = 5
        mock_ce = MagicMock()
        # Give the last chunk the highest score
        scores = np.array([float(n - i) for i in range(n)], dtype=np.float32)
        mock_ce.predict.return_value = scores
        mock_ce_cls.return_value = mock_ce

        from src.retrieval.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker(model_name="mock-reranker")
        chunks = _make_retrieved_chunks(n)
        reranked = reranker.rerank("query", chunks, top_k=n)

        # Scores from the reranker: index 0 gets highest raw score (n), then n-1, …
        reranker_scores = [c.reranker_score for c in reranked]
        assert reranker_scores == sorted(reranker_scores, reverse=True)

    @patch("sentence_transformers.CrossEncoder")
    def test_reranker_respects_top_k(self, mock_ce_cls: MagicMock) -> None:
        """Reranker should return at most top_k chunks."""
        mock_ce = MagicMock()
        mock_ce.predict.return_value = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mock_ce_cls.return_value = mock_ce

        from src.retrieval.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker(model_name="mock-reranker")
        chunks = _make_retrieved_chunks(5)
        reranked = reranker.rerank("query", chunks, top_k=3)

        assert len(reranked) == 3

    @patch("sentence_transformers.CrossEncoder")
    def test_reranker_populates_reranker_score(self, mock_ce_cls: MagicMock) -> None:
        """Each reranked chunk should have its reranker_score set."""
        mock_ce = MagicMock()
        mock_ce.predict.return_value = np.array([0.9, 0.5, 0.3])
        mock_ce_cls.return_value = mock_ce

        from src.retrieval.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker(model_name="mock-reranker")
        chunks = _make_retrieved_chunks(3)
        reranked = reranker.rerank("query", chunks, top_k=3)

        assert all(c.reranker_score is not None for c in reranked)

    @patch("sentence_transformers.CrossEncoder")
    def test_reranker_empty_input(self, mock_ce_cls: MagicMock) -> None:
        """Reranking an empty list should return an empty list."""
        mock_ce_cls.return_value = MagicMock()

        from src.retrieval.reranker import CrossEncoderReranker

        reranker = CrossEncoderReranker(model_name="mock-reranker")
        result = reranker.rerank("query", [], top_k=5)
        assert result == []
