"""ChromaDB-based vector store for document retrieval."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

from pydantic import BaseModel

from src.ingestion.embedder import DocumentEmbedder, EmbeddedChunk

logger = logging.getLogger(__name__)


class RetrievedChunk(BaseModel):
    """A chunk returned from a vector store query, enriched with similarity score."""

    text: str
    source_file: str
    page_number: int
    chunk_index: int
    lecture_title: str
    score: float
    collection_name: str
    reranker_score: Optional[float] = None


class ChromaVectorStore:
    """Persistent ChromaDB vector store.

    Supports multiple named collections (one per uploaded document / lecture).

    Args:
        persist_directory: Directory where ChromaDB will persist its data.
        embedder: :class:`DocumentEmbedder` used for query embedding.
    """

    def __init__(self, persist_directory: str, embedder: DocumentEmbedder) -> None:
        import chromadb

        self._embedder = embedder
        self._persist_dir = persist_directory

        # Use PersistentClient so data survives restarts
        self._client = chromadb.PersistentClient(path=persist_directory)
        logger.info("ChromaVectorStore initialised at: %s", persist_directory)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def add_documents(
        self, chunks: List[EmbeddedChunk], collection_name: str
    ) -> int:
        """Add embedded chunks to a named collection.

        The collection is created if it does not yet exist.

        Args:
            chunks: Embedded chunks to store.
            collection_name: Target ChromaDB collection.

        Returns:
            Number of chunks successfully added.
        """
        if not chunks:
            logger.warning("add_documents called with empty chunk list")
            return 0

        collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        ids = [f"{collection_name}_{chunk.chunk_index}" for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]
        metadatas = [
            {
                "source_file": chunk.source_file,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "lecture_title": chunk.lecture_title,
            }
            for chunk in chunks
        ]

        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info(
            "Added %d chunks to collection '%s'",
            len(chunks),
            collection_name,
        )
        return len(chunks)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(
        self,
        query_text: str,
        collection_name: str,
        top_k: int = 10,
    ) -> List[RetrievedChunk]:
        """Query a single collection.

        Args:
            query_text: Natural-language query.
            collection_name: Collection to search in.
            top_k: Maximum number of results to return.

        Returns:
            List of :class:`RetrievedChunk` objects sorted by relevance (best first).
        """
        try:
            collection = self._client.get_collection(name=collection_name)
        except Exception:
            logger.warning("Collection '%s' not found", collection_name)
            return []

        query_embedding = self._embedder.embed_query(query_text)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results, collection_name)

    def query_all_collections(self, query_text: str, top_k: int = 10) -> List[RetrievedChunk]:
        """Query all existing collections and merge results.

        Results are globally sorted by cosine similarity score before truncation
        to *top_k*.

        Args:
            query_text: Natural-language query.
            top_k: Maximum number of results to return across all collections.

        Returns:
            Top-k merged and sorted :class:`RetrievedChunk` objects.
        """
        collections = self.list_collections()
        if not collections:
            logger.info("No collections found for query_all_collections")
            return []

        all_chunks: List[RetrievedChunk] = []
        for col_name in collections:
            chunks = self.query(query_text, col_name, top_k=top_k)
            all_chunks.extend(chunks)

        # Sort by descending score and truncate
        all_chunks.sort(key=lambda c: c.score, reverse=True)
        return all_chunks[:top_k]

    # ------------------------------------------------------------------
    # Management
    # ------------------------------------------------------------------

    def list_collections(self) -> List[str]:
        """Return names of all existing collections."""
        try:
            collections = self._client.list_collections()
            # chromadb >= 0.5 returns Collection objects; older returns strings
            names: List[str] = []
            for col in collections:
                if hasattr(col, "name"):
                    names.append(col.name)
                else:
                    names.append(str(col))
            return names
        except Exception as exc:
            logger.error("Error listing collections: %s", exc)
            return []

    def delete_collection(self, name: str) -> bool:
        """Delete a collection by name.

        Returns:
            ``True`` if deleted successfully, ``False`` otherwise.
        """
        try:
            self._client.delete_collection(name=name)
            logger.info("Deleted collection: %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to delete collection '%s': %s", name, exc)
            return False

    def get_collection_info(self, name: str) -> Dict:
        """Return metadata for a collection.

        Args:
            name: Collection name.

        Returns:
            Dictionary with ``name`` and ``document_count`` keys.
        """
        try:
            collection = self._client.get_collection(name=name)
            return {"name": name, "document_count": collection.count()}
        except Exception as exc:
            logger.error("Error getting info for collection '%s': %s", name, exc)
            return {"name": name, "document_count": 0, "error": str(exc)}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_results(results: Dict, collection_name: str) -> List[RetrievedChunk]:
        """Convert raw ChromaDB query results into :class:`RetrievedChunk` objects."""
        chunks: List[RetrievedChunk] = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to a similarity score in [0, 1]
            score = max(0.0, 1.0 - (dist / 2.0))

            chunks.append(
                RetrievedChunk(
                    text=doc,
                    source_file=meta.get("source_file", ""),
                    page_number=int(meta.get("page_number", 0)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    lecture_title=meta.get("lecture_title", ""),
                    score=score,
                    collection_name=collection_name,
                )
            )

        return chunks
