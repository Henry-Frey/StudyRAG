"""
Mimics the server lifespan exactly. Run from studyrag/:
    python debug_server.py
"""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.config import get_settings
s = get_settings()
print(f"[cfg] model_path={s.llm_model_path}")
print(f"[cfg] chroma_dir={s.chroma_persist_dir}")

# 1. Chunker
try:
    from src.ingestion.chunker import TextChunker
    TextChunker(s.chunk_size, s.chunk_overlap)
    print("[OK] chunker")
except Exception as e:
    print(f"[FAIL] chunker: {e}")

# 2. Embedder
embedder = None
try:
    from src.ingestion.embedder import DocumentEmbedder
    embedder = DocumentEmbedder(s.embedding_model)
    print("[OK] embedder")
except Exception as e:
    print(f"[FAIL] embedder: {e}")

# 3. Vector store
vector_store = None
try:
    from src.retrieval.vector_store import ChromaVectorStore
    vector_store = ChromaVectorStore(s.chroma_persist_dir, embedder)
    print(f"[OK] vector_store  collections={vector_store.list_collections()}")
except Exception as e:
    print(f"[FAIL] vector_store: {e}")
    import traceback; traceback.print_exc()

# 4. Reranker
try:
    from src.retrieval.reranker import CrossEncoderReranker
    CrossEncoderReranker(s.reranker_model)
    print("[OK] reranker")
except Exception as e:
    print(f"[FAIL] reranker: {e}")

# 5. LLM
llm = None
try:
    from src.llm.local_llm import LocalLLM
    llm = LocalLLM(s.llm_model_path, s.llm_n_gpu_layers, s.llm_n_ctx, s.llm_temperature)
    print(f"[OK] llm  is_loaded={llm.is_loaded()}")
except Exception as e:
    print(f"[FAIL] llm: {e}")
    import traceback; traceback.print_exc()

print("\nDone.")
