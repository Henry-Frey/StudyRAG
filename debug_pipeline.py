"""
End-to-end pipeline test. Run from studyrag/:
    python debug_pipeline.py
"""
import os, sys, io
os.chdir(os.path.dirname(os.path.abspath(__file__)))

SEP = "-" * 50

def step(n, name):
    print(f"\n{SEP}\nSTEP {n}: {name}")

def ok(msg):   print(f"  [OK]   {msg}")
def fail(msg): print(f"  [FAIL] {msg}"); sys.exit(1)
def info(msg): print(f"         {msg}")

# ── Config ───────────────────────────────────────────────
step(1, "Config")
from src.config import get_settings
s = get_settings()
ok(f"model_path={s.llm_model_path}")
ok(f"chroma_dir={s.chroma_persist_dir}")

# ── Create minimal test PDF in memory ────────────────────
step(2, "Create test PDF")
try:
    import fitz  # PyMuPDF
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Dies ist ein Test-Dokument. Maschinelles Lernen ist wichtig.")
    pdf_bytes = doc.tobytes()
    doc.close()
    ok(f"Test PDF created ({len(pdf_bytes)} bytes)")
except Exception as e:
    fail(f"Could not create test PDF: {e}")

# ── PDF Parser ───────────────────────────────────────────
step(3, "PDF Parser")
try:
    from src.ingestion.pdf_parser import PDFParser
    parser = PDFParser()
    pages = parser.parse_pdf_bytes(pdf_bytes, "test.pdf")
    ok(f"Parsed {len(pages)} pages")
    for p in pages:
        info(f"  page={p.page_number} text_len={len(p.text)} text='{p.text[:60]}'")
    if not pages:
        fail("No pages extracted — PDF parsing broken")
except Exception as e:
    import traceback; traceback.print_exc()
    fail(f"PDFParser failed: {e}")

# ── Chunker ──────────────────────────────────────────────
step(4, "Chunker")
try:
    from src.ingestion.chunker import TextChunker
    chunker = TextChunker(s.chunk_size, s.chunk_overlap)
    chunks = chunker.chunk(pages)
    ok(f"Created {len(chunks)} chunks")
    for c in chunks[:2]:
        info(f"  chunk={c.chunk_index} text='{c.text[:60]}'")
    if not chunks:
        fail("No chunks produced — chunker broken")
except Exception as e:
    import traceback; traceback.print_exc()
    fail(f"Chunker failed: {e}")

# ── Embedder ─────────────────────────────────────────────
step(5, "Embedder")
try:
    from src.ingestion.embedder import DocumentEmbedder
    embedder = DocumentEmbedder(s.embedding_model)
    embedded = embedder.embed_chunks(chunks)
    ok(f"Embedded {len(embedded)} chunks, dim={len(embedded[0].embedding)}")
    if not embedded:
        fail("No embeddings produced")
except Exception as e:
    import traceback; traceback.print_exc()
    fail(f"Embedder failed: {e}")

# ── ChromaDB Store ───────────────────────────────────────
step(6, "ChromaDB — add documents")
try:
    from src.retrieval.vector_store import ChromaVectorStore
    vs = ChromaVectorStore(s.chroma_persist_dir, embedder)
    col = "debug_test_col"
    added = vs.add_documents(embedded, col)
    ok(f"Added {added} chunks to collection '{col}'")
    cols = vs.list_collections()
    ok(f"list_collections() = {cols}")
    if col not in cols:
        fail(f"Collection '{col}' not visible after add — chromadb persistence broken")
except Exception as e:
    import traceback; traceback.print_exc()
    fail(f"ChromaDB add failed: {e}")

# ── ChromaDB Query ───────────────────────────────────────
step(7, "ChromaDB — query")
try:
    results = vs.query("Maschinelles Lernen", col, top_k=3)
    ok(f"Query returned {len(results)} results")
    for r in results:
        info(f"  score={r.score:.3f} text='{r.text[:60]}'")
    if not results:
        fail("Query returned nothing — retrieval broken despite data being stored")
except Exception as e:
    import traceback; traceback.print_exc()
    fail(f"ChromaDB query failed: {e}")

# ── Cleanup ──────────────────────────────────────────────
step(8, "Cleanup")
vs.delete_collection("debug_test_col")
ok("Test collection deleted")

print(f"\n{SEP}")
print("ALL STEPS PASSED — pipeline is working end-to-end.")
print("If the UI still fails, the issue is in the HTTP layer (upload request not reaching server).")
