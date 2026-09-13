# StudyRAG: KI-Lernassistent mit RAG-Pipeline

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

![StudyRAG Interface](visual.png)

Ein vollständig lokaler KI-Lernassistent, der Retrieval-Augmented Generation (RAG) nutzt, um Studierenden beim Verstehen von Vorlesungsmaterialien zu helfen – ohne Cloud-Abhängigkeit und mit vollständiger Datensouveränität.

---

## Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend                       │
│              (Chat UI, Upload, Agent-Auswahl)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP / REST
┌────────────────────────▼────────────────────────────────────────┐
│                    FastAPI Backend                              │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐     │
│  │  /api/upload│  │  /api/chat   │  │  /api/collections   │     │
│  └──────┬──────┘  └──────┬───────┘  └─────────────────────┘     │
│         │                │                                      │
│  ┌──────▼──────┐  ┌──────▼───────────────────────────────────┐  │
│  │  Ingestion  │  │           Retrieval Pipeline             │  │
│  │  Pipeline   │  │  ┌──────────────┐  ┌──────────────────┐  │  │
│  │             │  │  │ ChromaDB     │  │ Cross-Encoder    │  │  │
│  │ PDF Parser  │  │  │ Vector Store │→ │ Reranker         │  │  │
│  │ Chunker     │  │  └──────────────┘  └──────────────────┘  │  │
│  │ Embedder    │  └──────────────────────────┬───────────────┘  │
│  └─────────────┘                             │                  │
│                                    ┌─────────▼───────────┐      │
│                                    │      Agents         │      │
│                                    │  ┌───────────────┐  │      │
│                                    │  │  Erklärer     │  │      │
│                                    │  │  Quizmaster   │  │      │
│                                    │  │  Vernetzer    │  │      │
│                                    │  └───────┬───────┘  │      │
│                                    └──────────┼──────────┘      │
│                                               │                 │
│                                    ┌──────────▼──────────┐      │
│                                    │   Local LLM         │      │
│                                    │  (Mistral 7B GGUF)  │      │
│                                    └─────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Features

- **Erklärer-Agent**: Erklärt Konzepte aus Vorlesungsmaterialien auf Deutsch mit Quellenangaben. Antwortet nur auf Basis indexierter Dokumente und gibt ehrlich zu, wenn Informationen fehlen.
- **Quizmaster-Agent**: Generiert Multiple-Choice-Fragen zur Prüfungsvorbereitung. Gibt valides JSON mit Fragen, Antwortoptionen, richtiger Antwort und Erklärung zurück.
- **Vernetzer-Agent**: Findet Querverbindungen zwischen Konzepten aus verschiedenen Vorlesungen. Ideal für interdisziplinäres Lernen.
- **Vollständig lokale Ausführung**: Keine Daten verlassen den eigenen Server. Kein API-Key erforderlich.
- **Sicherheitsfeatures**: Prompt-Injection-Erkennung, Eingabelängenbegrenzung, Sliding-Window Rate Limiting.
- **GPU-Unterstützung**: CUDA-Beschleunigung via llama-cpp-python (optional, fällt auf CPU zurück).
- **Persistente Vektordatenbank**: ChromaDB speichert Embeddings dauerhaft – kein erneutes Indexieren nach Neustart.

---

## Tech Stack

| Komponente          | Technologie                                      |
|---------------------|--------------------------------------------------|
| LLM                 | Mistral-7B-Instruct-v0.3 (GGUF via llama-cpp)   |
| Embedding-Modell    | sentence-transformers/all-MiniLM-L6-v2           |
| Reranker            | cross-encoder/ms-marco-MiniLM-L-6-v2             |
| Vektordatenbank     | ChromaDB (persistent)                            |
| Backend             | FastAPI + Uvicorn                                |
| Frontend            | Streamlit                                        |
| PDF-Verarbeitung    | PyMuPDF (fitz)                                   |
| Text-Splitting      | LangChain RecursiveCharacterTextSplitter         |
| Containerisierung   | Docker + Docker Compose                          |
| Tests               | pytest                                           |

---

## Quickstart mit Docker

```bash
# 1. Repository klonen
git clone <repo-url> && cd studyrag

# 2. Modell herunterladen
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.3-GGUF \
    mistral-7b-instruct-v0.3.Q4_K_M.gguf --local-dir ./models

# 3. Konfiguration und Start
cp .env.example .env && docker compose up --build
```

Frontend: http://localhost:8501 | API-Docs: http://localhost:8000/docs

---

## Lokale Installation (ohne Docker)

### 1. Repository klonen

```bash
git clone <repo-url>
cd studyrag
```

### 2. Virtuelle Umgebung erstellen

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 3. Abhängigkeiten installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Für GPU-Unterstützung (CUDA):

```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python --force-reinstall --no-cache-dir
```

### 4. Modell herunterladen

```bash
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.3-GGUF \
    mistral-7b-instruct-v0.3.Q4_K_M.gguf \
    --local-dir ./models
```

### 5. Konfiguration

```bash
cp .env.example .env
# .env nach Bedarf anpassen (z.B. GPU-Layer, Chunk-Größe)
```

### 6. Backend starten

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Frontend starten (separates Terminal)

```bash
streamlit run frontend/app.py --server.port 8501
```

---

## Modell-Download

Das System ist für **Mistral-7B-Instruct-v0.3** im GGUF-Format optimiert:

```bash
# Mit huggingface-cli (empfohlen):
huggingface-cli download TheBloke/Mistral-7B-Instruct-v0.3-GGUF \
    mistral-7b-instruct-v0.3.Q4_K_M.gguf \
    --local-dir ./models

# Alternativ mit wget:
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/mistral-7b-instruct-v0.3.Q4_K_M.gguf \
    -P ./models/
```

Das Modell benötigt ca. 4,1 GB Speicher (Q4_K_M Quantisierung). Für bessere Qualität kann Q5_K_M (~5,1 GB) verwendet werden.

---

## API-Dokumentation

Die interaktive API-Dokumentation ist verfügbar unter:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpunkte

| Methode | Pfad                          | Beschreibung                           |
|---------|-------------------------------|----------------------------------------|
| POST    | `/api/upload`                 | PDF hochladen und indexieren           |
| POST    | `/api/chat`                   | Frage an einen Agenten stellen         |
| GET     | `/api/collections`            | Alle Dokumentensammlungen auflisten    |
| DELETE  | `/api/collections/{name}`     | Sammlung löschen                       |
| GET     | `/api/health`                 | Systemstatus abrufen                   |

### Beispiel: Chat-Anfrage

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Was ist der Unterschied zwischen Backpropagation und Gradient Descent?",
    "agent_type": "explainer",
    "collection_name": "machine_learning"
  }'
```

### Beispiel: PDF hochladen

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@./lecture.pdf" \
  -F "collection_name=machine_learning"
```

---

## Architektur-Entscheidungen

### Warum Mistral 7B?
Mistral 7B bietet ein exzellentes Verhältnis zwischen Modellgröße und Qualität. Das Instruct-Format mit `[INST]...[/INST]`-Tags ermöglicht präzise Anweisungsausführung. Die GGUF-Quantisierung ermöglicht den Betrieb auf Consumer-Hardware (8 GB VRAM oder ~12 GB RAM für CPU-Inference).

### Warum ChromaDB?
ChromaDB ist eine leichtgewichtige, einbettungsoptimierte Vektordatenbank mit persistenter Speicherung. Sie unterstützt mehrere Collections (eine pro Vorlesung), was thematisch getrennte Suche oder kollektionsübergreifende Suche ermöglicht. Keine separate Datenbankinfrastruktur erforderlich.

### Warum Cross-Encoder Reranking?
Bi-Encoder-Embeddings (für die initiale Suche) sind schnell, aber weniger präzise als Cross-Encoder, die Query und Dokument gemeinsam kodieren. Der zweistufige Ansatz (Bi-Encoder-Retrieval → Cross-Encoder-Reranking) kombiniert Effizienz mit hoher Präzision: 10 Kandidaten werden abgerufen, die 5 relevantesten werden behalten.

---

## Sicherheit

Das System implementiert mehrere Sicherheitsschichten:

1. **Prompt-Injection-Erkennung**: 20+ bekannte Angriffsmuster werden blockiert (case-insensitiv). Blockierte Anfragen werden geloggt.
2. **Eingabelängenbegrenzung**: Konfigurierbar (Standard: 2000 Zeichen), verhindert Token-Flooding.
3. **Sliding-Window Rate Limiting**: Konfigurierbar pro Minute (Standard: 30 Anfragen), thread-sicher implementiert.
4. **Input-Sanitisierung**: Kontrollzeichen und potenziell gefährliche Zeichenfolgen werden bereinigt.
5. **CORS-Konfiguration**: Im Produktionsbetrieb sollte `allow_origins` auf vertrauenswürdige Domains beschränkt werden.

---

## Übertragbarkeit

StudyRAG ist domänenunabhängig und kann für beliebige PDF-Dokumente eingesetzt werden:

- **Rechtswesen**: Gesetze, Urteile, Kommentare
- **Medizin**: Klinische Leitlinien, Fachliteratur
- **Unternehmensintern**: Handbücher, technische Dokumentation
- **Forschung**: Wissenschaftliche Paper, Berichte

Konfiguration über `.env`: Chunk-Größe, Modellpfad, Top-K-Parameter und Sprachmodell können ohne Codeänderung angepasst werden.

---

## Tests ausführen

```bash
pytest tests/ -v
```

Mit Coverage:

```bash
pip install pytest-cov
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

## Lizenz

MIT License – siehe [LICENSE](LICENSE)

Copyright (c) 2024 StudyRAG Contributors

## CLI Usage

Run queries against a running backend:

    python -m src.cli chat "Was ist ein Transformer?" --agent explainer

Run `python -m src.cli --help` for all options.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed.
All settings can be overridden via environment variables prefixed with `STUDYRAG_`.
<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Elterngeld-Assistent — Prototyp</title>
<style>
/* ===========================================================
   Farbkonzept: Die Oberfläche ist absichtlich fast farblos.
   Das gesamte Farbbudget gehört den Variablen der Rechnung —
   eine Variable hat in Formel, Rechenweg, Regler und Fließtext
   immer dieselbe Farbe.
   =========================================================== */
:root{
  --ground:#edf0f3;
  --card:#ffffff;
  --ink:#131a24;
  --ink2:#5a6673;
  --ink3:#8a949f;
  --rule:#dbe1e7;
  --rule-strong:#b9c3cd;

  --t1:#2f4fcc; --t1bg:#e6eafb;   /* Einkommen vor der Geburt */
  --t2:#0b7466; --t2bg:#dbefeb;   /* Einkommen in Teilzeit */
  --t3:#8a3aa8; --t3bg:#f0e4f7;   /* Ersatzrate */
  --t4:#8a5a00; --t4bg:#f8eeda;   /* Geschwisterbonus */
  --t5:#a83a56; --t5bg:#fae3e9;   /* Mehrlingszuschlag */
  --t6:#4a5765; --t6bg:#e5e9ed;   /* Grenzen und Deckel */

  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --serif:ui-serif,Georgia,"Iowan Old Style","Times New Roman",serif;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--ground);
  color:var(--ink);
  font-family:var(--sans);
  font-size:16px;
  line-height:1.5;
  -webkit-font-smoothing:antialiased;
}
.app{max-width:760px;margin:0 auto;padding:0 16px 120px}

/* ---------- Kopf ---------- */
.top{
  display:flex;align-items:baseline;gap:10px;
  padding:20px 0 14px;border-bottom:1px solid var(--rule);
  position:sticky;top:0;background:var(--ground);z-index:20;
}
.top h1{font-size:17px;font-weight:600;letter-spacing:-0.01em;margin:0}
.top span{font-size:13px;color:var(--ink3)}

/* ---------- Chatverlauf ---------- */
.thread{padding-top:24px;display:flex;flex-direction:column;gap:26px}
.turn-user{align-self:flex-end;max-width:85%}
.turn-user p{
  margin:0;background:#fff;border:1px solid var(--rule);
  border-radius:14px 14px 4px 14px;padding:11px 14px;font-size:15px;
}
.turn-bot{max-width:100%}
.bot-lead{font-size:15px;color:var(--ink);margin:0 0 14px}

/* ---------- Rückfrage-Formular ---------- */
.ask{background:var(--card);border:1px solid var(--rule);border-radius:14px;overflow:hidden}
.ask-head{padding:13px 16px;border-bottom:1px solid var(--rule);font-size:13px;color:var(--ink2)}
.ask-body{padding:4px 16px 16px}
.field{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:12px 0;border-bottom:1px solid var(--rule)}
.field:last-of-type{border-bottom:0}
.field > label{flex:1 1 190px;font-size:14px;min-width:0}
.field .why{display:block;font-size:12px;color:var(--ink3);margin-top:1px}
input[type=number],select{
  font:inherit;font-size:14px;padding:7px 9px;border:1px solid var(--rule-strong);
  border-radius:8px;background:#fff;color:var(--ink);min-width:0;
}
input[type=number]{width:104px;text-align:right;font-variant-numeric:tabular-nums}
.seg{display:flex;border:1px solid var(--rule-strong);border-radius:8px;overflow:hidden}
.seg button{
  font:inherit;font-size:13px;padding:7px 11px;background:#fff;border:0;
  border-right:1px solid var(--rule-strong);cursor:pointer;color:var(--ink2);
}
.seg button:last-child{border-right:0}
.seg button[aria-pressed=true]{background:var(--ink);color:#fff}
.go{
  margin-top:16px;width:100%;font:inherit;font-size:15px;font-weight:500;
  padding:12px;border:0;border-radius:10px;background:var(--ink);color:#fff;cursor:pointer;
}
.go:hover{background:#000}

/* ---------- Rechenblatt ---------- */
.sheet{background:var(--card);border:1px solid var(--rule);border-radius:14px;overflow:hidden}
.sheet section{padding:18px 16px;border-bottom:1px solid var(--rule)}
.sheet section:last-child{border-bottom:0}
.sheet h2{
  font-size:13px;font-weight:600;color:var(--ink2);margin:0 0 12px;letter-spacing:0;
}

/* Ergebnis-Vergleich */
.verdict{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--rule);border-radius:10px;overflow:hidden}
.vcol{background:#fff;padding:14px}
.vcol.win{background:#f7faf9;box-shadow:inset 0 0 0 2px var(--t2)}
.vname{font-size:13px;color:var(--ink2);margin:0 0 6px}
.vbig{font-size:26px;font-weight:600;letter-spacing:-0.02em;font-variant-numeric:tabular-nums;margin:0}
.vsub{font-size:12.5px;color:var(--ink3);margin:2px 0 0}
.vtot{margin:10px 0 0;padding-top:9px;border-top:1px solid var(--rule);font-size:13px;color:var(--ink2)}
.vtot b{display:block;font-size:17px;color:var(--ink);font-variant-numeric:tabular-nums;font-weight:600}
.bars{margin-top:12px}
.bar{display:flex;align-items:center;gap:9px;margin-top:6px;font-size:12px;color:var(--ink2)}
.bar .track{flex:1;height:9px;background:var(--t6bg);border-radius:5px;overflow:hidden}
.bar .fill{height:100%;border-radius:5px;transition:width .28s ease}

/* Formel */
.formula{font-size:15px;line-height:2.25;margin:0 0 6px}
.formula .row{margin-bottom:10px}
.formula .lhs{font-weight:600}
.op{color:var(--ink3);padding:0 2px}
.tok{
  border-radius:6px;padding:3px 7px;white-space:nowrap;font-weight:500;
  box-decoration-break:clone;-webkit-box-decoration-break:clone;
}
.t1{background:var(--t1bg);color:var(--t1)}
.t2{background:var(--t2bg);color:var(--t2)}
.t3{background:var(--t3bg);color:var(--t3)}
.t4{background:var(--t4bg);color:var(--t4)}
.t5{background:var(--t5bg);color:var(--t5)}
.t6{background:var(--t6bg);color:var(--t6)}
.tok .num{font-variant-numeric:tabular-nums;opacity:.72;margin-left:5px;font-weight:600}

/* Rechenweg */
.steps{border-top:1px solid var(--rule);margin-top:6px}
.step{display:flex;gap:12px;align-items:baseline;padding:7px 0;border-bottom:1px solid var(--rule);font-size:14px}
.step .lbl{flex:1;color:var(--ink2)}
.step .val{font-variant-numeric:tabular-nums;font-weight:500;white-space:nowrap}
.step.sum{border-bottom:2px solid var(--ink)}
.step.sum .lbl,.step.sum .val{color:var(--ink);font-weight:600}
.step .note{font-size:12px;color:var(--ink3);display:block}
.dot{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:7px;vertical-align:1px}

/* Regler */
.slider{padding:13px 0;border-bottom:1px solid var(--rule)}
.slider:last-child{border-bottom:0}
.slider .head{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:14px}
.slider .head .v{font-variant-numeric:tabular-nums;font-weight:600}
.slider .hint{font-size:12px;color:var(--ink3);margin-top:2px}
input[type=range]{width:100%;margin:9px 0 0;accent-color:var(--ink);height:22px}
.toggles{display:flex;flex-wrap:wrap;gap:8px;padding-top:13px}
.chip{
  font:inherit;font-size:13px;padding:7px 12px;border-radius:999px;cursor:pointer;
  border:1px solid var(--rule-strong);background:#fff;color:var(--ink2);
}
.chip[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:#fff}
.chip.c4[aria-pressed=true]{background:var(--t4);border-color:var(--t4)}
.chip.c5[aria-pressed=true]{background:var(--t5);border-color:var(--t5)}
.stepper{display:inline-flex;align-items:center;gap:2px;border:1px solid var(--rule-strong);border-radius:999px;padding:2px}
.stepper button{font:inherit;width:28px;height:28px;border:0;background:transparent;cursor:pointer;color:var(--ink2);font-size:16px;border-radius:999px}
.stepper span{font-size:13px;padding:0 6px;font-variant-numeric:tabular-nums}

/* Antworttext */
.answer{font-family:var(--serif);font-size:16.5px;line-height:1.65;max-width:64ch}
.answer p{margin:0 0 13px}
.answer p:last-child{margin-bottom:0}
.answer b{font-weight:600}
.answer .n{font-variant-numeric:tabular-nums;font-weight:600}
.inl{border-radius:4px;padding:1px 4px}
.inl.t1{background:var(--t1bg);color:var(--t1)}
.inl.t2{background:var(--t2bg);color:var(--t2)}
.inl.t3{background:var(--t3bg);color:var(--t3)}
sup a{
  font-family:var(--sans);font-size:10.5px;font-variant-numeric:tabular-nums;
  text-decoration:none;color:var(--ink2);background:var(--t6bg);
  border-radius:3px;padding:1px 4px;margin-left:2px;
}
sup a:hover{background:var(--ink);color:#fff}

/* Quellen */
.src{border:1px solid var(--rule);border-radius:10px;margin-bottom:8px;background:#fff}
.src[open]{border-color:var(--rule-strong)}
.src summary{
  list-style:none;cursor:pointer;padding:11px 13px;display:flex;gap:10px;align-items:baseline;font-size:14px;
}
.src summary::-webkit-details-marker{display:none}
.src .mark{
  font-size:11px;font-variant-numeric:tabular-nums;background:var(--t6bg);color:var(--ink2);
  border-radius:3px;padding:1px 5px;flex:none;
}
.src .ttl{flex:1}
.src .score{font-size:11.5px;color:var(--ink3);font-variant-numeric:tabular-nums;flex:none}
.src .body{padding:0 13px 13px;font-family:var(--serif);font-size:14.5px;line-height:1.6;color:var(--ink2)}
.src .body a{color:var(--t1)}

.caveat{font-size:13px;color:var(--ink2);line-height:1.6;background:#f6f8f9;border-radius:10px;padding:13px}
.caveat b{color:var(--ink)}

/* Eingabezeile */
.composer{
  position:fixed;left:0;right:0;bottom:0;background:linear-gradient(to top,var(--ground) 72%,rgba(237,240,243,0));
  padding:22px 16px 16px;
}
.composer .inner{max-width:760px;margin:0 auto}
.follow{display:flex;gap:8px;overflow-x:auto;padding-bottom:9px;scrollbar-width:none}
.follow::-webkit-scrollbar{display:none}
.follow button{
  font:inherit;font-size:13px;white-space:nowrap;padding:8px 13px;border-radius:999px;
  border:1px solid var(--rule-strong);background:#fff;color:var(--ink2);cursor:pointer;
}
.follow button:hover{border-color:var(--ink);color:var(--ink)}
.box{display:flex;gap:8px;background:#fff;border:1px solid var(--rule-strong);border-radius:12px;padding:6px 6px 6px 14px}
.box input{flex:1;font:inherit;font-size:15px;border:0;outline:none;background:transparent;min-width:0}
.box button{font:inherit;border:0;background:var(--ink);color:#fff;border-radius:8px;padding:8px 14px;cursor:pointer}

.foot{font-size:12px;color:var(--ink3);text-align:center;padding:22px 0 0;line-height:1.6}

.flash{animation:flash .5s ease}
@keyframes flash{0%{background:#fff6d6}100%{background:transparent}}
@media (prefers-reduced-motion:reduce){
  *{animation:none!important;transition:none!important}
}
@media (max-width:430px){
  .verdict{grid-template-columns:1fr}
  .vbig{font-size:23px}
  .formula{font-size:14px;line-height:2.3}
  .answer{font-size:16px}
}
</style>
</head>
<body>

<div class="app">

  <div class="top">
    <h1>Elterngeld-Assistent</h1>
    <span>Prototyp · Stand 2026</span>
  </div>

  <div class="thread">

    <!-- ============ Nutzerfrage ============ -->
    <div class="turn-user">
      <p>Unser Kind kommt im März. Ich will ab dem 5. Lebensmonat wieder 20 Stunden pro Woche arbeiten. Lohnt sich für mich ElterngeldPlus oder lieber Basiselterngeld?</p>
    </div>

    <!-- ============ Rückfrage nach fehlenden Parametern ============ -->
    <div class="turn-bot">
      <p class="bot-lead">Das lässt sich ausrechnen. Für die Höhe brauche ich aber noch ein paar Angaben — ohne sie kann ich nur die Regel nennen, nicht deinen Betrag.</p>

      <div class="ask">
        <div class="ask-head">7 Angaben fehlen</div>
        <div class="ask-body">

          <div class="field">
            <label for="f-brutto">Bruttolohn vor der Geburt
              <span class="why">Durchschnitt der 12 Monate vor dem Mutterschutz</span></label>
            <input type="number" id="f-brutto" value="3800" step="50" min="0">
          </div>

          <div class="field">
            <label>Steuerklasse
              <span class="why">Bestimmt den pauschalen Steuerabzug</span></label>
            <select id="f-klasse">
              <option value="I">I</option>
              <option value="II">II</option>
              <option value="III">III</option>
              <option value="IV" selected>IV</option>
              <option value="V">V</option>
            </select>
          </div>

          <div class="field">
            <label>Krankenversicherung
              <span class="why">Gesetzlich Versicherte haben 9 % Pauschalabzug</span></label>
            <div class="seg" id="f-kv">
              <button data-v="1" aria-pressed="true">gesetzlich</button>
              <button data-v="0" aria-pressed="false">privat</button>
            </div>
          </div>

          <div class="field">
            <label>Kirchensteuerpflichtig
              <span class="why">9 % der Lohnsteuer zusätzlich</span></label>
            <div class="seg" id="f-kirche">
              <button data-v="1" aria-pressed="false">ja</button>
              <button data-v="0" aria-pressed="true">nein</button>
            </div>
          </div>

          <div class="field">
            <label for="f-teilzeit">Bruttolohn in der Teilzeit
              <span class="why">Ab dem 5. Lebensmonat, 20 Std./Woche</span></label>
            <input type="number" id="f-teilzeit" value="1900" step="50" min="0">
          </div>

          <div class="field">
            <label>Weiteres Kind unter 3 Jahren
              <span class="why">Löst den Geschwisterbonus aus</span></label>
            <div class="seg" id="f-geschwister">
              <button data-v="1" aria-pressed="false">ja</button>
              <button data-v="0" aria-pressed="true">nein</button>
            </div>
          </div>

          <div class="field">
            <label>Mehrlingsgeburt
              <span class="why">300 € je weiterem Kind</span></label>
            <div class="seg" id="f-mehrlinge">
              <button data-v="0" aria-pressed="true">Einling</button>
              <button data-v="1" aria-pressed="false">Zwillinge</button>
              <button data-v="2" aria-pressed="false">Drillinge</button>
            </div>
          </div>

          <button class="go" id="go">Berechnen</button>
        </div>
      </div>
    </div>

    <!-- ============ Antwort mit Rechenblatt ============ -->
    <div class="turn-bot" id="result" hidden>
      <p class="bot-lead">Danke. Hier ist deine Rechnung — zieh an den Reglern, um zu sehen, wie sich andere Werte auswirken.</p>

      <div class="sheet">

        <!-- Ergebnis -->
        <section>
          <div class="verdict">
            <div class="vcol" id="col-basis">
              <p class="vname">Basiselterngeld</p>
              <p class="vbig" id="r-basis">–</p>
              <p class="vsub">pro Monat, 12 Monate lang</p>
              <p class="vtot">Summe über den Bezug <b id="r-basis-tot">–</b></p>
            </div>
            <div class="vcol" id="col-plus">
              <p class="vname">ElterngeldPlus</p>
              <p class="vbig" id="r-plus">–</p>
              <p class="vsub">pro Monat, 24 Monate lang</p>
              <p class="vtot">Summe über den Bezug <b id="r-plus-tot">–</b></p>
            </div>
          </div>
          <div class="bars">
            <div class="bar"><span style="width:5.5em">Basis</span><span class="track"><span class="fill" id="bar-basis" style="background:var(--t6)"></span></span></div>
            <div class="bar"><span style="width:5.5em">Plus</span><span class="track"><span class="fill" id="bar-plus" style="background:var(--t2)"></span></span></div>
          </div>
        </section>

        <!-- Formel -->
        <section>
          <h2>Die Formel</h2>
          <div class="formula">
            <div class="row">
              <span class="lhs">Elterngeld-Netto</span> <span class="op">=</span>
              <span class="tok t1">Brutto<span class="num" id="k-brutto"></span></span>
              <span class="op">−</span> <span class="tok t6">Werbungskosten-Pauschale<span class="num">102,50</span></span>
              <span class="op">−</span> <span class="tok t6">Steuern<span class="num" id="k-steuer"></span></span>
              <span class="op">−</span> <span class="tok t6">Sozialabgaben<span class="num" id="k-sv"></span></span>
            </div>
            <div class="row">
              <span class="lhs">Ersatzrate</span> <span class="op">=</span>
              <span class="tok t3">67 %<span class="num">−</span></span>
              <span class="op">0,1 PP je 2 € über</span>
              <span class="tok t6">1.200 €</span>
              <span class="op">→</span>
              <span class="tok t3" id="k-rate">–</span>
            </div>
            <div class="row">
              <span class="lhs">Basiselterngeld</span> <span class="op">=</span>
              <span class="tok t3" id="k-rate2">–</span> <span class="op">×</span> <span class="op">(</span>
              <span class="tok t1">Netto vorher<span class="num" id="k-nv"></span></span>
              <span class="op">−</span>
              <span class="tok t2">Netto in Teilzeit<span class="num" id="k-nn"></span></span>
              <span class="op">)</span>
              <span class="op">+</span> <span class="tok t4">Geschwisterbonus<span class="num" id="k-gb"></span></span>
              <span class="op">+</span> <span class="tok t5">Mehrlingszuschlag<span class="num" id="k-mz"></span></span>
            </div>
            <div class="row">
              <span class="lhs">ElterngeldPlus</span> <span class="op">=</span> <span class="op">min (</span>
              <span class="tok t2">Basisbetrag mit Teilzeit<span class="num" id="k-p1"></span></span>
              <span class="op">,</span>
              <span class="tok t6">½ × Basis ohne Teilzeit<span class="num" id="k-p2"></span></span>
              <span class="op">)</span>
            </div>
          </div>
        </section>

        <!-- Rechenweg -->
        <section>
          <h2>Dein Rechenweg</h2>
          <div class="steps" id="steps"></div>
        </section>

        <!-- Regler -->
        <section>
          <h2>Werte ändern</h2>

          <div class="slider">
            <div class="head">
              <span><span class="dot" style="background:var(--t1)"></span>Bruttolohn vor der Geburt</span>
              <span class="v" id="s1-v">–</span>
            </div>
            <input type="range" id="s1" min="0" max="9000" step="50">
            <div class="hint" id="s1-h"></div>
          </div>

          <div class="slider">
            <div class="head">
              <span><span class="dot" style="background:var(--t2)"></span>Bruttolohn in der Teilzeit</span>
              <span class="v" id="s2-v">–</span>
            </div>
            <input type="range" id="s2" min="0" max="6000" step="50">
            <div class="hint" id="s2-h"></div>
          </div>

          <div class="slider">
            <div class="head">
              <span><span class="dot" style="background:var(--t6)"></span>Wochenstunden in der Teilzeit</span>
              <span class="v" id="s3-v">–</span>
            </div>
            <input type="range" id="s3" min="0" max="40" step="1">
            <div class="hint" id="s3-h"></div>
          </div>

          <div class="toggles">
            <button class="chip c4" id="t-geschwister" aria-pressed="false">Geschwisterbonus</button>
            <span class="stepper">
              <button id="m-minus" aria-label="weniger Mehrlingskinder">−</button>
              <span id="m-val">Einling</span>
              <button id="m-plus" aria-label="mehr Mehrlingskinder">+</button>
            </span>
          </div>
        </section>

        <!-- Antworttext -->
        <section>
          <h2>Die Antwort</h2>
          <div class="answer" id="answer"></div>
        </section>

        <!-- Quellen -->
        <section>
          <h2>Grundlage</h2>
          <div id="sources"></div>
          <div class="caveat">
            <b>Schätzung, keine Rechtsberatung.</b> Steuern werden hier vereinfacht nach § 32a EStG geschätzt; die Elterngeldstelle rechnet mit dem amtlichen Programmablaufplan, weshalb dein Bescheid um einige Euro abweichen kann. Mutterschaftsgeld wird in den Lebensmonaten 1 und 2 voll angerechnet und ist hier nicht abgebildet.
          </div>
        </section>

      </div>
    </div>

  </div>

  <p class="foot">Prototyp zur Ansicht der Interaktion — die Antworten sind hinterlegt, die Rechnung läuft live.</p>
</div>

<!-- Eingabezeile -->
<div class="composer">
  <div class="inner">
    <div class="follow" id="follow" hidden>
      <button data-act="h30">Was wäre bei 30 Stunden?</button>
      <button data-act="h0">Und wenn ich gar nicht arbeite?</button>
      <button data-act="rich">Mit 6.500 € Brutto vorher?</button>
    </div>
    <div class="box">
      <input placeholder="Frage stellen …" aria-label="Frage stellen">
      <button>Senden</button>
    </div>
  </div>
</div>

<script>
"use strict";

/* ============================================================
   KONSTANTEN — jährlich prüfen.
   Rechtsgrundlage: BEEG, EStG. Die Tarif- und Beitragswerte
   müssen produktiv aus dem BMF-Programmablaufplan bzw. der
   Sozialversicherungs-Rechengrößenverordnung gezogen werden.
   ============================================================ */
const K = {
  jahr: 2026,

  // § 2c BEEG — Abzug vom Bruttolohn vor der Besteuerung
  werbungskostenJahr: 1230,          // Arbeitnehmer-Pauschbetrag
  sonderausgabenJahr: 36,

  // Rechengrößen Sozialversicherung (Monatswerte)
  bbgKv: 5812.50,
  bbgRv: 8450.00,

  // § 2f BEEG — pauschale Sozialabgaben auf das Brutto
  svKvPv: 0.09,
  svRv:   0.10,
  svAlv:  0.02,

  // Tatsächliche Arbeitnehmeranteile, nur für die Vorsorgepauschale
  anRv: 0.093, anKv: 0.0865, anPv: 0.018, anPvKinderlos: 0.024,

  // § 2 BEEG
  nettoDeckel: 2770,                 // Einkommen darüber bleibt unberücksichtigt
  basisMax: 1800, basisMin: 300,
  plusMax: 900,  plusMin: 150,

  // § 2a BEEG
  geschwisterSatz: 0.10, geschwisterMinBasis: 75, geschwisterMinPlus: 37.50,
  mehrlingBasis: 300, mehrlingPlus: 150,

  // § 32a EStG — Tarif 2026
  grundfreibetrag: 12348,
  soliFreigrenze: 19950,
  entlastungAlleinerziehend: 4260,
  kirchensteuerSatz: 0.09,

  // § 1 Abs. 8 BEEG — Geburten ab 1.4.2025
  einkommensgrenze: 175000,

  // § 1 Abs. 6 BEEG
  maxWochenstunden: 32,
  basismonate: 12
};

/* ---------- § 32a EStG, Tarifformel ---------- */
function estTarif(zvE){
  const x = Math.floor(zvE);
  if (x <= 12348) return 0;
  if (x <= 17799){ const y = (x - 12348) / 10000; return (914.51 * y + 1400) * y; }
  if (x <= 69878){ const z = (x - 17799) / 10000; return (173.10 * z + 2397) * z + 1034.87; }
  if (x <= 277825) return 0.42 * x - 10884.88;
  return 0.45 * x - 19219.63;
}

function vorsorgepauschale(bruttoJahr, gesetzlich, kinderlos){
  const rv = Math.min(bruttoJahr, K.bbgRv * 12) * K.anRv;
  const kvBasis = Math.min(bruttoJahr, K.bbgKv * 12);
  const pv = kinderlos ? K.anPvKinderlos : K.anPv;
  const kv = gesetzlich ? kvBasis * (K.anKv + pv) : bruttoJahr * 0.07;
  return rv + kv;
}

/* ---------- §§ 2e, 2f BEEG — Abzüge ---------- */
function steuernMonat(bruttoMonat, p){
  const bruttoJahr = bruttoMonat * 12;
  let zvE = bruttoJahr - K.werbungskostenJahr - K.sonderausgabenJahr
          - vorsorgepauschale(bruttoJahr, p.gesetzlich, false);
  if (p.klasse === "II") zvE -= K.entlastungAlleinerziehend;
  zvE = Math.max(0, zvE);

  let lst;
  if (p.klasse === "III")      lst = 2 * estTarif(zvE / 2);
  else if (p.klasse === "V")   lst = estTarif(zvE + K.grundfreibetrag);   // vereinfacht
  else                         lst = estTarif(zvE);

  const freigrenze = p.klasse === "III" ? K.soliFreigrenze * 2 : K.soliFreigrenze;
  const soli = lst > freigrenze ? Math.min(0.055 * lst, 0.119 * (lst - freigrenze)) : 0;
  const kist = p.kirche ? K.kirchensteuerSatz * lst : 0;

  return { lst: lst / 12, soli: soli / 12, kist: kist / 12, summe: (lst + soli + kist) / 12 };
}

function svMonat(bruttoMonat, gesetzlich){
  const kv  = gesetzlich ? Math.min(bruttoMonat, K.bbgKv) * K.svKvPv : 0;
  const rv  = Math.min(bruttoMonat, K.bbgRv) * K.svRv;
  const alv = Math.min(bruttoMonat, K.bbgRv) * K.svAlv;
  return { kv, rv, alv, summe: kv + rv + alv };
}

function elterngeldNetto(bruttoMonat, p){
  if (bruttoMonat <= 0) return { brutto:0, wk:0, steuer:{summe:0}, sv:{summe:0}, netto:0 };
  const wk = K.werbungskostenJahr / 12;
  const steuer = steuernMonat(bruttoMonat, p);
  const sv = svMonat(bruttoMonat, p.gesetzlich);
  const netto = Math.max(0, bruttoMonat - wk - steuer.summe - sv.summe);
  return { brutto: bruttoMonat, wk, steuer, sv, netto };
}

/* ---------- § 2 Abs. 2 BEEG — gleitende Ersatzrate ---------- */
function ersatzrate(nettoVor){
  const n = Math.min(nettoVor, K.nettoDeckel);
  if (n < 1000)  return Math.min(1.00, 0.67 + Math.floor((1000 - n) / 2) * 0.001);
  if (n <= 1200) return 0.67;
  return Math.max(0.65, 0.67 - Math.floor((n - 1200) / 2) * 0.001);
}

const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));

/* ---------- Gesamtrechnung ---------- */
function rechne(p){
  const vor  = elterngeldNetto(p.bruttoVor, p);
  const nach = elterngeldNetto(p.bruttoNach, p);

  const nettoVorGedeckelt = Math.min(vor.netto, K.nettoDeckel);
  const nettoNach = Math.min(nach.netto, K.nettoDeckel);
  const differenz = Math.max(0, nettoVorGedeckelt - nettoNach);
  const rate = ersatzrate(vor.netto);

  const basisOhneArbeit = clamp(rate * nettoVorGedeckelt, K.basisMin, K.basisMax);
  const basisRoh        = clamp(rate * differenz,          K.basisMin, K.basisMax);

  const plusDeckel = basisOhneArbeit / 2;
  const plusRoh    = clamp(Math.min(rate * differenz, plusDeckel), K.plusMin, K.plusMax);

  const boni = (betrag, plus) => {
    const gb = p.geschwister
      ? Math.max(betrag * K.geschwisterSatz, plus ? K.geschwisterMinPlus : K.geschwisterMinBasis) : 0;
    const mz = p.mehrlinge * (plus ? K.mehrlingPlus : K.mehrlingBasis);
    return { gb, mz, gesamt: betrag + gb + mz };
  };

  const b = boni(basisRoh, false);
  const pl = boni(plusRoh, true);

  return {
    vor, nach, nettoVorGedeckelt, nettoNach, differenz, rate,
    basisOhneArbeit, basisRoh, plusDeckel, plusRoh,
    basis: { ...b, monat: b.gesamt, monate: K.basismonate, summe: b.gesamt * K.basismonate },
    plus:  { ...pl, monat: pl.gesamt, monate: K.basismonate * 2, summe: pl.gesamt * K.basismonate * 2 },
    gedeckelt: vor.netto > K.nettoDeckel,
    mindestbetrag: basisRoh <= K.basisMin + 0.001 && rate * differenz < K.basisMin
  };
}

/* ---------- Formatierung ---------- */
const eur = n => n.toLocaleString("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " €";
const eur0 = n => Math.round(n).toLocaleString("de-DE") + " €";
const pct = n => (n * 100).toLocaleString("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 }) + " %";

/* ============================================================
   Zustand und Oberfläche
   ============================================================ */
const state = {
  bruttoVor: 3800, bruttoNach: 1900, stunden: 20,
  klasse: "IV", gesetzlich: true, kirche: false,
  geschwister: false, mehrlinge: 0
};

const $ = id => document.getElementById(id);

function segHandler(el, cb){
  el.addEventListener("click", e => {
    const btn = e.target.closest("button"); if (!btn) return;
    [...el.querySelectorAll("button")].forEach(b => b.setAttribute("aria-pressed", String(b === btn)));
    cb(Number(btn.dataset.v));
  });
}
segHandler($("f-kv"),          v => state.gesetzlich = !!v);
segHandler($("f-kirche"),      v => state.kirche = !!v);
segHandler($("f-geschwister"), v => state.geschwister = !!v);
segHandler($("f-mehrlinge"),   v => state.mehrlinge = v);
$("f-klasse").addEventListener("change", e => state.klasse = e.target.value);

$("go").addEventListener("click", () => {
  state.bruttoVor  = Math.max(0, Number($("f-brutto").value) || 0);
  state.bruttoNach = Math.max(0, Number($("f-teilzeit").value) || 0);
  $("s1").value = state.bruttoVor;
  $("s2").value = state.bruttoNach;
  $("s3").value = state.stunden;
  $("t-geschwister").setAttribute("aria-pressed", String(state.geschwister));
  $("result").hidden = false;
  $("follow").hidden = false;
  render();
  $("result").scrollIntoView({ behavior: "smooth", block: "start" });
});

/* ---------- Regler ---------- */
$("s1").addEventListener("input", e => { state.bruttoVor  = Number(e.target.value); render(); });
$("s2").addEventListener("input", e => { state.bruttoNach = Number(e.target.value); render(); });
$("s3").addEventListener("input", e => { state.stunden    = Number(e.target.value); render(); });
$("t-geschwister").addEventListener("click", e => {
  state.geschwister = !state.geschwister;
  e.currentTarget.setAttribute("aria-pressed", String(state.geschwister));
  render();
});
const mehrlingLabel = ["Einling", "Zwillinge", "Drillinge", "Vierlinge"];
$("m-minus").addEventListener("click", () => { state.mehrlinge = Math.max(0, state.mehrlinge - 1); render(); });
$("m-plus").addEventListener("click",  () => { state.mehrlinge = Math.min(3, state.mehrlinge + 1); render(); });

$("follow").addEventListener("click", e => {
  const btn = e.target.closest("button"); if (!btn) return;
  if (btn.dataset.act === "h30"){ state.stunden = 30; state.bruttoNach = Math.round(state.bruttoVor * 0.75 / 50) * 50; }
  if (btn.dataset.act === "h0"){  state.stunden = 0;  state.bruttoNach = 0; }
  if (btn.dataset.act === "rich"){ state.bruttoVor = 6500; }
  $("s1").value = state.bruttoVor; $("s2").value = state.bruttoNach; $("s3").value = state.stunden;
  render();
});

/* ---------- Rendern ---------- */
let vorher = {};
function setFlash(id, txt){
  const el = $(id);
  if (el.textContent !== txt && vorher[id] !== undefined){
    el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
  }
  el.textContent = txt; vorher[id] = txt;
}

function render(){
  const r = rechne(state);

  // Ergebnis
  setFlash("r-basis", eur0(r.basis.monat));
  setFlash("r-plus",  eur0(r.plus.monat));
  setFlash("r-basis-tot", eur0(r.basis.summe));
  setFlash("r-plus-tot",  eur0(r.plus.summe));
  const max = Math.max(r.basis.summe, r.plus.summe, 1);
  $("bar-basis").style.width = (r.basis.summe / max * 100) + "%";
  $("bar-plus").style.width  = (r.plus.summe  / max * 100) + "%";
  $("col-plus").classList.toggle("win",  r.plus.summe  > r.basis.summe + 1);
  $("col-basis").classList.toggle("win", r.basis.summe > r.plus.summe + 1);

  // Formel-Tokens
  $("k-brutto").textContent = eur0(state.bruttoVor);
  $("k-steuer").textContent = eur0(r.vor.steuer.summe);
  $("k-sv").textContent     = eur0(r.vor.sv.summe);
  $("k-rate").textContent   = pct(r.rate);
  $("k-rate2").textContent  = pct(r.rate);
  $("k-nv").textContent     = eur0(r.nettoVorGedeckelt);
  $("k-nn").textContent     = eur0(r.nettoNach);
  $("k-gb").textContent     = eur0(r.basis.gb);
  $("k-mz").textContent     = eur0(r.basis.mz);
  $("k-p1").textContent     = eur0(r.plusRoh <= r.plusDeckel ? r.basisRoh : r.basisRoh);
  $("k-p2").textContent     = eur0(r.plusDeckel);

  // Rechenweg
  const row = (lbl, val, cls, note) =>
    `<div class="step ${cls || ""}"><span class="lbl">${lbl}${note ? `<span class="note">${note}</span>` : ""}</span><span class="val">${val}</span></div>`;

  const d1 = '<span class="dot" style="background:var(--t1)"></span>';
  const d2 = '<span class="dot" style="background:var(--t2)"></span>';
  const d3 = '<span class="dot" style="background:var(--t3)"></span>';
  const d4 = '<span class="dot" style="background:var(--t4)"></span>';
  const d5 = '<span class="dot" style="background:var(--t5)"></span>';

  let html = "";
  html += row(d1 + "Bruttolohn vor der Geburt", eur(state.bruttoVor));
  html += row("− Werbungskosten-Pauschale", "− " + eur(r.vor.wk), "", "1.230 € im Jahr");
  html += row("− Steuern", "− " + eur(r.vor.steuer.summe), "",
              `Lohnsteuer ${eur(r.vor.steuer.lst)}${r.vor.steuer.kist > 0 ? " · Kirchensteuer " + eur(r.vor.steuer.kist) : ""}${r.vor.steuer.soli > 0 ? " · Soli " + eur(r.vor.steuer.soli) : ""}`);
  html += row("− Sozialabgaben", "− " + eur(r.vor.sv.summe), "",
              `${state.gesetzlich ? "9 % KV/PV · " : ""}10 % RV · 2 % ALV`);
  html += row(d1 + "Elterngeld-Netto vor der Geburt", eur(r.vor.netto), "sum",
              r.gedeckelt ? `gekappt auf ${eur(K.nettoDeckel)}` : "");
  html += row(d2 + "Elterngeld-Netto in der Teilzeit", eur(r.nettoNach), "",
              state.bruttoNach > 0 ? `aus ${eur(state.bruttoNach)} brutto` : "kein Einkommen");
  html += row("Wegfallendes Einkommen", eur(r.differenz), "",
              `${eur(r.nettoVorGedeckelt)} − ${eur(r.nettoNach)}`);
  html += row(d3 + "Ersatzrate", pct(r.rate), "",
              r.vor.netto > 1200 ? "abgesenkt, weil das Netto über 1.200 € liegt"
              : r.vor.netto < 1000 ? "erhöht, weil das Netto unter 1.000 € liegt" : "Standardsatz");
  html += row("Basiselterngeld vor Zuschlägen", eur(r.basisRoh), "",
              r.mindestbetrag ? "Mindestbetrag greift" : `${pct(r.rate)} × ${eur(r.differenz)}`);
  if (state.geschwister) html += row(d4 + "+ Geschwisterbonus", "+ " + eur(r.basis.gb), "", "10 %, mindestens 75 €");
  if (state.mehrlinge)   html += row(d5 + "+ Mehrlingszuschlag", "+ " + eur(r.basis.mz), "", `300 € × ${state.mehrlinge}`);
  html += row("Basiselterngeld", eur(r.basis.monat), "sum");
  html += row("Deckel für ElterngeldPlus", eur(r.plusDeckel), "",
              `halbes Basiselterngeld ohne Teilzeit (${eur(r.basisOhneArbeit)})`);
  html += row("ElterngeldPlus", eur(r.plus.monat), "sum",
              r.plusRoh >= r.plusDeckel - 0.01 ? "durch den Deckel begrenzt" : "Deckel nicht erreicht");
  $("steps").innerHTML = html;

  // Regler-Beschriftung
  $("s1-v").textContent = eur0(state.bruttoVor);
  $("s1-h").textContent = r.gedeckelt
    ? `Über ${eur0(K.nettoDeckel)} Netto zählt nichts mehr — mehr Brutto ändert dein Elterngeld nicht.`
    : `Elterngeld-Netto ${eur0(r.vor.netto)} von ${eur0(K.nettoDeckel)} bis zum Deckel.`;

  $("s2-v").textContent = eur0(state.bruttoNach);
  $("s2-h").textContent = state.bruttoNach === 0
    ? "Ohne Teilzeit sind beide Varianten in der Summe gleich hoch."
    : `Jeder Euro Teilzeit-Netto senkt das Basiselterngeld um ${pct(r.rate)}.`;

  $("s3-v").textContent = state.stunden + " Std.";
  $("s3-h").textContent = state.stunden > K.maxWochenstunden
    ? `Über ${K.maxWochenstunden} Stunden entfällt der Anspruch vollständig.`
    : state.stunden >= 24
      ? "In diesem Bereich ist der Partnerschaftsbonus möglich: 24 bis 32 Stunden bei beiden Eltern."
      : `Erlaubt sind bis zu ${K.maxWochenstunden} Stunden pro Woche.`;

  $("m-val").textContent = mehrlingLabel[state.mehrlinge];

  renderAnswer(r);
  renderSources(r);
}

/* ---------- Fließtext ---------- */
function renderAnswer(r){
  const diffSumme = r.plus.summe - r.basis.summe;
  const n = v => `<span class="n">${v}</span>`;

  let p = [];

  if (state.bruttoNach > 0){
    p.push(`In deinem Fall ist <b>ElterngeldPlus die bessere Wahl</b>. Du bekommst zwar nur ${n(eur0(r.plus.monat))} statt ${n(eur0(r.basis.monat))} im Monat, aber doppelt so lange — über den gesamten Bezug sind das ${n(eur0(r.plus.summe))} statt ${n(eur0(r.basis.summe))}, also ${n(eur0(Math.abs(diffSumme)))} mehr.<sup><a href="#q4a">4</a></sup>`);
    p.push(`Der Grund liegt in der Anrechnung: Basiselterngeld ersetzt nur das Einkommen, das <i>wegfällt</i>. Von deinem Elterngeld-Netto vor der Geburt (<span class="inl t1">${eur0(r.nettoVorGedeckelt)}</span>) bleibt nach Abzug deines Teilzeit-Nettos (<span class="inl t2">${eur0(r.nettoNach)}</span>) nur noch ${n(eur0(r.differenz))} übrig, auf die deine Ersatzrate von <span class="inl t3">${pct(r.rate)}</span> angewendet wird.<sup><a href="#q2">1</a></sup> Ein Basismonat ist dadurch stark gekürzt — verbraucht aber trotzdem einen ganzen Monat deines Kontingents. ElterngeldPlus wird stattdessen auf zwei Monate gestreckt und dabei nur bis auf die Hälfte des Betrags gedeckelt, den du ohne Arbeit bekämst (${n(eur0(r.plusDeckel))}).`);
  } else {
    p.push(`Ohne Einkommen nach der Geburt sind beide Varianten <b>in der Summe gleich viel wert</b>: ${n(eur0(r.basis.summe))} so oder so. ElterngeldPlus ist dann genau die Hälfte pro Monat bei doppelter Laufzeit.<sup><a href="#q4a">4</a></sup> Entscheide hier nach dem Zeitpunkt: Basiselterngeld bringt das Geld schneller, ElterngeldPlus streckt es über einen längeren Zeitraum.`);
    p.push(`Sobald du auch nur etwas dazuverdienst, kippt der Vergleich zugunsten von ElterngeldPlus — schieb den grünen Regler nach oben, um das zu sehen.`);
  }

  if (r.gedeckelt){
    p.push(`Dein Einkommen liegt über der Bemessungsgrenze. Alles über <span class="inl t1">${eur0(K.nettoDeckel)}</span> Elterngeld-Netto bleibt unberücksichtigt,<sup><a href="#q2">1</a></sup> deshalb ändert ein höherer Bruttolohn dein Ergebnis nicht mehr. Prüft außerdem die Einkommensgrenze: Ab ${n(eur0(K.einkommensgrenze))} zu versteuerndem Jahreseinkommen entfällt der Anspruch ganz.<sup><a href="#q1">5</a></sup>`);
  }

  if (r.mindestbetrag){
    p.push(`Rechnerisch läge dein Anspruch unter dem Mindestbetrag, deshalb greift die Untergrenze von ${n(eur0(K.basisMin))} für Basiselterngeld beziehungsweise ${n(eur0(K.plusMin))} für ElterngeldPlus.<sup><a href="#q2">1</a></sup>`);
  }

  if (state.geschwister || state.mehrlinge){
    let z = [];
    if (state.geschwister) z.push(`der Geschwisterbonus von <span class="inl t1" style="background:var(--t4bg);color:var(--t4)">${eur0(r.basis.gb)}</span>`);
    if (state.mehrlinge)   z.push(`der Mehrlingszuschlag von <span class="inl t1" style="background:var(--t5bg);color:var(--t5)">${eur0(r.basis.mz)}</span>`);
    p.push(`Enthalten ist ${z.join(" und ")}. Diese Zuschläge kommen oben auf den Höchstbetrag drauf, werden also nicht mit gedeckelt.<sup><a href="#q2a">2</a></sup>`);
  }

  if (state.stunden > K.maxWochenstunden){
    p.push(`<b>Achtung:</b> Mit ${n(state.stunden + " Wochenstunden")} liegst du über der Grenze von ${K.maxWochenstunden} Stunden. Dann besteht für diese Monate gar kein Anspruch.<sup><a href="#q1">5</a></sup>`);
  } else if (state.stunden >= 24){
    p.push(`Bei ${n(state.stunden + " Stunden")} kommt zusätzlich der Partnerschaftsbonus in Frage: zwei bis vier weitere ElterngeldPlus-Monate, wenn ihr beide gleichzeitig zwischen 24 und 32 Stunden arbeitet.<sup><a href="#q4">3</a></sup>`);
  }

  p.push(`Ein praktischer Hinweis zur Reihenfolge: In den Lebensmonaten 1 und 2 wird das Mutterschaftsgeld voll angerechnet, dort lohnt ElterngeldPlus meist nicht. Üblich ist, mit Basismonaten zu starten und ab dem Wiedereinstieg auf ElterngeldPlus zu wechseln.`);

  $("answer").innerHTML = p.map(t => `<p>${t}</p>`).join("");
}

/* ---------- Belegstellen aus dem RAG-Index ---------- */
const QUELLEN = [
  { id:"q2",  mark:"1", titel:"§ 2 BEEG — Höhe des Elterngeldes", score:"0,94",
    url:"https://www.gesetze-im-internet.de/beeg/__2.html",
    text:"Regelt die Ersatzrate und ihre Gleitzone: 67 Prozent als Ausgangswert, abgesenkt bis auf 65 Prozent bei höherem Einkommen und angehoben bis auf 100 Prozent bei niedrigem. Legt außerdem die Bemessungsgrenze von 2.770 Euro, den Höchstbetrag von 1.800 Euro und den Mindestbetrag von 300 Euro fest." },
  { id:"q2a", mark:"2", titel:"§ 2a BEEG — Geschwisterbonus und Mehrlingszuschlag", score:"0,89",
    url:"https://www.gesetze-im-internet.de/beeg/__2a.html",
    text:"Der Geschwisterbonus beträgt 10 Prozent des zustehenden Elterngeldes, mindestens 75 Euro beim Basiselterngeld. Voraussetzung ist ein weiteres Kind unter drei Jahren oder zwei Kinder unter sechs. Der Mehrlingszuschlag beträgt 300 Euro für jedes weitere Mehrlingskind." },
  { id:"q2c", mark:"6", titel:"§§ 2c bis 2f BEEG — Einkommensermittlung", score:"0,86",
    url:"https://www.gesetze-im-internet.de/beeg/__2c.html",
    text:"Beschreibt, wie aus dem Bruttolohn das Elterngeld-Netto wird: Abzug des Arbeitnehmer-Pauschbetrags, danach pauschalierte Steuern nach dem amtlichen Programmablaufplan und pauschale Sozialabgaben von 9 Prozent für Kranken- und Pflegeversicherung, 10 Prozent für die Rente und 2 Prozent für die Arbeitsförderung. Einmalzahlungen wie Weihnachtsgeld bleiben außen vor." },
  { id:"q4a", mark:"4", titel:"§ 4a BEEG — ElterngeldPlus", score:"0,92",
    url:"https://www.gesetze-im-internet.de/beeg/__4a.html",
    text:"Ein Monat Basiselterngeld entspricht zwei Monaten ElterngeldPlus. Der Monatsbetrag ist auf die Hälfte dessen begrenzt, was ohne Einkommen nach der Geburt zustünde — daraus folgt der Höchstbetrag von 900 Euro." },
  { id:"q4",  mark:"3", titel:"§ 4 BEEG — Bezugszeitraum und Partnerschaftsbonus", score:"0,81",
    url:"https://www.gesetze-im-internet.de/beeg/__4.html",
    text:"Zwölf Monatsbeträge stehen einem Elternteil zu, vierzehn, wenn beide Eltern Elterngeld beziehen. Der Partnerschaftsbonus gewährt zwei bis vier zusätzliche Monate ElterngeldPlus, wenn beide gleichzeitig zwischen 24 und 32 Wochenstunden arbeiten." },
  { id:"q1",  mark:"5", titel:"§ 1 BEEG — Anspruch, Stundengrenze, Einkommensgrenze", score:"0,78",
    url:"https://www.gesetze-im-internet.de/beeg/__1.html",
    text:"Während des Bezugs sind höchstens 32 Wochenstunden erlaubt. Für Geburten ab dem 1. April 2025 entfällt der Anspruch, wenn das zu versteuernde Einkommen im Kalenderjahr vor der Geburt 175.000 Euro übersteigt." }
];

function renderSources(){
  $("sources").innerHTML = QUELLEN.map(q => `
    <details class="src" id="${q.id}">
      <summary><span class="mark">${q.mark}</span><span class="ttl">${q.titel}</span><span class="score">${q.score}</span></summary>
      <div class="body">${q.text} <a href="${q.url}" target="_blank" rel="noopener">Gesetzestext öffnen</a></div>
    </details>`).join("");
}

// Klick auf eine Fußnote öffnet die passende Quelle
document.addEventListener("click", e => {
  const a = e.target.closest('sup a'); if (!a) return;
  e.preventDefault();
  const d = document.querySelector(a.getAttribute("href"));
  if (d){ d.open = true; d.scrollIntoView({ behavior:"smooth", block:"center" }); }
});
</script>
</body>
</html>
