"""FastAPI application entry point for StudyRAG."""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.config import get_settings
from src.api.routes import router

# ---------------------------------------------------------------------------
# Logging setup (must happen before any logger calls)
# ---------------------------------------------------------------------------


def _configure_logging(log_level: str) -> None:
    """Configure root logger with a human-readable format."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


_configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan: initialise heavyweight components once on startup
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialise LLM, embedder, vector store and agents on startup; clean up on shutdown."""
    settings = get_settings()
    logger.info("StudyRAG starting up…")

    # Store settings in app state for routes
    app.state.settings = settings

    # --- PDF parser & chunker (lightweight) ---
    from src.ingestion.pdf_parser import PDFParser
    from src.ingestion.chunker import TextChunker

    app.state.pdf_parser = PDFParser()
    app.state.chunker = TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    # --- Embedder ---
    try:
        from src.ingestion.embedder import DocumentEmbedder

        app.state.embedder = DocumentEmbedder(model_name=settings.embedding_model)
        logger.info("Embedder loaded: %s", settings.embedding_model)
    except Exception as exc:
        logger.error("Failed to load embedder: %s", exc)
        app.state.embedder = None

    # --- Vector store ---
    try:
        from src.retrieval.vector_store import ChromaVectorStore

        app.state.vector_store = ChromaVectorStore(
            persist_directory=settings.chroma_persist_dir,
            embedder=app.state.embedder,
        )
        logger.info("Vector store initialised at: %s", settings.chroma_persist_dir)
    except Exception as exc:
        logger.error("Failed to initialise vector store: %s", exc)
        app.state.vector_store = None

    # --- Reranker ---
    try:
        from src.retrieval.reranker import CrossEncoderReranker

        app.state.reranker = CrossEncoderReranker(model_name=settings.reranker_model)
        logger.info("Reranker loaded: %s", settings.reranker_model)
    except Exception as exc:
        logger.warning("Reranker not loaded (will skip reranking): %s", exc)
        app.state.reranker = None

    # --- LLM ---
    try:
        from src.llm.local_llm import LocalLLM

        app.state.llm = LocalLLM(
            model_path=settings.llm_model_path,
            n_gpu_layers=settings.llm_n_gpu_layers,
            n_ctx=settings.llm_n_ctx,
            temperature=settings.llm_temperature,
        )
        logger.info(
            "LLM initialised: loaded=%s, path=%s",
            app.state.llm.is_loaded(),
            settings.llm_model_path,
        )
    except Exception as exc:
        logger.error("Failed to initialise LLM: %s", exc)
        app.state.llm = None

    # --- Agents ---
    llm = app.state.llm
    agents: dict = {}

    if llm is not None:
        from src.agents.explainer_agent import ExplainerAgent
        from src.agents.quiz_agent import QuizAgent
        from src.agents.connector_agent import ConnectorAgent

        agents = {
            "explainer": ExplainerAgent(llm=llm),
            "quiz": QuizAgent(llm=llm),
            "connector": ConnectorAgent(llm=llm),
        }
        logger.info("Agents registered: %s", list(agents.keys()))
    else:
        logger.warning("LLM not available – agents will not be registered")

    app.state.agents = agents

    logger.info("StudyRAG startup complete")

    # ----- Application runs here -----
    yield

    # Shutdown
    logger.info("StudyRAG shutting down…")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="StudyRAG",
        description=(
            "KI-Lernassistent mit RAG-Pipeline – "
            "Lernen, Prüfungsvorbereitung und Konzeptvernetzung "
            "mit lokal ausgeführten Sprachmodellen."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS – allow all origins for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        """Redirect root to the interactive API docs."""
        return RedirectResponse(url="/docs")

    return app


# Module-level app instance (used by uvicorn and tests)
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
