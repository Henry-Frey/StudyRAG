from __future__ import annotations

import logging
import time
import threading
from collections import deque
from typing import Deque, Dict

from fastapi import Depends, HTTPException, Request, status

from src.config import get_settings

logger = logging.getLogger(__name__)

# singleton shared across all requests — created lazily on first use
_rate_limiter_instance: "SlidingWindowRateLimiter | None" = None
_limiter_lock = threading.Lock()


class SlidingWindowRateLimiter:
    """Per-client sliding window rate limiter.

    Stores a deque of timestamps per client IP. On each call the deque is
    pruned of anything older than the window, then checked against the limit.
    Using monotonic time avoids issues with clock adjustments.
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._client_windows: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, client_id: str) -> bool:
        now = time.monotonic()

        with self._lock:
            if client_id not in self._client_windows:
                self._client_windows[client_id] = deque()

            window = self._client_windows[client_id]
            cutoff = now - self._window_seconds

            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) >= self._max_requests:
                logger.warning(
                    "Rate limit exceeded for client '%s': %d requests in %ds window",
                    client_id,
                    len(window),
                    self._window_seconds,
                )
                return False

            window.append(now)
            return True

    def get_request_count(self, client_id: str) -> int:
        now = time.monotonic()
        with self._lock:
            window = self._client_windows.get(client_id, deque())
            cutoff = now - self._window_seconds
            return sum(1 for ts in window if ts > cutoff)

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        return self._window_seconds


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Return the process-wide limiter, creating it on first call."""
    global _rate_limiter_instance

    if _rate_limiter_instance is None:
        with _limiter_lock:
            # double-checked locking — another thread may have created it
            if _rate_limiter_instance is None:
                settings = get_settings()
                _rate_limiter_instance = SlidingWindowRateLimiter(
                    max_requests=settings.rate_limit_per_minute,
                    window_seconds=60,
                )
                logger.info("Rate limiter created: %d req/min", settings.rate_limit_per_minute)

    return _rate_limiter_instance


async def rate_limit_dependency(
    request: Request,
    limiter: SlidingWindowRateLimiter = Depends(get_rate_limiter),
) -> None:
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Rate limit exceeded: maximum {limiter.max_requests} requests "
                f"per {limiter.window_seconds} seconds."
            ),
            headers={"Retry-After": str(limiter.window_seconds)},
        )
