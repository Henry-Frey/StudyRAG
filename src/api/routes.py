"""FastAPI route definitions for the StudyRAG API."""
from __future__ import annotations

import logging
import time
from typing import List, Optional

import torch
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel, Field

from src.security.input_validator import InputValidator, PromptInjectionError, InputTooLongError
from src.security.rate_limiter import rate_limit_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["StudyRAG"])

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""

    query: str = Field(..., min_length=1, max_length=2000, description="User query")
    agent_type: str = Field(default="explainer", description="Agent type: explainer, quiz, connector")
    collection_name: Optional[str] = Field(default=None, description="Target collection (None = all)")


class ChatResponse(BaseModel):
    """Response from the /api/chat endpoint."""

    answer: str
    sources: List[dict]
    agent_name: str
    agent_type: str
    processing_time_ms: float
    quiz_data: Optional[dict] = None


class UploadResponse(BaseModel):
    """Response from the /api/upload endpoint."""

    message: str
    collection_name: str
    chunks_added: int
    pages_processed: int


class CollectionInfo(BaseModel):
    """Metadata for a single ChromaDB collection."""

    name: str
    document_count: int


class HealthResponse(BaseModel):
    """Response from the /api/health endpoint."""

    status: str
    llm_loaded: bool
    chromadb_available: bool
    gpu_available: bool
    collections_count: int


# ---------------------------------------------------------------------------
# Helpers to access app state (set during lifespan in main.py)
# ---------------------------------------------------------------------------


def _get_app_state(request: Request) -> dict:
    """Extract the shared application state from the request's app."""
    return request.app.state.__dict__


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=UploadResponse,
    summary="Upload a PDF and ingest into the vector store",
    status_code=status.HTTP_201_CREATED,
)
async def upload_pdf(
    request: Request,
    file: UploadFile = File(..., description="PDF file to ingest"),
    collection_name: Optional[str] = Form(default=None),
) -> UploadResponse:
    """Ingest a PDF into the vector store.

    Parses the PDF, splits it into chunks, generates embeddings, and stores
    everything in ChromaDB under *collection_name* (defaults to the filename
    stem if not provided).
    """
    state = _get_app_state(request)

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    col_name = collection_name or file.filename.replace(".pdf", "").replace(" ", "_")

    logger.info("Upload request: file='%s', collection='%s'", file.filename, col_name)

    try:
        content = await file.read()

        pdf_parser = state.get("pdf_parser")
        chunker = state.get("chunker")
        embedder = state.get("embedder")
        vector_store = state.get("vector_store")

        if not all([pdf_parser, chunker, embedder, vector_store]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ingestion pipeline not initialised.",
            )

        pages = pdf_parser.parse_pdf_bytes(content, file.filename)
        if not pages:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No text could be extracted from the PDF.",
            )

        chunks = chunker.chunk(pages)
        embedded_chunks = embedder.embed_chunks(chunks)
        added = vector_store.add_documents(embedded_chunks, col_name)

        logger.info(
            "Upload complete: %d pages, %d chunks, collection='%s'",
            len(pages),
            added,
            col_name,
        )

        return UploadResponse(
            message=f"Datei '{file.filename}' erfolgreich verarbeitet.",
            collection_name=col_name,
            chunks_added=added,
            pages_processed=len(pages),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Upload error for '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {exc}",
        ) from exc


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with a StudyRAG agent",
    dependencies=[Depends(rate_limit_dependency)],
)
async def chat(
    request: Request,
    body: ChatRequest,
) -> ChatResponse:
    """Send a query to the specified agent and receive an answer with sources."""
    state = _get_app_state(request)
    t0 = time.perf_counter()

    # Input validation
    validator = InputValidator()
    try:
        validated_query = validator.validate(body.query)
    except InputTooLongError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PromptInjectionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    vector_store = state.get("vector_store")
    reranker = state.get("reranker")
    agents: dict = state.get("agents", {})
    settings = state.get("settings")

    if not vector_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialised.",
        )

    agent = agents.get(body.agent_type)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown agent_type '{body.agent_type}'. Valid: {list(agents.keys())}",
        )

    logger.info(
        "Chat request: agent='%s', collection='%s', query='%.80s'",
        body.agent_type,
        body.collection_name,
        validated_query,
    )

    try:
        top_k = settings.top_k_retrieval if settings else 10
        top_k_rerank = settings.top_k_rerank if settings else 5

        # Connector agent requests more chunks for broader coverage
        if body.agent_type == "connector":
            top_k = top_k * 2

        if body.collection_name:
            chunks = vector_store.query(validated_query, body.collection_name, top_k=top_k)
        else:
            chunks = vector_store.query_all_collections(validated_query, top_k=top_k)

        if not chunks:
            # Return a helpful response even when no documents are indexed
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return ChatResponse(
                answer="Es wurden keine relevanten Dokumente gefunden. "
                       "Bitte laden Sie zuerst Vorlesungsmaterialien hoch.",
                sources=[],
                agent_name=agent.name,
                agent_type=agent.agent_type,
                processing_time_ms=round(elapsed_ms, 2),
            )

        if reranker:
            chunks = reranker.rerank(validated_query, chunks, top_k=top_k_rerank)

        response = agent.run(validated_query, chunks)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        logger.info(
            "Chat complete: agent='%s', time=%.0f ms",
            body.agent_type,
            elapsed_ms,
        )

        return ChatResponse(
            answer=response.answer,
            sources=[src.model_dump() for src in response.sources],
            agent_name=response.agent_name,
            agent_type=response.agent_type,
            processing_time_ms=round(elapsed_ms, 2),
            quiz_data=response.quiz_data,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Chat error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {exc}",
        ) from exc


@router.get(
    "/collections",
    response_model=List[CollectionInfo],
    summary="List all available document collections",
)
async def list_collections(request: Request) -> List[CollectionInfo]:
    """Return all ChromaDB collections with their document counts."""
    state = _get_app_state(request)
    vector_store = state.get("vector_store")

    if not vector_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialised.",
        )

    collection_names = vector_store.list_collections()
    result: List[CollectionInfo] = []

    for name in collection_names:
        info = vector_store.get_collection_info(name)
        result.append(
            CollectionInfo(name=name, document_count=info.get("document_count", 0))
        )

    return result


@router.delete(
    "/collections/{name}",
    summary="Delete a document collection",
    status_code=status.HTTP_200_OK,
)
async def delete_collection(name: str, request: Request) -> dict:
    """Delete the ChromaDB collection identified by *name*."""
    state = _get_app_state(request)
    vector_store = state.get("vector_store")

    if not vector_store:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialised.",
        )

    success = vector_store.delete_collection(name)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{name}' not found or could not be deleted.",
        )

    logger.info("Collection deleted: %s", name)
    return {"message": f"Collection '{name}' successfully deleted."}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API health check",
)
async def health_check(request: Request) -> HealthResponse:
    """Return the current health status of the API and its components."""
    state = _get_app_state(request)

    llm = state.get("llm")
    vector_store = state.get("vector_store")

    llm_loaded = llm.is_loaded() if llm else False
    chromadb_available = vector_store is not None

    collections_count = 0
    if vector_store:
        try:
            collections_count = len(vector_store.list_collections())
        except Exception:
            chromadb_available = False

    gpu_available = torch.cuda.is_available()

    overall_status = "healthy" if (llm_loaded and chromadb_available) else "degraded"

    return HealthResponse(
        status=overall_status,
        llm_loaded=llm_loaded,
        chromadb_available=chromadb_available,
        gpu_available=gpu_available,
        collections_count=collections_count,
    )
