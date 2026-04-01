"""
Minimal Streamlit upload debugger.
Run in a second terminal:
    streamlit run debug_streamlit.py --server.port 8502
Then open http://localhost:8502
"""
import streamlit as st
import requests
import fitz

BASE = "http://localhost:8000"
st.title("Upload Debugger")

# ── Step 1: Can Streamlit reach the backend at all? ──────
st.header("1. Backend reachable?")
try:
    r = requests.get(f"{BASE}/api/health", timeout=5)
    st.success(f"Yes — {r.json()}")
except Exception as e:
    st.error(f"No: {e}")
    st.stop()

# ── Step 2: Upload with NO file picker (hardcoded PDF) ───
st.header("2. Upload without file picker")
st.write("Generates a test PDF internally and uploads it directly.")

if st.button("Upload hardcoded test PDF"):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 100), "Maschinelles Lernen Test Dokument.")
    pdf_bytes = doc.tobytes()
    doc.close()

    r = requests.post(
        f"{BASE}/api/upload",
        files={"file": ("hardcoded_test.pdf", pdf_bytes, "application/pdf")},
        data={"collection_name": "debug_no_picker"},
        timeout=60,
    )
    st.write(f"Status: {r.status_code}")
    st.json(r.json())

# ── Step 3: Upload WITH file picker ──────────────────────
st.header("3. Upload with file picker")
st.write("Select a PDF, then click Upload.")

picked = st.file_uploader("Pick a PDF", type=["pdf"])
st.write(f"file_uploader returned: `{picked}`")

if picked:
    # Seek to start before reading — guards against cursor being at EOF
    picked.seek(0)
    file_bytes = picked.read()
    st.write(f"Read {len(file_bytes)} bytes from picker (after seek(0))")
    if file_bytes:
        st.session_state["picked_bytes"] = (picked.name, file_bytes)
        st.success(f"Bytes saved to session_state: {len(file_bytes)} bytes")
    else:
        st.error("read() returned 0 bytes — cursor issue confirmed")

if st.button("Upload picked file"):
    saved = st.session_state.get("picked_bytes")
    if saved:
        name, data = saved
        st.write(f"Sending: {name}, {len(data)} bytes")
        if len(data) == 0:
            st.error("0 bytes in session_state — upload skipped")
        else:
            r = requests.post(
                f"{BASE}/api/upload",
                files={"file": (name, data, "application/pdf")},
                data={"collection_name": "debug_with_picker"},
                timeout=60,
            )
            st.write(f"Status: {r.status_code}")
            st.json(r.json())
    else:
        st.error("No file in session_state — pick a file first")

# ── Step 4: Collections ───────────────────────────────────
st.header("4. Current collections")
r = requests.get(f"{BASE}/api/collections", timeout=5)
st.json(r.json())

# ── Cleanup ───────────────────────────────────────────────
st.header("5. Cleanup")
if st.button("Delete debug collections"):
    for col in ["debug_no_picker", "debug_with_picker"]:
        try:
            requests.delete(f"{BASE}/api/collections/{col}", timeout=5)
        except Exception:
            pass
    st.success("Done")
    st.rerun()
