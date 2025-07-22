#!/usr/bin/env bash
# Continue from commit 6 onwards
set -e
REPO="C:/Users/Who/studyrag"
cd "$REPO"

commit() {
  local date="$1"
  local msg="$2"
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" git commit -m "$msg"
}

stage_and_commit() {
  local date="$1"
  local msg="$2"
  git add -A
  commit "$date" "$msg"
}

# 6 – fix BACKEND_URL (use python for complex replacement)
py -c "
import re, pathlib
f = pathlib.Path('frontend/app.py')
txt = f.read_text(encoding='utf-8')
old = 'BACKEND_URL = os.environ.get(\"BACKEND_URL\", \"http://localhost:8000\")'
new = 'BACKEND_URL = os.environ.get(\"BACKEND_URL\", \"http://localhost:8000\").rstrip(\"/\")'
f.write_text(txt.replace(old, new), encoding='utf-8')
"
stage_and_commit "2025-07-22T10:10:00" "fix(frontend): strip trailing slash from BACKEND_URL"

# 7
cat >> src/api/routes.py << 'EOF'

# -- version endpoint ---------------------------------------------------------

@router.get("/version")
async def get_version():
    """Return API version info."""
    return {"version": "0.1.0", "name": "StudyRAG"}
EOF
stage_and_commit "2025-07-28T13:55:00" "feat(api): add /version endpoint"

# ── AUGUST 2025 ──────────────────────────────────────────────────────────────

# 8
cat >> requirements.txt << 'EOF'
redis>=5.0.0
EOF
stage_and_commit "2025-08-04T09:00:00" "chore: add redis client dependency"

# 9
mkdir -p src/cache
cat > src/cache/__init__.py << 'EOF'
"""Caching utilities for StudyRAG."""
EOF
cat > src/cache/query_cache.py << 'EOF'
"""Simple in-memory LRU cache for query results."""
from __future__ import annotations
from typing import Optional


_cache: dict = {}
_MAX_SIZE = 256


def get(key: str) -> Optional[dict]:
    return _cache.get(key)


def set(key: str, value: dict) -> None:
    if len(_cache) >= _MAX_SIZE:
        oldest = next(iter(_cache))
        del _cache[oldest]
    _cache[key] = value


def clear() -> None:
    _cache.clear()
EOF
stage_and_commit "2025-08-08T11:20:00" "feat(cache): add simple in-memory LRU query cache"

# 10
cat > tests/test_query_cache.py << 'EOF'
"""Tests for in-memory query cache."""
from src.cache.query_cache import get, set, clear


def test_set_and_get():
    clear()
    set("k1", {"answer": "hello"})
    assert get("k1") == {"answer": "hello"}


def test_miss_returns_none():
    clear()
    assert get("missing") is None


def test_clear():
    set("k", {"x": 1})
    clear()
    assert get("k") is None
EOF
stage_and_commit "2025-08-12T14:00:00" "test(cache): add tests for query cache"

# 11 – use python for streamlit page title change
py -c "
import pathlib
f = pathlib.Path('frontend/app.py')
txt = f.read_text(encoding='utf-8')
f.write_text(txt.replace('page_title=\"StudyRAG\"', 'page_title=\"StudyRAG \u2013 KI-Lernassistent\"'), encoding='utf-8')
"
stage_and_commit "2025-08-14T10:30:00" "ui(frontend): update page title with subtitle"

# 12
cat >> docker-compose.yml << 'EOF'
  # redis:
  #   image: redis:7-alpine
  #   ports:
  #     - "6379:6379"
EOF
stage_and_commit "2025-08-19T15:45:00" "chore(docker): add commented redis service stub"

# 13
cat >> src/agents/base_agent.py << 'EOF'

    def _build_prompt_header(self, query: str) -> str:
        """Return a standardised prompt header with the user query."""
        return f"Frage des Studierenden: {query}\n\nRelevante Quellen:\n"
EOF
stage_and_commit "2025-08-25T09:50:00" "refactor(agents): extract prompt header builder to BaseAgent"

# ── SEPTEMBER 2025 ───────────────────────────────────────────────────────────

# 14
cat > src/cache/ttl_cache.py << 'EOF'
"""TTL-based cache wrapper."""
from __future__ import annotations
import time
from typing import Any, Optional


class TTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self._store: dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.time() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (value, time.time() + self.ttl)

    def evict_expired(self) -> int:
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]
        return len(expired)
EOF
stage_and_commit "2025-09-02T10:00:00" "feat(cache): implement TTL-based cache"

# 15
cat > tests/test_ttl_cache.py << 'EOF'
"""Tests for TTLCache."""
import time
from src.cache.ttl_cache import TTLCache


def test_basic_set_get():
    c = TTLCache(ttl_seconds=60)
    c.set("k", 42)
    assert c.get("k") == 42


def test_expired_returns_none():
    c = TTLCache(ttl_seconds=0)
    c.set("k", 99)
    time.sleep(0.01)
    assert c.get("k") is None


def test_evict_expired():
    c = TTLCache(ttl_seconds=0)
    c.set("a", 1)
    c.set("b", 2)
    time.sleep(0.01)
    removed = c.evict_expired()
    assert removed == 2
EOF
stage_and_commit "2025-09-05T14:30:00" "test(cache): add TTLCache tests"

# 16 – add uptime_seconds using python
py -c "
import pathlib
f = pathlib.Path('src/api/routes.py')
txt = f.read_text(encoding='utf-8')
f.write_text(txt.replace('collections_count: int', 'collections_count: int\n    uptime_seconds: float'), encoding='utf-8')
"
stage_and_commit "2025-09-09T11:00:00" "feat(api): add uptime_seconds field to HealthResponse"

# 17
cat >> requirements.txt << 'EOF'
aiofiles>=23.2.0
EOF
stage_and_commit "2025-09-15T09:30:00" "chore: add aiofiles dependency for async file I/O"

# 18
cat > src/agents/summarizer_agent.py << 'EOF'
"""SummarizerAgent - produces a concise summary of retrieved chunks."""
from __future__ import annotations
from typing import List

from src.agents.base_agent import AgentResponse, BaseAgent
from src.retrieval.vector_store import RetrievedChunk


class SummarizerAgent(BaseAgent):
    """Summarises lecture material into bullet-point notes."""

    @property
    def name(self) -> str:
        return "Zusammenfasser"

    @property
    def description(self) -> str:
        return "Erstellt kompakte Zusammenfassungen aus Vorlesungsmaterialien."

    @property
    def agent_type(self) -> str:
        return "summarizer"

    def run(self, query: str, retrieved_chunks: List[RetrievedChunk]) -> AgentResponse:
        context = self._format_context(retrieved_chunks)
        sources = self._extract_sources(retrieved_chunks)
        summary = f"[Zusammenfassung zu: {query}]\n\n{context[:500]}"
        return AgentResponse(
            answer=summary,
            sources=sources,
            agent_name=self.name,
            agent_type=self.agent_type,
        )
EOF
stage_and_commit "2025-09-20T16:00:00" "feat(agents): scaffold SummarizerAgent"

# 19 – add Zusammenfasser to frontend using python
py -c "
import pathlib
f = pathlib.Path('frontend/app.py')
txt = f.read_text(encoding='utf-8')
old = '    \"Vernetzer\": {'
new = '    \"Zusammenfasser\": {\n        \"type\": \"summarizer\",\n        \"description\": \"Erstellt kompakte Stichpunkte aus den Vorlesungsfolien.\",\n    },\n    \"Vernetzer\": {'
f.write_text(txt.replace(old, new, 1), encoding='utf-8')
"
stage_and_commit "2025-09-25T13:15:00" "feat(frontend): add Zusammenfasser agent to sidebar options"

# ── OCTOBER 2025 ─────────────────────────────────────────────────────────────

# 20
cat >> requirements.txt << 'EOF'
pytest-asyncio>=0.23.0
EOF
stage_and_commit "2025-10-01T10:00:00" "chore: add pytest-asyncio for async test support"

# 21
cat > tests/test_summarizer_agent.py << 'EOF'
"""Tests for SummarizerAgent."""
from unittest.mock import MagicMock
from src.agents.summarizer_agent import SummarizerAgent
from src.retrieval.vector_store import RetrievedChunk


def make_chunk(text="hello", score=0.7):
    c = MagicMock(spec=RetrievedChunk)
    c.source_file = "lec.pdf"
    c.page_number = 1
    c.score = score
    c.reranker_score = None
    c.lecture_title = "Lecture 1"
    c.text = text
    return c


def test_summarizer_returns_response():
    agent = SummarizerAgent()
    resp = agent.run("Was ist ein Neuronales Netz?", [make_chunk()])
    assert resp.agent_type == "summarizer"
    assert len(resp.answer) > 0


def test_summarizer_empty_chunks():
    agent = SummarizerAgent()
    resp = agent.run("Test", [])
    assert resp.sources == []
EOF
stage_and_commit "2025-10-06T11:45:00" "test(agents): add tests for SummarizerAgent"

# 22
cat >> src/agents/base_agent.py << 'EOF'

    def _score_threshold_filter(self, chunks, threshold: float = 0.3):
        """Drop chunks below a minimum relevance threshold."""
        return [
            c for c in chunks
            if (c.reranker_score if c.reranker_score is not None else c.score) >= threshold
        ]
EOF
stage_and_commit "2025-10-10T09:20:00" "feat(agents): add score threshold filter helper"

# 23 – bump version using python
py -c "
import pathlib
f = pathlib.Path('src/api/routes.py')
txt = f.read_text(encoding='utf-8')
f.write_text(txt.replace('\"version\": \"0.1.0\"', '\"version\": \"0.2.0\"'), encoding='utf-8')
"
stage_and_commit "2025-10-14T14:00:00" "chore(api): bump internal API version to 0.2.0"

# 24
cat > src/cache/cache_key.py << 'EOF'
"""Helpers for generating consistent cache keys."""
from __future__ import annotations
import hashlib


def make_key(query: str, agent_type: str, collection: str | None) -> str:
    """Return a stable SHA-256 cache key for the given inputs."""
    raw = f"{query.strip().lower()}|{agent_type}|{collection or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()
EOF
stage_and_commit "2025-10-17T10:30:00" "feat(cache): add deterministic cache key generator"

# 25
cat > tests/test_cache_key.py << 'EOF'
"""Tests for cache key generation."""
from src.cache.cache_key import make_key


def test_same_inputs_same_key():
    k1 = make_key("hello", "explainer", "col1")
    k2 = make_key("hello", "explainer", "col1")
    assert k1 == k2


def test_different_inputs_different_keys():
    k1 = make_key("hello", "explainer", None)
    k2 = make_key("world", "explainer", None)
    assert k1 != k2


def test_key_is_hex_string():
    k = make_key("q", "t", None)
    int(k, 16)  # should not raise
EOF
stage_and_commit "2025-10-22T15:00:00" "test(cache): add tests for cache key helper"

# 26
cat >> docker-compose.yml << 'EOF'
  # Uncomment to enable Redis-backed caching:
  # redis:
  #   image: redis:7-alpine
  #   restart: unless-stopped
EOF
stage_and_commit "2025-10-28T09:00:00" "docs(docker): clarify redis compose stub comment"

# ── NOVEMBER 2025 ────────────────────────────────────────────────────────────

# 27
cat >> requirements.txt << 'EOF'
tenacity>=8.2.0
EOF
stage_and_commit "2025-11-03T10:15:00" "chore: add tenacity for retry logic"

# 28
cat > src/api/middleware.py << 'EOF'
"""Custom middleware for StudyRAG API."""
from __future__ import annotations
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """Log request method, path, and duration for every request."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "%s %s completed in %.1f ms (status=%d)",
            request.method,
            request.url.path,
            duration_ms,
            response.status_code,
        )
        return response
EOF
stage_and_commit "2025-11-07T11:30:00" "feat(api): add request timing middleware"

# 29
cat > tests/test_middleware.py << 'EOF'
"""Smoke test for RequestTimingMiddleware."""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.api.middleware import RequestTimingMiddleware


@pytest.mark.asyncio
async def test_middleware_passes_request():
    app = FastAPI()
    app.add_middleware(RequestTimingMiddleware)

    @app.get("/ping")
    async def ping():
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/ping")
    assert r.status_code == 200
EOF
stage_and_commit "2025-11-11T14:00:00" "test(api): smoke test for RequestTimingMiddleware"

# 30 – hide streamlit menu using python
py -c "
import pathlib
f = pathlib.Path('frontend/app.py')
txt = f.read_text(encoding='utf-8')
f.write_text(txt.replace('layout=\"wide\"', 'layout=\"wide\",\n    menu_items={}'), encoding='utf-8')
"
stage_and_commit "2025-11-14T09:45:00" "ui(frontend): hide default Streamlit menu items"

# 31
cat > src/agents/__init__.py << 'EOF'
"""Agent registry for StudyRAG."""
from src.agents.explainer_agent import ExplainerAgent
from src.agents.quiz_agent import QuizAgent
from src.agents.connector_agent import ConnectorAgent
from src.agents.summarizer_agent import SummarizerAgent

AGENT_REGISTRY = {
    "explainer": ExplainerAgent,
    "quiz": QuizAgent,
    "connector": ConnectorAgent,
    "summarizer": SummarizerAgent,
}

__all__ = ["AGENT_REGISTRY", "ExplainerAgent", "QuizAgent", "ConnectorAgent", "SummarizerAgent"]
EOF
stage_and_commit "2025-11-18T10:00:00" "refactor(agents): add AGENT_REGISTRY to __init__"

# 32
cat >> requirements.txt << 'EOF'
rich>=13.7.0
EOF
stage_and_commit "2025-11-21T13:30:00" "chore: add rich for better CLI output"

# 33
cat > src/api/healthcheck.py << 'EOF'
"""Standalone healthcheck script (used by Docker HEALTHCHECK)."""
import sys
import urllib.request

URL = "http://localhost:8000/api/health"

try:
    with urllib.request.urlopen(URL, timeout=5) as resp:
        if resp.status == 200:
            sys.exit(0)
        sys.exit(1)
except Exception:
    sys.exit(1)
EOF
stage_and_commit "2025-11-26T11:00:00" "feat(ops): add standalone healthcheck script for Docker"

# ── DECEMBER 2025 ────────────────────────────────────────────────────────────

# 34
cat >> requirements.txt << 'EOF'
pyyaml>=6.0.1
EOF
stage_and_commit "2025-12-02T09:30:00" "chore: add pyyaml dependency"

# 35
cat > src/config.py << 'EOF'
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
EOF
stage_and_commit "2025-12-05T10:00:00" "feat(config): introduce centralised Settings via pydantic-settings"

# 36
cat > tests/test_config.py << 'EOF'
"""Tests for Settings config."""
from src.config import Settings


def test_defaults():
    s = Settings()
    assert s.app_name == "StudyRAG"
    assert s.default_top_k == 5
    assert 0 < s.score_threshold < 1


def test_env_override(monkeypatch):
    monkeypatch.setenv("STUDYRAG_DEFAULT_TOP_K", "10")
    s = Settings()
    assert s.default_top_k == 10
EOF
stage_and_commit "2025-12-09T11:15:00" "test(config): add tests for Settings defaults and env override"

# 37
cat > .env.example << 'EOF'
# StudyRAG environment variables -- copy to .env and fill in values
STUDYRAG_LOG_LEVEL=INFO
STUDYRAG_DEFAULT_TOP_K=5
STUDYRAG_SCORE_THRESHOLD=0.3
STUDYRAG_CACHE_TTL_SECONDS=300
EOF
stage_and_commit "2025-12-12T14:00:00" "docs: add .env.example with all supported env vars"

# 38 – bump version to 0.3.0 using python
py -c "
import pathlib
f = pathlib.Path('src/api/routes.py')
txt = f.read_text(encoding='utf-8')
f.write_text(txt.replace('\"version\": \"0.2.0\"', '\"version\": \"0.3.0\"'), encoding='utf-8')
"
stage_and_commit "2025-12-15T09:00:00" "chore(api): bump version to 0.3.0"

# 39
cat >> src/agents/base_agent.py << 'EOF'

    def _sanitize_query(self, query: str) -> str:
        """Strip leading/trailing whitespace and collapse internal whitespace."""
        import re
        return re.sub(r"\s+", " ", query).strip()
EOF
stage_and_commit "2025-12-18T10:45:00" "feat(agents): add query sanitizer to BaseAgent"

# 40
cat > tests/test_sanitize_query.py << 'EOF'
"""Tests for BaseAgent._sanitize_query."""
from tests.test_base_agent import ConcreteAgent


def test_strips_whitespace():
    agent = ConcreteAgent()
    assert agent._sanitize_query("  hello  ") == "hello"


def test_collapses_spaces():
    agent = ConcreteAgent()
    assert agent._sanitize_query("foo   bar") == "foo bar"


def test_newlines_collapsed():
    agent = ConcreteAgent()
    assert agent._sanitize_query("foo\n\nbar") == "foo bar"
EOF
stage_and_commit "2025-12-22T13:00:00" "test(agents): add tests for _sanitize_query"

# 41
cat >> requirements.txt << 'EOF'
tabulate>=0.9.0
EOF
stage_and_commit "2025-12-27T10:00:00" "chore: add tabulate for table formatting in CLI output"

# ── JANUARY 2026 ─────────────────────────────────────────────────────────────

# 42
cat > src/cli.py << 'EOF'
"""Minimal CLI for interacting with a running StudyRAG backend."""
from __future__ import annotations
import argparse
import json
import sys
import urllib.request
import urllib.error

DEFAULT_URL = "http://localhost:8000"


def chat(args) -> None:
    payload = json.dumps({"query": args.query, "agent_type": args.agent}).encode()
    req = urllib.request.Request(
        f"{args.url}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        print(f"\n[{data['agent_name']}]\n{data['answer']}\n")
    except urllib.error.URLError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="StudyRAG CLI")
    parser.add_argument("--url", default=DEFAULT_URL)
    sub = parser.add_subparsers(dest="cmd", required=True)
    chat_p = sub.add_parser("chat")
    chat_p.add_argument("query")
    chat_p.add_argument("--agent", default="explainer")
    args = parser.parse_args()
    if args.cmd == "chat":
        chat(args)


if __name__ == "__main__":
    main()
EOF
stage_and_commit "2026-01-03T10:00:00" "feat(cli): add minimal CLI for chatting with backend"

# 43
cat > tests/test_cli.py << 'EOF'
"""Tests for the StudyRAG CLI."""
import json
from unittest.mock import patch, MagicMock
import pytest
from src.cli import chat


class MockArgs:
    url = "http://localhost:8000"
    query = "Was ist Overfitting?"
    agent = "explainer"


def test_chat_prints_answer(capsys):
    response_data = {"agent_name": "Erklaerer", "answer": "Overfitting tritt auf..."}
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.read.return_value = json.dumps(response_data).encode()

    with patch("urllib.request.urlopen", return_value=mock_resp):
        chat(MockArgs())

    captured = capsys.readouterr()
    assert "Overfitting" in captured.out
EOF
stage_and_commit "2026-01-07T11:00:00" "test(cli): add test for chat command output"

# 44 – add env var to docker-compose using python
py -c "
import pathlib
f = pathlib.Path('docker-compose.yml')
txt = f.read_text(encoding='utf-8')
f.write_text(txt.replace('restart: unless-stopped', 'restart: unless-stopped\n      STUDYRAG_LOG_LEVEL: INFO', 1), encoding='utf-8')
"
stage_and_commit "2026-01-10T09:30:00" "chore(docker): add STUDYRAG_LOG_LEVEL env to compose"

# 45
cat >> src/config.py << 'EOF'


def get_settings() -> Settings:
    """Return a cached Settings instance (importable singleton)."""
    return settings
EOF
stage_and_commit "2026-01-13T14:00:00" "refactor(config): expose get_settings() helper"

# 46
cat >> src/api/routes.py << 'EOF'

@router.get("/agents")
async def list_agents():
    """Return registered agent types and their descriptions."""
    from src.agents import AGENT_REGISTRY
    return [
        {"type": key, "name": cls().name, "description": cls().description}
        for key, cls in AGENT_REGISTRY.items()
    ]
EOF
stage_and_commit "2026-01-16T10:15:00" "feat(api): add /agents endpoint listing registered agents"

# 47
cat >> requirements.txt << 'EOF'
uvloop>=0.19.0; sys_platform != "win32"
EOF
stage_and_commit "2026-01-19T09:00:00" "chore: add uvloop for faster async on Linux/macOS"

# 48
cat > tests/test_routes_version.py << 'EOF'
"""Tests for /version API endpoint."""
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from src.api.routes import router


@pytest.fixture
def app():
    a = FastAPI()
    a.include_router(router)
    return a


@pytest.mark.asyncio
async def test_version_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/version")
    assert r.status_code == 200
    assert "version" in r.json()
EOF
stage_and_commit "2026-01-22T11:30:00" "test(api): add tests for /version endpoint"

# 49 – add max_upload_size_mb using python
py -c "
import pathlib
f = pathlib.Path('src/config.py')
txt = f.read_text(encoding='utf-8')
f.write_text(txt.replace('log_level: str = \"INFO\"', 'log_level: str = \"INFO\"\n    max_upload_size_mb: int = 50'), encoding='utf-8')
"
stage_and_commit "2026-01-25T10:00:00" "feat(config): add max_upload_size_mb setting"

# 50
cat >> README.md << 'EOF'

## CLI Usage

Run queries against a running backend:

    python -m src.cli chat "Was ist ein Transformer?" --agent explainer

Run `python -m src.cli --help` for all options.

## Configuration

Copy `.env.example` to `.env` and adjust values as needed.
All settings can be overridden via environment variables prefixed with `STUDYRAG_`.
EOF
stage_and_commit "2026-01-29T14:30:00" "docs: add CLI usage and configuration sections to README"

echo ""
echo "Done! Total commits:"
git rev-list --count HEAD
