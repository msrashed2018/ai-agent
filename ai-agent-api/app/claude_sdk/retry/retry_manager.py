"""Retry manager with exponential backoff and circuit breaker."""
import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Callable, Any, TypeVar, Optional

from claude_agent_sdk import CLIConnectionError, ClaudeSDKError

from app.claude_sdk.retry.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryPolicy:
    """Retry policy configuration.

    Defines how retry logic should behave:
    - max_retries: Maximum number of retry attempts
    - base_delay: Initial delay between retries (seconds)
    - max_delay: Maximum delay between retries (seconds)
    - exponential_base: Base for exponential backoff calculation
    - jitter: Whether to add random jitter to delays

    Example:
        >>> policy = RetryPolicy(max_retries=3, base_delay=2.0)
        >>> manager = RetryManager(policy)
    """

    max_retries: int = 3
    base_delay: float = 2.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryManager:
    """Manage retry logic with exponential backoff.

    This class handles:
    - Automatic retry on transient failures
    - Exponential backoff with optional jitter
    - Circuit breaker integration
    - Retry attempt tracking and logging

    Example:
        >>> policy = RetryPolicy(max_retries=3, base_delay=2.0)
        >>> manager = RetryManager(policy)
        >>> result = await manager.execute_with_retry(some_async_function, arg1, arg2)
    """

    def __init__(self, policy: RetryPolicy, circuit_breaker: Optional[CircuitBreaker] = None):
        """Initialize retry manager with policy.

        Args:
            policy: Retry policy configuration
            circuit_breaker: Optional circuit breaker for failure protection
        """
        self.policy = policy
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

        logger.info(
            f"RetryManager initialized: max_retries={policy.max_retries}, base_delay={policy.base_delay}s"
        )

    async def execute_with_retry(
        self, operation: Callable[..., Any], *args, **kwargs
    ) -> Any:
        """Execute operation with retry logic.

        Args:
            operation: Async function to execute
            *args: Positional arguments for operation
            **kwargs: Keyword arguments for operation

        Returns:
            Result from successful operation execution

        Raises:
            Exception: If all retries are exhausted or non-retryable error occurs
        """
        for attempt in range(self.policy.max_retries + 1):
            try:
                # Check circuit breaker
                if not self.circuit_breaker.allow_request():
                    from app.claude_sdk.exceptions import CircuitBreakerOpenError

                    raise CircuitBreakerOpenError("Circuit breaker is open")

                logger.debug(
                    f"Executing operation (attempt {attempt + 1}/{self.policy.max_retries + 1})"
                )

                # Execute operation
                result = await operation(*args, **kwargs)

                # Success - reset circuit breaker
                self.circuit_breaker.record_success()

                if attempt > 0:
                    logger.info(
                        f"Operation succeeded on attempt {attempt + 1}/{self.policy.max_retries + 1}"
                    )

                return result

            except CLIConnectionError as e:
                # Transient error - retry
                logger.warning(
                    f"Connection error on attempt {attempt + 1}/{self.policy.max_retries + 1}: {str(e)}"
                )

                if attempt < self.policy.max_retries:
                    delay = self._calculate_delay(attempt)
                    logger.info(f"Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    # All retries exhausted
                    self.circuit_breaker.record_failure()
                    logger.error(
                        f"All {self.policy.max_retries + 1} attempts failed with connection errors"
                    )
                    raise

            except ClaudeSDKError as e:
                # Non-retryable SDK error - fail fast
                self.circuit_breaker.record_failure()
                logger.error(f"Non-retryable SDK error: {str(e)}")
                raise

            except Exception as e:
                # Unexpected error - fail fast
                self.circuit_breaker.record_failure()
                logger.error(f"Unexpected error: {str(e)}", exc_info=True)
                raise

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: delay = base_delay * (exponential_base ^ attempt)
        delay = min(
            self.policy.base_delay * (self.policy.exponential_base**attempt),
            self.policy.max_delay,
        )

        if self.policy.jitter:
            # Add random jitter (0-25% of delay)
            jitter = delay * random.uniform(0, 0.25)
            delay += jitter

        return delay

    def reset(self) -> None:
        """Reset retry manager state.

        Clears circuit breaker and retry tracking.
        """
        self.circuit_breaker.reset()
        logger.info("RetryManager reset")
