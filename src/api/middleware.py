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
