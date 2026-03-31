"""StudyRAG Streamlit frontend application."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
API_CHAT = f"{BACKEND_URL}/api/chat"
API_UPLOAD = f"{BACKEND_URL}/api/upload"
API_COLLECTIONS = f"{BACKEND_URL}/api/collections"
API_HEALTH = f"{BACKEND_URL}/api/health"
API_DELETE_COLLECTION = f"{BACKEND_URL}/api/collections"

AGENT_OPTIONS: Dict[str, Dict[str, str]] = {
    "Erklärer": {
        "type": "explainer",
        "description": "Erklärt Konzepte aus den Vorlesungsmaterialien mit Quellenangaben.",
    },
    "Quizmaster": {
        "type": "quiz",
        "description": "Generiert Multiple-Choice-Fragen zur Prüfungsvorbereitung.",
    },
    "Vernetzer": {
        "type": "connector",
        "description": "Findet Querverbindungen zwischen Konzepten aus verschiedenen Vorlesungen.",
    },
}

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="StudyRAG",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history: List[Dict[str, Any]] = []
if "selected_collection" not in st.session_state:
    st.session_state.selected_collection: Optional[str] = None
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent: str = "Erklärer"
if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers: Dict[int, int] = {}
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted: bool = False


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _get_health() -> Optional[Dict[str, Any]]:
    """Fetch health status from the backend."""
    try:
        response = requests.get(API_HEALTH, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return None
    except Exception:
        return None


def _get_collections() -> List[Dict[str, Any]]:
    """Fetch available collections from the backend."""
    try:
        response = requests.get(API_COLLECTIONS, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def _upload_pdf(
    file_bytes: bytes,
    filename: str,
    collection_name: str,
) -> Optional[Dict[str, Any]]:
    """Upload a PDF to the backend ingestion endpoint."""
    try:
        files = {"file": (filename, file_bytes, "application/pdf")}
        data = {"collection_name": collection_name}
        response = requests.post(API_UPLOAD, files=files, data=data, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Backend nicht erreichbar. Bitte Backend starten."}
    except requests.exceptions.HTTPError as exc:
        return {"error": f"HTTP {exc.response.status_code}: {exc.response.text}"}
    except Exception as exc:
        return {"error": str(exc)}


def _chat(
    query: str,
    agent_type: str,
    collection_name: Optional[str],
) -> Optional[Dict[str, Any]]:
    """Send a chat request to the backend."""
    payload: Dict[str, Any] = {
        "query": query,
        "agent_type": agent_type,
    }
    if collection_name:
        payload["collection_name"] = collection_name

    try:
        response = requests.post(API_CHAT, json=payload, timeout=180)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Backend nicht erreichbar. Bitte Backend starten."}
    except requests.exceptions.HTTPError as exc:
        try:
            detail = exc.response.json().get("detail", exc.response.text)
        except Exception:
            detail = exc.response.text
        return {"error": f"Fehler: {detail}"}
    except Exception as exc:
        return {"error": str(exc)}


def _render_sources(sources: List[Dict[str, Any]]) -> None:
    """Render source citations in an expandable section."""
    if not sources:
        return

    with st.expander(f"Quellen ({len(sources)})", expanded=False):
        for src in sources:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{src.get('lecture_title', src.get('file_name', 'Unbekannt'))}**")
                st.caption(src.get("file_name", ""))
            with col2:
                st.write(f"Seite {src.get('page_number', '?')}")
            with col3:
                score = src.get("relevance_score", 0)
                st.write(f"Relevanz: {score:.2%}")


def _render_quiz(quiz_data: Dict[str, Any], msg_index: int) -> None:
    """Render interactive Multiple-Choice quiz questions."""
    questions = quiz_data.get("questions", [])
    if not questions:
        return

    st.markdown("### Quiz")
    key_prefix = f"quiz_{msg_index}"

    for q_idx, question in enumerate(questions):
        q_text = question.get("question", "")
        options = question.get("options", [])
        correct_idx = question.get("correct", 0)
        explanation = question.get("explanation", "")
        source = question.get("source", "")

        st.markdown(f"**Frage {q_idx + 1}:** {q_text}")

        answer_key = f"{key_prefix}_q{q_idx}"
        selected = st.radio(
            label=f"Antwort für Frage {q_idx + 1}",
            options=list(range(len(options))),
            format_func=lambda i, opts=options: opts[i] if i < len(opts) else "",
            key=answer_key,
            label_visibility="collapsed",
        )

        if st.session_state.get(f"{answer_key}_submitted"):
            if selected == correct_idx:
                st.success(f"Richtig! {explanation}")
            else:
                correct_text = options[correct_idx] if correct_idx < len(options) else "N/A"
                st.error(f"Falsch. Richtige Antwort: {correct_text}")
                if explanation:
                    st.info(f"Erklärung: {explanation}")
            if source:
                st.caption(f"Quelle: {source}")

        if st.button(f"Überprüfen", key=f"{answer_key}_btn"):
            st.session_state[f"{answer_key}_submitted"] = True
            st.rerun()

        st.divider()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------


with st.sidebar:
    st.title("📚 StudyRAG")
    st.markdown("*KI-Lernassistent mit RAG-Pipeline*")
    st.divider()

    # --- Upload section ---
    st.subheader("Dokumente hochladen")

    uploaded_files = st.file_uploader(
        "PDF-Dateien auswählen",
        type=["pdf"],
        accept_multiple_files=True,
        help="Laden Sie Vorlesungsfolien oder Skripte als PDF hoch.",
    )

    collection_input = st.text_input(
        "Sammlungsname",
        placeholder="z.B. Informatik_WS24",
        help="Name für die Dokumentensammlung (optional, Dateiname wird verwendet wenn leer).",
    )

    if st.button("Hochladen", type="primary", disabled=not uploaded_files):
        if uploaded_files:
            progress_bar = st.progress(0)
            status_placeholder = st.empty()

            for i, uploaded_file in enumerate(uploaded_files):
                col_name = (
                    collection_input.strip()
                    if collection_input.strip()
                    else uploaded_file.name.replace(".pdf", "").replace(" ", "_")
                )

                status_placeholder.info(f"Verarbeite '{uploaded_file.name}'…")
                file_bytes = uploaded_file.read()

                result = _upload_pdf(file_bytes, uploaded_file.name, col_name)
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)

                if result and "error" not in result:
                    st.success(
                        f"'{uploaded_file.name}' verarbeitet: "
                        f"{result.get('chunks_added', 0)} Chunks, "
                        f"{result.get('pages_processed', 0)} Seiten"
                    )
                else:
                    error_msg = result.get("error", "Unbekannter Fehler") if result else "Keine Antwort"
                    st.error(f"Fehler bei '{uploaded_file.name}': {error_msg}")

            status_placeholder.empty()
            st.rerun()

    st.divider()

    # --- Settings section ---
    st.subheader("Einstellungen")

    # Collection selector
    collections = _get_collections()
    collection_names = ["Alle Sammlungen"] + [c["name"] for c in collections]
    selected_col_label = st.selectbox(
        "Sammlung auswählen",
        options=collection_names,
        help="Wählen Sie eine spezifische Sammlung oder alle.",
    )
    st.session_state.selected_collection = (
        None if selected_col_label == "Alle Sammlungen" else selected_col_label
    )

    # Agent selector
    agent_label = st.radio(
        "Agent auswählen",
        options=list(AGENT_OPTIONS.keys()),
        format_func=lambda x: x,
        key="agent_radio",
    )
    st.session_state.selected_agent = agent_label
    st.caption(AGENT_OPTIONS[agent_label]["description"])

    st.divider()

    # --- Status info ---
    st.subheader("Status")
    health = _get_health()

    if health is None:
        st.error("Backend nicht erreichbar")
    else:
        status_color = "green" if health.get("status") == "healthy" else "orange"
        st.markdown(
            f"Status: :{status_color}[{health.get('status', 'unknown').upper()}]"
        )
        st.write(f"LLM geladen: {'Ja' if health.get('llm_loaded') else 'Nein'}")
        st.write(f"GPU verfügbar: {'Ja' if health.get('gpu_available') else 'Nein'}")
        st.write(f"Sammlungen: {health.get('collections_count', 0)}")
        total_docs = sum(c.get("document_count", 0) for c in collections)
        st.write(f"Dokumente gesamt: {total_docs}")

# ---------------------------------------------------------------------------
# Main area: Chat interface
# ---------------------------------------------------------------------------

# Header
col_title, col_clear = st.columns([5, 1])
with col_title:
    active_agent = AGENT_OPTIONS.get(st.session_state.selected_agent, {})
    st.title(f"💬 {st.session_state.selected_agent}")
    st.caption(active_agent.get("description", ""))

with col_clear:
    st.write("")  # vertical spacer
    if st.button("Chat leeren", key="clear_chat"):
        st.session_state.chat_history = []
        st.session_state.quiz_answers = {}
        st.session_state.quiz_submitted = False
        st.rerun()

st.divider()

# Render existing chat history
for msg_index, msg in enumerate(st.session_state.chat_history):
    role = msg.get("role", "user")

    with st.chat_message(role):
        if role == "user":
            st.write(msg["content"])
        else:
            # Assistant message
            agent_name = msg.get("agent_name", "Agent")
            agent_type = msg.get("agent_type", "")
            st.caption(f"Agent: **{agent_name}** ({agent_type})")

            # Render quiz interactively if quiz_data present
            if msg.get("quiz_data"):
                _render_quiz(msg["quiz_data"], msg_index)
            else:
                st.markdown(msg["content"])

            _render_sources(msg.get("sources", []))

            if msg.get("processing_time_ms"):
                st.caption(f"⏱ {msg['processing_time_ms']:.0f} ms")

# Chat input
if prompt := st.chat_input("Stelle eine Frage zu deinen Vorlesungsmaterialien…"):
    # Show user message immediately
    with st.chat_message("user"):
        st.write(prompt)

    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Show spinner while waiting for response
    with st.chat_message("assistant"):
        agent_info = AGENT_OPTIONS.get(st.session_state.selected_agent, {})
        agent_type = agent_info.get("type", "explainer")

        with st.spinner("Antwort wird generiert…"):
            response = _chat(
                query=prompt,
                agent_type=agent_type,
                collection_name=st.session_state.selected_collection,
            )

        if response and "error" not in response:
            agent_name = response.get("agent_name", "Agent")
            resp_agent_type = response.get("agent_type", "")
            st.caption(f"Agent: **{agent_name}** ({resp_agent_type})")

            quiz_data = response.get("quiz_data")
            if quiz_data:
                _render_quiz(quiz_data, len(st.session_state.chat_history))
            else:
                st.markdown(response.get("answer", ""))

            _render_sources(response.get("sources", []))
            processing_time = response.get("processing_time_ms", 0)
            st.caption(f"⏱ {processing_time:.0f} ms")

            # Store in history
            st.session_state.chat_history.append(
                {
                    "role": "assistant",
                    "content": response.get("answer", ""),
                    "agent_name": agent_name,
                    "agent_type": resp_agent_type,
                    "sources": response.get("sources", []),
                    "quiz_data": quiz_data,
                    "processing_time_ms": processing_time,
                }
            )
        else:
            error_msg = response.get("error", "Unbekannter Fehler") if response else "Keine Antwort"
            st.error(f"Fehler: {error_msg}")

            if "Backend nicht erreichbar" in error_msg:
                st.info(
                    "Stellen Sie sicher, dass das Backend läuft:\n"
                    "```\nuvicorn src.main:app --host 0.0.0.0 --port 8000\n```"
                )
