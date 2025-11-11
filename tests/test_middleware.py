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
