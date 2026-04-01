"""
Posts a real upload request directly to the running server (bypasses Streamlit).
Run with the server already running:
    python debug_http_upload.py
"""
import os, io
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import requests
import fitz  # PyMuPDF

BASE = "http://localhost:8000"

# 1. Health check
print("1. Health check...")
r = requests.get(f"{BASE}/api/health", timeout=5)
print(f"   {r.status_code} {r.json()}")

# 2. Collections before
print("\n2. Collections before upload...")
r = requests.get(f"{BASE}/api/collections", timeout=5)
print(f"   {r.status_code} {r.json()}")

# 3. Create minimal PDF in memory
print("\n3. Creating test PDF...")
doc = fitz.open()
page = doc.new_page()
page.insert_text((50, 100), "Maschinelles Lernen: Neuronale Netze sind wichtig fuer KI.")
pdf_bytes = doc.tobytes()
doc.close()
print(f"   {len(pdf_bytes)} bytes")

# 4. POST upload
print("\n4. Posting to /api/upload...")
r = requests.post(
    f"{BASE}/api/upload",
    files={"file": ("test_lecture.pdf", pdf_bytes, "application/pdf")},
    data={"collection_name": "debug_http_test"},
    timeout=60,
)
print(f"   Status: {r.status_code}")
print(f"   Body:   {r.text}")

# 5. Collections after
print("\n5. Collections after upload...")
r = requests.get(f"{BASE}/api/collections", timeout=5)
print(f"   {r.status_code} {r.json()}")

# 6. Chat query
if r.status_code == 200 and r.json():
    print("\n6. Sending chat query...")
    r = requests.post(
        f"{BASE}/api/chat",
        json={
            "query": "Was sind neuronale Netze?",
            "agent_type": "explainer",
            "collection_name": "debug_http_test",
        },
        timeout=120,
    )
    print(f"   Status: {r.status_code}")
    body = r.json()
    print(f"   Answer: {body.get('answer', body.get('detail', '???'))[:200]}")
    print(f"   Sources: {body.get('sources', [])}")
else:
    print("\n6. Skipped — no collections found after upload.")

# 7. Cleanup
print("\n7. Cleanup...")
r = requests.delete(f"{BASE}/api/collections/debug_http_test", timeout=5)
print(f"   {r.status_code} {r.json()}")
