"""Sliding-window rate limiter for FastAPI."""
from __future__ import annotations

import logging
import time
import threading
from collections import deque
from typing import Deque, Dict

from fastapi import Depends, HTTPException, Request, status

from src.config import get_settings

logger = logging.getLogger(__name__)

# Module-level singleton so all routes share the same limiter instance
_rate_limiter_instance: "SlidingWindowRateLimiter | None" = None
_limiter_lock = threading.Lock()


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter.

    Tracks request timestamps per *client_id* in a :class:`collections.deque`.
    Timestamps older than *window_seconds* are pruned on each call to
    :meth:`is_allowed`.

    Args:
        max_requests: Maximum number of allowed requests within the window.
        window_seconds: Duration of the sliding window in seconds (default 60).
    """

    def __init__(self, max_requests: int, window_seconds: int = 60) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._client_windows: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_allowed(self, client_id: str) -> bool:
        """Check whether *client_id* may make another request.

        Prunes expired timestamps, then either records the new timestamp and
        returns ``True``, or returns ``False`` if the limit is reached.

        Args:
            client_id: Unique identifier for the client (e.g. IP address).

        Returns:
            ``True`` if the request is within the rate limit, ``False`` otherwise.
        """
        now = time.monotonic()

        with self._lock:
            if client_id not in self._client_windows:
                self._client_windows[client_id] = deque()

            window: Deque[float] = self._client_windows[client_id]

            # Prune timestamps outside the current window
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
        """Return the current request count for *client_id* within the window."""
        now = time.monotonic()
        with self._lock:
            window = self._client_windows.get(client_id, deque())
            cutoff = now - self._window_seconds
            return sum(1 for ts in window if ts > cutoff)

    @property
    def max_requests(self) -> int:
        """Maximum requests allowed per window."""
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        """Window duration in seconds."""
        return self._window_seconds


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------


def get_rate_limiter() -> SlidingWindowRateLimiter:
    """Return the singleton :class:`SlidingWindowRateLimiter`.

    Creates the instance on first call using settings from :func:`get_settings`.
    """
    global _rate_limiter_instance

    if _rate_limiter_instance is None:
        with _limiter_lock:
            if _rate_limiter_instance is None:
                settings = get_settings()
                _rate_limiter_instance = SlidingWindowRateLimiter(
                    max_requests=settings.rate_limit_per_minute,
                    window_seconds=60,
                )
                logger.info(
                    "Rate limiter created: %d req/min",
                    settings.rate_limit_per_minute,
                )

    return _rate_limiter_instance


async def rate_limit_dependency(
    request: Request,
    limiter: SlidingWindowRateLimiter = Depends(get_rate_limiter),
) -> None:
    """FastAPI dependency that enforces rate limiting.

    Uses the client's IP address as the ``client_id``.

    Raises:
        HTTPException: 429 Too Many Requests if the limit is exceeded.
    """
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
