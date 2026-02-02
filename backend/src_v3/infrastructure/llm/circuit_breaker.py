"""
Circuit Breaker for LLM Providers

FIX Cortez74: Implements circuit breaker pattern to prevent cascading failures
when LLM providers are unavailable or experiencing issues.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit is open, requests fail fast without calling LLM
- HALF_OPEN: Testing if LLM is back, allowing limited requests

Configuration:
- failure_threshold: Number of failures before opening circuit (default: 5)
- recovery_timeout: Seconds to wait before trying half-open (default: 30)
- half_open_max_calls: Max calls allowed in half-open state (default: 3)
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, Callable, TypeVar, Generic
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3
    success_threshold: int = 2  # Successes needed in half-open to close


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None


class CircuitBreaker:
    """
    Circuit breaker implementation for LLM providers.

    Usage:
        breaker = CircuitBreaker(name="gemini")

        async with breaker:
            response = await llm.generate(messages)

        # Or with decorator:
        @breaker.protect
        async def call_llm():
            return await llm.generate(messages)
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change: float = time.time()

        # Thread safety
        self._lock = asyncio.Lock()

        # Statistics
        self._stats = CircuitBreakerStats()

        logger.info(
            "CircuitBreaker initialized: %s (threshold=%d, timeout=%.1fs)",
            name, self.config.failure_threshold, self.config.recovery_timeout
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)"""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)"""
        return self._state == CircuitState.OPEN

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "stats": {
                "total_calls": self._stats.total_calls,
                "successful_calls": self._stats.successful_calls,
                "failed_calls": self._stats.failed_calls,
                "rejected_calls": self._stats.rejected_calls,
                "state_changes": self._stats.state_changes,
            }
        }

    async def _check_state(self) -> bool:
        """
        Check and potentially transition circuit state.
        Returns True if request should proceed, False if rejected.
        """
        async with self._lock:
            self._stats.total_calls += 1

            if self._state == CircuitState.CLOSED:
                return True

            elif self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time is not None:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.config.recovery_timeout:
                        self._transition_to(CircuitState.HALF_OPEN)
                        self._half_open_calls = 0
                        return True

                # Still in timeout, reject request
                self._stats.rejected_calls += 1
                return False

            elif self._state == CircuitState.HALF_OPEN:
                # Allow limited calls to test recovery
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True

                # Too many half-open calls, reject
                self._stats.rejected_calls += 1
                return False

        return True

    async def record_success(self) -> None:
        """Record a successful call"""
        async with self._lock:
            self._stats.successful_calls += 1
            self._stats.last_success_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    self._failure_count = 0
                    self._success_count = 0

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    async def record_failure(self, error: Optional[Exception] = None) -> None:
        """Record a failed call"""
        async with self._lock:
            self._stats.failed_calls += 1
            self._stats.last_failure_time = time.time()
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to(CircuitState.OPEN)
                self._success_count = 0

            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.warning(
                        "CircuitBreaker %s OPENED after %d failures",
                        self.name, self._failure_count,
                        extra={"error": str(error) if error else None}
                    )

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state (must be called with lock held)"""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._last_state_change = time.time()
            self._stats.state_changes += 1

            logger.info(
                "CircuitBreaker %s: %s -> %s",
                self.name, old_state.value, new_state.value
            )

    async def __aenter__(self):
        """Async context manager entry"""
        allowed = await self._check_state()
        if not allowed:
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open. "
                f"Retry after {self.config.recovery_timeout}s."
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if exc_type is None:
            await self.record_success()
        else:
            await self.record_failure(exc_val)
        return False  # Don't suppress exceptions

    def protect(self, func: Callable) -> Callable:
        """Decorator to protect an async function with circuit breaker"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with self:
                return await func(*args, **kwargs)
        return wrapper

    async def reset(self) -> None:
        """Reset circuit breaker to closed state"""
        async with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
            self._last_failure_time = None
            logger.info("CircuitBreaker %s manually reset to CLOSED", self.name)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request is rejected"""
    pass


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = asyncio.Lock()


async def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
) -> CircuitBreaker:
    """
    Get or create a circuit breaker by name.

    Args:
        name: Unique name for the circuit breaker (e.g., "gemini", "ollama")
        config: Optional configuration

    Returns:
        CircuitBreaker instance
    """
    async with _registry_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name, config)
        return _circuit_breakers[name]


def get_all_circuit_breakers() -> Dict[str, Dict[str, Any]]:
    """Get stats for all circuit breakers"""
    return {name: cb.get_stats() for name, cb in _circuit_breakers.items()}
