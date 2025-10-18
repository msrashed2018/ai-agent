"""Circuit breaker to prevent cascading failures."""
import logging
import time
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class CircuitBreakerState(str, Enum):
    """Circuit breaker states.

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Circuit tripped, requests rejected
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures.

    The circuit breaker pattern prevents cascading failures by:
    1. Tracking failure rate
    2. Opening circuit after threshold exceeded (reject requests)
    3. Half-opening after timeout (test recovery)
    4. Closing circuit when service recovers

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        >>> if breaker.allow_request():
        ...     try:
        ...         result = await do_something()
        ...         breaker.record_success()
        ...     except Exception:
        ...         breaker.record_failure()
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
    ):
        """Initialize circuit breaker with thresholds.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before testing recovery
            success_threshold: Successful attempts needed to close circuit in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

        logger.info(
            f"CircuitBreaker initialized: failure_threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout}s, success_threshold={success_threshold}"
        )

    def allow_request(self) -> bool:
        """Check if request should be allowed.

        Returns:
            True if request allowed, False if circuit is open
        """
        if self.state == CircuitBreakerState.CLOSED:
            # Normal operation - allow all requests
            return True

        elif self.state == CircuitBreakerState.OPEN:
            # Check if recovery timeout elapsed
            if (
                self.last_failure_time
                and (time.time() - self.last_failure_time) >= self.recovery_timeout
            ):
                # Transition to half-open to test recovery
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info("Circuit breaker transitioned to HALF_OPEN state")
                return True

            # Still in open state - reject request
            logger.warning("Circuit breaker is OPEN - request rejected")
            return False

        elif self.state == CircuitBreakerState.HALF_OPEN:
            # In test mode - allow limited requests
            return True

        return False

    def record_success(self) -> None:
        """Record successful operation.

        Updates state based on success count in half-open state.
        """
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                f"Circuit breaker success count: {self.success_count}/{self.success_threshold}"
            )

            if self.success_count >= self.success_threshold:
                # Service recovered - close circuit
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info("Circuit breaker transitioned to CLOSED state - service recovered")

        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed operation.

        Opens circuit if failure threshold exceeded.
        """
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.debug(f"Circuit breaker failure count: {self.failure_count}/{self.failure_threshold}")

        if self.failure_count >= self.failure_threshold:
            # Too many failures - open circuit
            self.state = CircuitBreakerState.OPEN
            logger.warning(
                f"Circuit breaker OPENED after {self.failure_count} failures - "
                f"will retry after {self.recovery_timeout}s"
            )

        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during recovery test - reopen circuit
            self.state = CircuitBreakerState.OPEN
            logger.warning("Circuit breaker REOPENED - recovery test failed")

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker reset to CLOSED state")

    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state.

        Returns:
            CircuitBreakerState: Current state
        """
        return self.state
