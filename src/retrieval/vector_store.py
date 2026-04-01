from __future__ import annotations

import logging
from typing import Dict, List, Optional

from pydantic import BaseModel

from src.ingestion.embedder import DocumentEmbedder, EmbeddedChunk

logger = logging.getLogger(__name__)


class RetrievedChunk(BaseModel):
    text: str
    source_file: str
    page_number: int
    chunk_index: int
    lecture_title: str
    score: float
    collection_name: str
    reranker_score: Optional[float] = None


class ChromaVectorStore:
    """Thin wrapper around ChromaDB's PersistentClient.

    Each uploaded document gets its own named collection so users can query
    a single lecture or all of them at once.
    """

    def __init__(self, persist_directory: str, embedder: Optional[DocumentEmbedder]) -> None:
        import chromadb
        import os

        self._embedder = embedder
        self._persist_dir = persist_directory

        os.makedirs(persist_directory, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_directory)
        logger.info("ChromaVectorStore initialised at: %s", persist_directory)

    def add_documents(self, chunks: List[EmbeddedChunk], collection_name: str) -> int:
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

        logger.info("Added %d chunks to collection '%s'", len(chunks), collection_name)
        return len(chunks)

    def query(self, query_text: str, collection_name: str, top_k: int = 10) -> List[RetrievedChunk]:
        try:
            collection = self._client.get_collection(name=collection_name)
        except Exception:
            logger.warning("Collection '%s' not found", collection_name)
            return []

        if self._embedder is None:
            raise RuntimeError("Embedder not loaded — cannot embed query. Check startup logs.")

        count = collection.count()
        if count == 0:
            logger.warning("Collection '%s' is empty", collection_name)
            return []

        query_embedding = self._embedder.embed_query(query_text)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
        )

        return self._parse_results(results, collection_name)

    def query_all_collections(self, query_text: str, top_k: int = 10) -> List[RetrievedChunk]:
        """Query every collection and merge, keeping the globally top-k results."""
        collections = self.list_collections()
        if not collections:
            logger.info("No collections found for query_all_collections")
            return []

        all_chunks: List[RetrievedChunk] = []
        for col_name in collections:
            all_chunks.extend(self.query(query_text, col_name, top_k=top_k))

        all_chunks.sort(key=lambda c: c.score, reverse=True)
        return all_chunks[:top_k]

    def list_collections(self) -> List[str]:
        try:
            collections = self._client.list_collections()
            # chromadb >= 0.5 returns Collection objects; older returns plain strings
            names: List[str] = []
            for col in collections:
                names.append(col.name if hasattr(col, "name") else str(col))
            return names
        except Exception as exc:
            logger.error("Error listing collections: %s", exc)
            return []

    def delete_collection(self, name: str) -> bool:
        try:
            self._client.delete_collection(name=name)
            logger.info("Deleted collection: %s", name)
            return True
        except Exception as exc:
            logger.error("Failed to delete collection '%s': %s", name, exc)
            return False

    def get_collection_info(self, name: str) -> Dict:
        try:
            collection = self._client.get_collection(name=name)
            return {"name": name, "document_count": collection.count()}
        except Exception as exc:
            logger.error("Error getting info for collection '%s': %s", name, exc)
            return {"name": name, "document_count": 0, "error": str(exc)}

    @staticmethod
    def _parse_results(results: Dict, collection_name: str) -> List[RetrievedChunk]:
        chunks: List[RetrievedChunk] = []

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            # ChromaDB returns cosine distance (0 = identical, 2 = opposite);
            # convert to a [0, 1] similarity score
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
