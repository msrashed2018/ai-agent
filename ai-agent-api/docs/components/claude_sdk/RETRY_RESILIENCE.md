# Retry & Resilience

## Purpose

The Retry & Resilience subsystem provides automatic retry logic, circuit breaker protection, and error handling to ensure reliable Claude SDK operations in the face of transient failures. It implements production-ready reliability patterns including exponential backoff, circuit breaker states, and error classification.

Key Components:
- **RetryManager**: Executes operations with automatic retry and exponential backoff
- **CircuitBreaker**: Prevents cascading failures when service is degraded
- **RetryPolicy**: Configuration for retry behavior (attempts, delays, jitter)
- **ErrorHandler**: Centralizes error handling and recovery logic

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Executor Layer                           │
├─────────────────────────────────────────────────────────────┤
│  BackgroundExecutor                                          │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  RetryManager                                          │ │
│  │    • execute_with_retry(operation, *args)             │ │
│  │    • Exponential backoff calculation                  │ │
│  │    • Error classification (retryable vs permanent)    │ │
│  │    • Integrates with CircuitBreaker                   │ │
│  └────────────────────────────────────────────────────────┘ │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  CircuitBreaker                                        │ │
│  │    • State: CLOSED | OPEN | HALF_OPEN                 │ │
│  │    • allow_request() → bool                           │ │
│  │    • record_success() → transition to CLOSED          │ │
│  │    • record_failure() → increment failures            │ │
│  │    • Auto-recovery after timeout                      │ │
│  └────────────────────────────────────────────────────────┘ │
│    ↓                                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  RetryPolicy                                           │ │
│  │    • max_retries: 3                                   │ │
│  │    • base_delay: 2.0s                                 │ │
│  │    • max_delay: 60.0s                                 │ │
│  │    • exponential_base: 2.0                            │ │
│  │    • jitter: True                                     │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Error Classification                                        │
│    ├─> CLIConnectionError → RETRYABLE (transient)           │
│    ├─> ClaudeSDKError → NON-RETRYABLE (permanent)           │
│    └─> Other errors → NON-RETRYABLE                         │
└─────────────────────────────────────────────────────────────┘
```

## Key Classes & Interfaces

### RetryPolicy

**File**: [app/claude_sdk/retry/retry_manager.py](../../app/claude_sdk/retry/retry_manager.py)

**Purpose**: Configuration dataclass for retry behavior.

```python
# Lines 17-38
@dataclass
class RetryPolicy:
    """Retry policy configuration."""

    max_retries: int = 3          # Maximum retry attempts (total attempts = max_retries + 1)
    base_delay: float = 2.0       # Initial delay between retries (seconds)
    max_delay: float = 60.0       # Maximum delay (seconds)
    exponential_base: float = 2.0 # Base for exponential backoff
    jitter: bool = True           # Add random jitter to delays

    # Example backoff schedule with defaults:
    # Attempt 0: No delay (first try)
    # Attempt 1: 2.0s (2.0 * 2^0 = 2.0)
    # Attempt 2: 4.0s (2.0 * 2^1 = 4.0)
    # Attempt 3: 8.0s (2.0 * 2^2 = 8.0)
    # With jitter: Each delay += random(0-25% of delay)
```

### RetryManager

**File**: [app/claude_sdk/retry/retry_manager.py](../../app/claude_sdk/retry/retry_manager.py)

```python
# Lines 40-170
class RetryManager:
    """Manage retry logic with exponential backoff."""

    def __init__(self, policy: RetryPolicy, circuit_breaker: Optional[CircuitBreaker] = None):
        self.policy = policy
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    async def execute_with_retry(
        self, operation: Callable[..., Any], *args, **kwargs
    ) -> Any:
        """Execute operation with retry logic.

        Flow:
        1. Check circuit breaker before each attempt
        2. Execute operation
        3. On success: record success, return result
        4. On CLIConnectionError (retryable):
           - If retries remain: wait with backoff, retry
           - If exhausted: record failure, raise
        5. On ClaudeSDKError (non-retryable): record failure, raise immediately
        6. On other errors: record failure, raise immediately

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: Original exception if all retries exhausted
        """
        for attempt in range(self.policy.max_retries + 1):
            # 1. Check circuit breaker
            if not self.circuit_breaker.allow_request():
                from app.claude_sdk.exceptions import CircuitBreakerOpenError
                raise CircuitBreakerOpenError("Circuit breaker is open")

            try:
                # 2. Execute operation
                result = await operation(*args, **kwargs)

                # 3. Success - reset circuit breaker
                self.circuit_breaker.record_success()
                return result

            except CLIConnectionError as e:
                # 4. Transient error - retry
                if attempt < self.policy.max_retries:
                    delay = self._calculate_delay(attempt)
                    await asyncio.sleep(delay)
                    continue
                else:
                    # Retries exhausted
                    self.circuit_breaker.record_failure()
                    raise

            except ClaudeSDKError as e:
                # 5. Non-retryable SDK error
                self.circuit_breaker.record_failure()
                raise

            except Exception as e:
                # 6. Unexpected error
                self.circuit_breaker.record_failure()
                raise

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter.

        delay = min(base_delay * (exponential_base ^ attempt), max_delay)
        if jitter: delay += random(0-25% of delay)
        """
        delay = min(
            self.policy.base_delay * (self.policy.exponential_base**attempt),
            self.policy.max_delay,
        )

        if self.policy.jitter:
            jitter = delay * random.uniform(0, 0.25)
            delay += jitter

        return delay
```

### CircuitBreaker

**File**: [app/claude_sdk/retry/circuit_breaker.py](../../app/claude_sdk/retry/circuit_breaker.py)

```python
# Lines 10-22
class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation, requests allowed
    OPEN = "open"           # Circuit tripped, requests rejected
    HALF_OPEN = "half_open" # Testing recovery, limited requests allowed

# Lines 24-161
class CircuitBreaker:
    """Circuit breaker to prevent cascading failures."""

    def __init__(
        self,
        failure_threshold: int = 5,      # Failures before opening circuit
        recovery_timeout: int = 60,       # Seconds before testing recovery
        success_threshold: int = 2,       # Successes needed to close circuit
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

    def allow_request(self) -> bool:
        """Check if request should be allowed.

        Returns:
            True if request allowed, False if circuit is open

        State transitions:
        - CLOSED → Allow all requests
        - OPEN → Check if recovery_timeout elapsed:
            - Yes → Transition to HALF_OPEN, allow request
            - No → Reject request
        - HALF_OPEN → Allow request (to test recovery)
        """
        if self.state == CircuitBreakerState.CLOSED:
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
                return True

            # Still in open state - reject
            return False

        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True

        return False

    def record_success(self) -> None:
        """Record successful operation.

        State transitions:
        - HALF_OPEN: Increment success count
            - If success_threshold reached → CLOSED
        - CLOSED: Reset failure count
        """
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1

            if self.success_count >= self.success_threshold:
                # Service recovered - close circuit
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0

        elif self.state == CircuitBreakerState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed operation.

        State transitions:
        - CLOSED/HALF_OPEN: Increment failure count
            - If failure_threshold reached → OPEN
        - HALF_OPEN: Failed during recovery → OPEN
        """
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            # Too many failures - open circuit
            self.state = CircuitBreakerState.OPEN

        elif self.state == CircuitBreakerState.HALF_OPEN:
            # Failed during recovery test - reopen circuit
            self.state = CircuitBreakerState.OPEN
```

### ErrorHandler

**File**: [app/claude_sdk/handlers/error_handler.py](../../app/claude_sdk/handlers/error_handler.py)

```python
# Lines 16-179
class ErrorHandler:
    """Centralized error handling and recovery logic."""

    def __init__(
        self,
        db: AsyncSession,
        session_repo: SessionRepository,
        audit_service: AuditService,
    ):
        self.db = db
        self.session_repo = session_repo
        self.audit_service = audit_service

    async def handle_sdk_error(
        self, error: Exception, session_id: UUID, context: Dict[str, Any]
    ) -> None:
        """Handle SDK errors and update session state.

        1. Update session status to failed
        2. Log error to audit trail
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Update session status
        await session_repo.update(
            session_id,
            status="failed",
            error_message=error_message
        )

        # Log to audit trail
        await self.log_error(error, session_id, context)

    def is_retryable(self, error: Exception) -> bool:
        """Determine if error is retryable.

        Returns:
            True for transient errors (CLIConnectionError)
            False for permanent errors (ClaudeSDKError, others)
        """
        if isinstance(error, CLIConnectionError):
            return True  # Transient network issues

        if isinstance(error, ClaudeSDKError):
            return False  # Permanent SDK errors

        return False  # Unknown errors are not retryable

    def classify_error(self, error: Exception) -> Dict[str, Any]:
        """Classify error with details for reporting."""
        return {
            "type": type(error).__name__,
            "message": str(error),
            "is_retryable": self.is_retryable(error),
            "category": "connection" if isinstance(error, CLIConnectionError)
                       else "sdk" if isinstance(error, ClaudeSDKError)
                       else "unknown",
            "severity": "warning" if isinstance(error, CLIConnectionError)
                       else "error"
        }
```

## Retry Flow Diagram

```
Operation execution requested
  ↓
RetryManager.execute_with_retry(operation, *args)
  ↓
For attempt in range(max_retries + 1):  # 0, 1, 2, 3 (4 total attempts)
  ↓
  ┌─────────────────────────────────────────┐
  │ 1. Check Circuit Breaker                │
  │    allow = circuit_breaker.allow_request() │
  │    if not allow:                        │
  │        raise CircuitBreakerOpenError    │
  └─────────────────────────────────────────┘
  ↓
  ┌─────────────────────────────────────────┐
  │ 2. Execute Operation                    │
  │    result = await operation(*args)      │
  └─────────────────────────────────────────┘
  ↓
  ├─> SUCCESS
  │     ├─> circuit_breaker.record_success()
  │     └─> return result ✓
  │
  ├─> CLIConnectionError (RETRYABLE)
  │     ├─> if attempt < max_retries:
  │     │     ├─> Calculate backoff delay
  │     │     │     delay = base_delay * (2 ** attempt)
  │     │     │     if jitter: delay += random(0-25%)
  │     │     ├─> await asyncio.sleep(delay)
  │     │     └─> Continue to next attempt →
  │     │
  │     └─> else (retries exhausted):
  │           ├─> circuit_breaker.record_failure()
  │           └─> raise CLIConnectionError ✗
  │
  └─> ClaudeSDKError | Other (NON-RETRYABLE)
        ├─> circuit_breaker.record_failure()
        └─> raise immediately ✗
```

## Circuit Breaker State Machine

```
                         [Initial State]
                               │
                               ↓
                    ┌──────────────────┐
                    │     CLOSED       │ ← Normal operation
                    │  (Allow requests)│
                    └──────────────────┘
                               │
                   failure_count >= failure_threshold (5)
                               │
                               ↓
                    ┌──────────────────┐
                    │      OPEN        │ ← Circuit tripped
                    │ (Reject requests)│
                    └──────────────────┘
                               │
                   recovery_timeout (60s) elapsed
                               │
                               ↓
                    ┌──────────────────┐
                    │   HALF_OPEN      │ ← Testing recovery
                    │ (Limited requests)│
                    └──────────────────┘
                         │         │
            success_count│         │ Any failure
           >= success    │         │
          threshold (2)  │         │
                         ↓         ↓
                    ┌─────────┐  ┌──────┐
                    │ CLOSED  │  │ OPEN │
                    └─────────┘  └──────┘
```

## Error Classification

### Retryable Errors

Transient failures that should be retried:

```python
from claude_agent_sdk import CLIConnectionError

# Examples:
- CLIConnectionError: "Failed to connect to Claude Code CLI"
- CLIConnectionError: "Connection timeout"
- CLIConnectionError: "Connection reset by peer"
```

**Retry Strategy**:
- Exponential backoff
- Up to `max_retries` attempts
- Circuit breaker protection

### Non-Retryable Errors

Permanent failures that should fail fast:

```python
from claude_agent_sdk import ClaudeSDKError

# Examples:
- ClaudeSDKError: "Invalid API key"
- ClaudeSDKError: "Model not found"
- ClaudeSDKError: "Invalid tool configuration"
- ValueError: "Invalid session configuration"
```

**Handling**:
- No retry
- Immediate failure
- Circuit breaker records failure

## Configuration

### Default Configuration

```python
# RetryPolicy defaults
RetryPolicy(
    max_retries=3,          # 4 total attempts
    base_delay=2.0,         # 2 seconds
    max_delay=60.0,         # 1 minute max
    exponential_base=2.0,   # Double each time
    jitter=True             # Add randomness
)

# CircuitBreaker defaults
CircuitBreaker(
    failure_threshold=5,    # Open after 5 failures
    recovery_timeout=60,    # Wait 60s before testing
    success_threshold=2     # Need 2 successes to close
)
```

### Backoff Schedule Examples

**With default settings** (base_delay=2.0, exponential_base=2.0, max_retries=3):

| Attempt | Formula | Delay (no jitter) | With 25% jitter |
|---------|---------|-------------------|-----------------|
| 0 | First try | 0s | 0s |
| 1 | 2.0 * 2^0 | 2.0s | 2.0-2.5s |
| 2 | 2.0 * 2^1 | 4.0s | 4.0-5.0s |
| 3 | 2.0 * 2^2 | 8.0s | 8.0-10.0s |

Total time with failures: 14-17.5s

**Aggressive retry** (base_delay=1.0, max_retries=5):

| Attempt | Delay | Cumulative |
|---------|-------|------------|
| 0 | 0s | 0s |
| 1 | 1.0s | 1.0s |
| 2 | 2.0s | 3.0s |
| 3 | 4.0s | 7.0s |
| 4 | 8.0s | 15.0s |
| 5 | 16.0s | 31.0s |

**Conservative retry** (base_delay=5.0, max_retries=2):

| Attempt | Delay | Cumulative |
|---------|-------|------------|
| 0 | 0s | 0s |
| 1 | 5.0s | 5.0s |
| 2 | 10.0s | 15.0s |

## Integration with Other Components

### EnhancedClaudeClient

Uses retry logic internally for connection:

```python
# From app/claude_sdk/core/client.py:94-129
for attempt in range(self.config.max_retries + 1):
    try:
        self.sdk_client = ClaudeSDKClient(options=self._sdk_options)
        self.state = ClientState.CONNECTED
        return

    except CLIConnectionError as e:
        if attempt < self.config.max_retries:
            delay = self.config.retry_delay * (2**attempt)
            await asyncio.sleep(delay)
        else:
            raise
```

### BackgroundExecutor

Uses RetryManager for query execution:

```python
# From app/claude_sdk/execution/background_executor.py:89-93
retry_manager = RetryManager(retry_policy)
await retry_manager.execute_with_retry(self._execute_query, prompt)
```

### ExecutorFactory

Creates RetryManager for BackgroundExecutor:

```python
# From app/claude_sdk/execution/executor_factory.py:190-194
retry_policy = RetryPolicy(
    max_retries=session.max_retries or 3,
    base_delay=session.retry_delay or 2.0,
)
retry_manager = RetryManager(retry_policy)
```

## Common Tasks

### How to Configure Retry Behavior

```python
from app.claude_sdk.retry.retry_manager import RetryManager, RetryPolicy

# Create custom retry policy
policy = RetryPolicy(
    max_retries=5,      # More retries
    base_delay=1.0,     # Faster initial retry
    max_delay=30.0,     # Lower max delay
    exponential_base=1.5,  # Slower growth
    jitter=True         # Add randomness
)

# Create retry manager
retry_manager = RetryManager(policy)

# Use in operation
result = await retry_manager.execute_with_retry(my_operation, arg1, arg2)
```

### How to Configure Circuit Breaker

```python
from app.claude_sdk.retry.circuit_breaker import CircuitBreaker

# Create custom circuit breaker
breaker = CircuitBreaker(
    failure_threshold=10,   # More tolerant
    recovery_timeout=30,    # Faster recovery test
    success_threshold=3     # Need more successes
)

# Use with retry manager
retry_manager = RetryManager(policy, circuit_breaker=breaker)
```

### How to Handle Errors in Executors

```python
from app.claude_sdk.handlers.error_handler import ErrorHandler

# Create error handler
error_handler = ErrorHandler(db, session_repo, audit_service)

# In executor
try:
    result = await client.query(prompt)
except Exception as e:
    # Handle error
    await error_handler.handle_sdk_error(e, session_id, context={"prompt": prompt})

    # Check if retryable
    if error_handler.is_retryable(e):
        # Can retry
        pass
    else:
        # Permanent failure
        raise
```

### How to Monitor Circuit Breaker State

```python
# Check circuit breaker state
state = circuit_breaker.get_state()

if state == CircuitBreakerState.OPEN:
    print("Circuit is OPEN - requests are being rejected")
elif state == CircuitBreakerState.HALF_OPEN:
    print("Circuit is HALF_OPEN - testing recovery")
elif state == CircuitBreakerState.CLOSED:
    print("Circuit is CLOSED - normal operation")

# Reset circuit breaker
circuit_breaker.reset()  # Force back to CLOSED state
```

### How to Implement Custom Retry Logic

```python
from app.claude_sdk.retry.retry_manager import RetryManager

class CustomRetryManager(RetryManager):
    async def execute_with_retry(self, operation, *args, **kwargs):
        # Custom pre-retry logic
        print("Starting retry sequence...")

        try:
            # Call parent implementation
            result = await super().execute_with_retry(operation, *args, **kwargs)
            print("Operation succeeded!")
            return result

        except Exception as e:
            # Custom error handling
            print(f"All retries exhausted: {e}")
            raise

    def _calculate_delay(self, attempt: int) -> float:
        # Custom backoff calculation
        # Example: Linear backoff instead of exponential
        return self.policy.base_delay * (attempt + 1)
```

## Best Practices

### 1. Choose Appropriate Retry Settings

```python
# Interactive sessions: Fail fast
RetryPolicy(max_retries=1, base_delay=1.0)

# Background tasks: More aggressive retry
RetryPolicy(max_retries=5, base_delay=2.0)

# Critical operations: Very aggressive
RetryPolicy(max_retries=10, base_delay=1.0, max_delay=120.0)
```

### 2. Use Circuit Breaker for External Dependencies

```python
# Wrap external API calls
external_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
retry_manager = RetryManager(policy, circuit_breaker=external_breaker)
```

### 3. Log Retry Attempts

```python
# In retry manager
async def execute_with_retry(self, operation, *args, **kwargs):
    for attempt in range(self.policy.max_retries + 1):
        try:
            logger.info(f"Attempt {attempt + 1}/{self.policy.max_retries + 1}")
            result = await operation(*args, **kwargs)
            logger.info("Operation succeeded")
            return result
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < self.policy.max_retries:
                delay = self._calculate_delay(attempt)
                logger.info(f"Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)
            else:
                logger.error("All retries exhausted")
                raise
```

### 4. Combine with Timeouts

```python
import asyncio

# Set operation timeout
async def execute_with_timeout(operation, timeout_seconds):
    try:
        result = await asyncio.wait_for(operation(), timeout=timeout_seconds)
        return result
    except asyncio.TimeoutError:
        raise CLIConnectionError("Operation timed out")
```

## Related Files

- [app/claude_sdk/retry/retry_manager.py](../../app/claude_sdk/retry/retry_manager.py) - RetryManager, RetryPolicy
- [app/claude_sdk/retry/circuit_breaker.py](../../app/claude_sdk/retry/circuit_breaker.py) - CircuitBreaker, CircuitBreakerState
- [app/claude_sdk/handlers/error_handler.py](../../app/claude_sdk/handlers/error_handler.py) - ErrorHandler
- [app/claude_sdk/core/client.py](../../app/claude_sdk/core/client.py) - EnhancedClaudeClient with retry
- [app/claude_sdk/execution/background_executor.py](../../app/claude_sdk/execution/background_executor.py) - Uses RetryManager
- [app/claude_sdk/exceptions.py](../../app/claude_sdk/exceptions.py) - SDK exception hierarchy

## Related Documentation

- [SDK_INTEGRATION_OVERVIEW.md](./SDK_INTEGRATION_OVERVIEW.md) - Overall architecture
- [CLIENT_MANAGEMENT.md](./CLIENT_MANAGEMENT.md) - EnhancedClaudeClient retry logic
- [EXECUTION_STRATEGIES.md](./EXECUTION_STRATEGIES.md) - How executors use retry

## Keywords

retry-logic, resilience, circuit-breaker, exponential-backoff, retry-manager, retry-policy, circuit-breaker-state, error-handling, error-classification, transient-failures, permanent-failures, retryable-errors, non-retryable-errors, failure-recovery, cascading-failures, recovery-timeout, failure-threshold, success-threshold, jitter, backoff-schedule, cli-connection-error, claude-sdk-error, error-handler, graceful-degradation, reliability-patterns, fault-tolerance
