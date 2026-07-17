"""Circuit breaker and concurrency limiter for provider calls."""

from __future__ import annotations

import time
from collections import deque
from typing import Any


class CircuitBreaker:
    """Stops calling a provider after consecutive failures exceed threshold.

    States: CLOSED (normal) -> OPEN (failing) -> HALF_OPEN (testing recovery)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_requests: int = 1,
    ):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_max_requests = half_open_max_requests

        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._half_open_requests = 0

    @property
    def state(self) -> str:
        self._transition()
        return self._state

    @property
    def is_open(self) -> bool:
        return self.state == "OPEN"

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == "HALF_OPEN":
            self._half_open_requests += 1
            if self._half_open_requests >= self._half_open_max_requests:
                self._state = "CLOSED"
                self._failure_count = 0
                self._half_open_requests = 0
        elif self._state == "CLOSED":
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if (
            self._state == "CLOSED" and self._failure_count >= self._failure_threshold
        ) or self._state == "HALF_OPEN":
            self._state = "OPEN"

    def _transition(self) -> None:
        """Check if we should transition from OPEN to HALF_OPEN."""
        if self._state == "OPEN":
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                self._state = "HALF_OPEN"
                self._half_open_requests = 0

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state
        return state in ("CLOSED", "HALF_OPEN")

    def stats(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time,
        }


class ConcurrencyLimiter:
    """Limits the number of concurrent provider requests."""

    def __init__(self, max_concurrency: int = 5):
        self._max_concurrency = max_concurrency
        self._semaphore_count = max_concurrency
        self._waiters: deque = deque()

    async def __aenter__(self) -> ConcurrencyLimiter:
        while self._semaphore_count <= 0:
            import asyncio

            await asyncio.sleep(0.1)
        self._semaphore_count -= 1
        return self

    async def __aexit__(self, *args: Any) -> None:
        self._semaphore_count += 1

    @property
    def available(self) -> int:
        return self._semaphore_count
