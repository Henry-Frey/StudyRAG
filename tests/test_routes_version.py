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
