"""App settings, loaded from .env."""
from __future__ import annotations

import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    llm_model_path: str = "./models/mistral-7b-instruct-v0.3.Q4_K_M.gguf"
    llm_n_gpu_layers: int = -1
    llm_n_ctx: int = 4096
    llm_temperature: float = 0.1

    # Embedding & retrieval
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    chroma_persist_dir: str = "./data/chroma_db"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k_retrieval: int = 10
    top_k_rerank: int = 5

    # Security
    max_input_length: int = 2000
    rate_limit_per_minute: int = 30

    # API server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    logger.info("Configuration loaded: model_path=%s", settings.llm_model_path)
    return settings
