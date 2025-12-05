"""Central application configuration loaded from environment variables."""
from __future__ import annotations
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "StudyRAG"
    api_version: str = "0.2.0"
    max_query_length: int = 4000
    default_top_k: int = 5
    score_threshold: float = 0.3
    cache_ttl_seconds: int = 300
    log_level: str = "INFO"

    class Config:
        env_prefix = "STUDYRAG_"
        env_file = ".env"


settings = Settings()
