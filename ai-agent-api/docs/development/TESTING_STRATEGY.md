# Testing Strategy and Best Practices

**Version**: 1.0
**Last Updated**: 2025-10-19
**Purpose**: Comprehensive testing approach and guidelines for AI-Agent-API

---

## Overview

The AI-Agent-API follows a comprehensive testing strategy based on the **testing pyramid**: many unit tests, fewer integration tests, and minimal end-to-end tests. We aim for **80%+ code coverage** to ensure reliability and maintainability.

**Test Framework**: pytest with pytest-asyncio

---

## Testing Pyramid

```
         /\
        /  \       E2E Tests (Few)
       /----\      - Complete workflows
      /      \     - Real API endpoints
     /--------\    - Slowest, most expensive
    /          \
   /  Integration \ Integration Tests (Some)
  /--------------\ - Multiple components
 /                \- Real database
/    Unit Tests    \ Unit Tests (Many)
--------------------
- Individual functions  - Fast execution
- Mocked dependencies   - 80%+ coverage
```

### Coverage Targets

- **Overall**: 80%+
- **Domain Layer**: 90%+
- **Service Layer**: 85%+
- **Repository Layer**: 80%+
- **API Layer**: 75%+

---

## Test Structure

```
tests/
├── conftest.py              # Global fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/
│   │   ├── entities/        # Test domain entities
│   │   └── value_objects/   # Test value objects
│   ├── services/            # Test service layer
│   ├── repositories/        # Test repositories (mocked DB)
│   └── claude_sdk/          # Test SDK integration
├── integration/             # Integration tests (real DB)
│   ├── repositories/        # Test with real database
│   ├── services/            # Test service integration
│   └── claude_sdk/          # Test SDK with database
├── e2e/                     # End-to-end tests
│   └── test_*.py            # Complete API workflows
└── fixtures/                # Shared test data
```

---

## Unit Tests

### Purpose

Test **individual functions/methods** in isolation with all dependencies mocked.

### Characteristics

- **Fast**: < 1 second each
- **Isolated**: No external dependencies
- **Focused**: One function/method per test
- **Mocked**: All dependencies mocked

### Location

`tests/unit/[layer]/test_*.py`

### Example: Testing Service Layer

```python
# tests/unit/test_session_service.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from app.services.session_service import SessionService
from app.domain.entities.session import Session, SessionStatus, SessionMode
from app.domain.exceptions import QuotaExceededError

class TestSessionService:
    """Unit tests for SessionService."""

    @pytest.fixture
    def session_service(self, db_session, mock_storage_manager, mock_audit_service):
        """Create SessionService with mocked dependencies."""
        from app.repositories.session_repository import SessionRepository
        from app.repositories.message_repository import MessageRepository

        return SessionService(
            db=db_session,
            session_repo=SessionRepository(db_session),
            message_repo=MessageRepository(db_session),
            storage_manager=mock_storage_manager,
            audit_service=mock_audit_service,
        )

    @pytest.mark.asyncio
    async def test_create_session_success(
        self,
        session_service,
        test_user,
        mock_storage_manager,
        mock_audit_service,
    ):
        """Test successful session creation."""
        # Arrange
        user_id = test_user.id
        mode = SessionMode.INTERACTIVE
        sdk_options = {
            "model": "claude-sonnet-4-5",
            "max_turns": 10,
        }
        mock_storage_manager.create_working_directory.return_value = "/tmp/test-workdir"

        # Act
        session = await session_service.create_session(
            user_id=user_id,
            mode=mode,
            sdk_options=sdk_options,
            name="Test Session",
        )

        # Assert
        assert session is not None
        assert session.user_id == user_id
        assert session.mode == mode
        assert session.status == SessionStatus.CREATED
        assert session.working_directory_path == "/tmp/test-workdir"

        # Verify mocks called
        mock_storage_manager.create_working_directory.assert_called_once()
        mock_audit_service.log_session_created.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_session_quota_exceeded(
        self,
        session_service,
        test_user,
        db_session,
    ):
        """Test session creation fails when quota exceeded."""
        # Arrange - Create 5 active sessions (exceeding quota)
        from app.models.session import SessionModel

        for i in range(5):
            session = SessionModel(
                id=uuid4(),
                user_id=test_user.id,
                name=f"Session {i}",
                mode="interactive",
                status="active",
                sdk_options={"model": "claude-sonnet-4-5"},
                working_directory_path=f"/tmp/session-{i}",
            )
            db_session.add(session)
        await db_session.commit()

        # Act & Assert
        with pytest.raises(QuotaExceededError):
            await session_service.create_session(
                user_id=test_user.id,
                mode=SessionMode.INTERACTIVE,
                sdk_options={"model": "claude-sonnet-4-5"},
            )
```

### Example: Testing Domain Entity

```python
# tests/unit/domain/entities/test_session.py
import pytest
from uuid import uuid4

from app.domain.entities.session import Session, SessionStatus, SessionMode
from app.domain.exceptions import InvalidStateTransitionError

class TestSession:
    """Unit tests for Session entity."""

    def test_session_creation(self):
        """Test session can be created with valid parameters."""
        # Arrange & Act
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={"model": "claude-sonnet-4-5"},
        )

        # Assert
        assert session.status == SessionStatus.CREATED
        assert session.mode == SessionMode.INTERACTIVE
        assert session.total_messages == 0

    def test_valid_state_transition(self):
        """Test valid state transition succeeds."""
        # Arrange
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        # Act
        session.transition_to(SessionStatus.CONNECTING)

        # Assert
        assert session.status == SessionStatus.CONNECTING

    def test_invalid_state_transition(self):
        """Test invalid state transition raises error."""
        # Arrange
        session = Session(
            id=uuid4(),
            user_id=uuid4(),
            mode=SessionMode.INTERACTIVE,
            sdk_options={},
        )

        # Act & Assert
        with pytest.raises(InvalidStateTransitionError):
            session.transition_to(SessionStatus.COMPLETED)  # Can't go directly
```

### Example: Testing Repository (Mocked)

```python
# tests/unit/repositories/test_session_repository.py
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.repositories.session_repository import SessionRepository
from app.models.session import SessionModel

@pytest.mark.asyncio
class TestSessionRepository:
    """Unit tests for SessionRepository."""

    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = AsyncMock()
        db.execute = AsyncMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock()
        return db

    @pytest.fixture
    def repository(self, mock_db):
        """Create repository with mocked database."""
        return SessionRepository(mock_db)

    async def test_create_session(self, repository, mock_db):
        """Test creating a session."""
        # Arrange
        session_data = {
            "id": uuid4(),
            "user_id": uuid4(),
            "name": "Test",
            "mode": "interactive",
            "status": "created",
        }

        # Act
        session = await repository.create(**session_data)

        # Assert
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()
```

---

## Integration Tests

### Purpose

Test **multiple components together** with real infrastructure (database, Redis).

### Characteristics

- **Slower**: 1-5 seconds each
- **Real DB**: Uses test PostgreSQL database
- **Mocked External APIs**: Claude API mocked
- **Multiple Components**: Tests integration between layers

### Location

`tests/integration/`

### Example: Repository Integration Test

```python
# tests/integration/repositories/test_hook_execution_repository_integration.py
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.hook_execution_repository import HookExecutionRepository

@pytest.mark.asyncio
async def test_create_and_get_hook_execution(db_session: AsyncSession, test_session_model):
    """Test creating and retrieving a hook execution with real database."""
    # Arrange
    repo = HookExecutionRepository(db_session)

    execution_data = {
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "ls -la"},
        "output_data": {"stdout": "file1.txt\nfile2.txt"},
        "execution_time_ms": 150
    }

    # Act
    execution = await repo.create(**execution_data)
    await db_session.commit()

    retrieved = await repo.get_by_id(execution.id)

    # Assert
    assert retrieved is not None
    assert retrieved.hook_name == "pre_execute"
    assert retrieved.tool_name == "bash_tool"
    assert retrieved.execution_time_ms == 150
    assert retrieved.input_data == {"command": "ls -la"}
    assert retrieved.output_data == {"stdout": "file1.txt\nfile2.txt"}

@pytest.mark.asyncio
async def test_get_by_session(db_session: AsyncSession, test_session_model):
    """Test retrieving all hook executions for a session."""
    # Arrange
    repo = HookExecutionRepository(db_session)

    await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "pre_execute",
        "tool_use_id": "toolu_bash_001",
        "tool_name": "bash_tool",
        "input_data": {"command": "echo test"},
        "execution_time_ms": 100
    })

    await repo.create(**{
        "session_id": test_session_model.id,
        "hook_name": "post_execute",
        "tool_use_id": "toolu_python_001",
        "tool_name": "python_tool",
        "input_data": {"code": "print('hello')"},
        "execution_time_ms": 200
    })

    await db_session.commit()

    # Act
    executions = await repo.get_by_session(test_session_model.id)

    # Assert
    assert len(executions) >= 2
    hook_names = [e.hook_name for e in executions]
    assert "pre_execute" in hook_names
    assert "post_execute" in hook_names
```

### Example: Service Integration Test

```python
# tests/integration/services/test_session_service_integration.py
import pytest
from uuid import uuid4

from app.services.session_service import SessionService
from app.domain.entities.session import SessionMode

@pytest.mark.asyncio
async def test_create_and_retrieve_session(
    db_session,
    test_user,
    mock_storage_manager,
    mock_audit_service,
):
    """Test creating and retrieving a session with real database."""
    # Arrange
    from app.repositories.session_repository import SessionRepository

    service = SessionService(
        db=db_session,
        session_repo=SessionRepository(db_session),
        # ... other repos
        storage_manager=mock_storage_manager,
        audit_service=mock_audit_service,
    )

    mock_storage_manager.create_working_directory.return_value = "/tmp/test"

    # Act - Create session
    created = await service.create_session(
        user_id=test_user.id,
        mode=SessionMode.INTERACTIVE,
        sdk_options={"model": "claude-sonnet-4-5"},
        name="Integration Test Session",
    )
    await db_session.commit()

    # Act - Retrieve session
    retrieved = await service.get_session(
        session_id=created.id,
        user_id=test_user.id,
    )

    # Assert
    assert retrieved.id == created.id
    assert retrieved.name == "Integration Test Session"
    assert retrieved.user_id == test_user.id
```

---

## End-to-End Tests

### Purpose

Test **complete workflows** through the API layer with real HTTP requests.

### Characteristics

- **Slowest**: 5-10 seconds each
- **Full Stack**: API → Service → Repository → Database
- **TestClient**: FastAPI's TestClient or httpx AsyncClient
- **Real Endpoints**: Test actual API routes

### Location

`tests/e2e/`

### Example: API Endpoint Test

```python
# tests/e2e/test_session_workflow.py
import pytest
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_complete_session_workflow(async_client, auth_headers):
    """Test complete session lifecycle through API."""
    # Step 1: Create session
    response = await async_client.post(
        "/api/v1/sessions",
        json={
            "name": "E2E Test Session",
            "mode": "interactive",
            "sdk_options": {
                "model": "claude-sonnet-4-5",
                "permission_mode": "default",
            },
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    session_data = response.json()
    session_id = session_data["id"]

    # Step 2: Get session
    response = await async_client.get(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "E2E Test Session"

    # Step 3: Activate session
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/activate",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Step 4: Pause session
    response = await async_client.post(
        f"/api/v1/sessions/{session_id}/pause",
        headers=auth_headers,
    )
    assert response.status_code == 200

    # Step 5: Delete session
    response = await async_client.delete(
        f"/api/v1/sessions/{session_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
```

---

## Test Fixtures

### Global Fixtures (conftest.py)

Located in `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/tests/conftest.py`

#### Database Fixtures

```python
@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async database engine for tests."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncSession:
    """Create database session for tests."""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
```

#### User Fixtures

```python
@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession) -> OrganizationModel:
    """Create test organization."""
    org = OrganizationModel(
        id=uuid4(),
        name="Test Organization",
        slug="test-org",
        plan="pro",
        max_users=10,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_organization) -> UserModel:
    """Create test user."""
    user = UserModel(
        id=uuid4(),
        organization_id=test_organization.id,
        email="test@example.com",
        username="testuser",
        password_hash="$2b$12$test_hashed_password",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
```

#### Mock Fixtures

```python
@pytest.fixture
def mock_claude_sdk_client():
    """Mock Claude SDK client."""
    mock_client = AsyncMock()
    mock_client.connect.return_value = None
    mock_client.disconnect.return_value = None
    mock_client.query.return_value = None
    return mock_client

@pytest.fixture
def mock_storage_manager():
    """Mock storage manager."""
    mock_manager = AsyncMock()
    mock_manager.create_working_directory.return_value = "/tmp/test-workdir"
    mock_manager.get_working_directory.return_value = "/tmp/test-workdir"
    return mock_manager

@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    mock_service = AsyncMock()
    mock_service.log_session_created.return_value = None
    mock_service.log_permission_allowed.return_value = None
    return mock_service
```

#### Test Client Fixtures

```python
@pytest.fixture
def client(override_get_db):
    """Create test client with overridden dependencies."""
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncClient:
    """Create async test client."""
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
```

---

## AAA Pattern (Arrange-Act-Assert)

All tests follow the **AAA pattern** for clarity and consistency:

```python
@pytest.mark.asyncio
async def test_create_session():
    # Arrange - Set up test data and mocks
    user_id = uuid4()
    mode = SessionMode.INTERACTIVE
    sdk_options = {"model": "claude-sonnet-4-5"}
    mock_storage.create_working_directory.return_value = "/tmp/test"

    # Act - Execute the code under test
    session = await service.create_session(
        user_id=user_id,
        mode=mode,
        sdk_options=sdk_options,
    )

    # Assert - Verify the results
    assert session.status == SessionStatus.CREATED
    assert session.user_id == user_id
    mock_storage.create_working_directory.assert_called_once()
```

---

## Mocking External Dependencies

### Mock SDK Client

```python
from unittest.mock import AsyncMock

@pytest.fixture
def mock_sdk_client():
    """Mock Claude SDK client."""
    client = AsyncMock()
    client.connect.return_value = None
    client.query.return_value = {
        "type": "assistant",
        "content": [{"type": "text", "text": "Response"}]
    }
    return client

# Usage in test
async def test_query_session(service, mock_sdk_client):
    response = await service.query("Hello")
    mock_sdk_client.query.assert_called_with("Hello")
```

### Mock HTTP Requests

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_external_api_call():
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"result": "success"}
        )

        response = await external_service.call_api()
        assert response["result"] == "success"
```

### Mock Database Queries

```python
from unittest.mock import MagicMock

def test_repository_query(mock_db):
    # Mock database result
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = SessionModel(id=uuid4())
    mock_db.execute.return_value = mock_result

    # Test
    session = await repo.get_by_id(uuid4())
    assert session is not None
```

---

## Async Testing

### Using pytest-asyncio

All async tests use `@pytest.mark.asyncio`:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

### Async Fixtures

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def async_data():
    """Async fixture."""
    data = await fetch_data()
    yield data
    await cleanup_data(data)

@pytest.mark.asyncio
async def test_with_async_fixture(async_data):
    """Test using async fixture."""
    assert async_data is not None
```

---

## Database Testing

### Test Database Configuration

Tests use a separate test database:

```python
# In conftest.py
TEST_DATABASE_URL = "postgresql+asyncpg://aiagent_test:password_test@localhost:5433/aiagent_test_db"

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
```

### Setup and Teardown

```python
@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create and teardown database for each test."""
    engine = create_async_engine(TEST_DATABASE_URL)

    # Setup: Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Teardown: Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
```

### Transaction Rollback

Each test runs in a transaction that's rolled back:

```python
@pytest_asyncio.fixture
async def db_session(async_engine):
    """Database session with automatic rollback."""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        # Automatic rollback on fixture teardown
```

---

## Test Coverage

### Running Tests with Coverage

```bash
# Run all tests with coverage
make test-cov

# Or manually
pytest tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Coverage Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

# Exclude from coverage
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/__init__.py",
    "*/migrations/*",
]
```

### Coverage Report Example

```
Name                                Stmts   Miss  Cover
-------------------------------------------------------
app/services/session_service.py      145      8    94%
app/repositories/session_repo.py       89      5    94%
app/domain/entities/session.py         67      3    96%
app/api/v1/sessions.py                112     15    87%
-------------------------------------------------------
TOTAL                                2543    198    92%
```

---

## Running Tests

### All Tests

```bash
# Run all tests
make test

# Or manually
pytest tests/
```

### By Test Type

```bash
# Unit tests only
make test-unit

# Integration tests only
make test-integration

# E2E tests only
make test-e2e

# Or manually
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

### Specific Tests

```bash
# Single file
pytest tests/unit/test_session_service.py

# Single test
pytest tests/unit/test_session_service.py::test_create_session_success

# By keyword
pytest -k "session"

# By marker
pytest -m "asyncio"
```

### Verbose Output

```bash
# Verbose mode
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

### Watch Mode

```bash
# Auto-run tests on file changes
make test-watch

# Or manually
poetry run pytest-watch tests/ -- -v --tb=short
```

---

## Best Practices

### 1. One Assertion Per Test (When Possible)

```python
# GOOD - Focused test
async def test_session_status_after_creation():
    session = await service.create_session(...)
    assert session.status == SessionStatus.CREATED

# ACCEPTABLE - Related assertions
async def test_session_properties_after_creation():
    session = await service.create_session(...)
    assert session.status == SessionStatus.CREATED
    assert session.total_messages == 0
    assert session.total_tool_calls == 0
```

### 2. Descriptive Test Names

```python
# GOOD - Clear what's being tested
async def test_create_session_with_invalid_mode_raises_error()
async def test_get_session_returns_none_when_not_found()
async def test_pause_session_transitions_status_to_paused()

# BAD - Vague names
async def test_session()
async def test_error()
```

### 3. Use Parametrize for Multiple Cases

```python
@pytest.mark.parametrize("mode,expected_status", [
    (SessionMode.INTERACTIVE, SessionStatus.CREATED),
    (SessionMode.NON_INTERACTIVE, SessionStatus.CREATED),
    (SessionMode.FORKED, SessionStatus.CREATED),
])
async def test_session_creation_modes(mode, expected_status):
    session = Session(id=uuid4(), user_id=uuid4(), mode=mode, sdk_options={})
    assert session.status == expected_status
```

### 4. Clean Up Resources

```python
@pytest_asyncio.fixture
async def temp_file():
    """Create and cleanup temp file."""
    file_path = "/tmp/test_file.txt"

    # Setup
    with open(file_path, "w") as f:
        f.write("test")

    yield file_path

    # Cleanup
    if os.path.exists(file_path):
        os.remove(file_path)
```

### 5. Don't Test Implementation Details

```python
# GOOD - Test behavior
async def test_create_session_returns_valid_session():
    session = await service.create_session(...)
    assert session.id is not None
    assert session.status == SessionStatus.CREATED

# BAD - Test internal implementation
async def test_create_session_calls_repository():
    await service.create_session(...)
    # Don't test that service calls repository
    # Test the outcome, not how it's achieved
```

---

## Common Testing Patterns

### Testing Repository

```python
@pytest.mark.asyncio
async def test_repository_create_and_retrieve(db_session):
    """Test creating and retrieving entity."""
    repo = SessionRepository(db_session)

    # Create
    session = await repo.create(
        id=uuid4(),
        user_id=uuid4(),
        name="Test",
        mode="interactive",
        status="created",
    )
    await db_session.commit()

    # Retrieve
    retrieved = await repo.get_by_id(session.id)

    assert retrieved.id == session.id
    assert retrieved.name == "Test"
```

### Testing Service

```python
@pytest.mark.asyncio
async def test_service_business_logic(
    db_session,
    test_user,
    mock_storage_manager,
):
    """Test service orchestration."""
    service = SessionService(
        db=db_session,
        session_repo=SessionRepository(db_session),
        storage_manager=mock_storage_manager,
    )

    session = await service.create_session(
        user_id=test_user.id,
        mode=SessionMode.INTERACTIVE,
        sdk_options={},
    )

    assert session is not None
    mock_storage_manager.create_working_directory.assert_called()
```

### Testing API Endpoint

```python
@pytest.mark.asyncio
async def test_api_endpoint(async_client, auth_headers):
    """Test API endpoint."""
    response = await async_client.post(
        "/api/v1/sessions",
        json={
            "name": "Test",
            "mode": "interactive",
            "sdk_options": {"model": "claude-sonnet-4-5"},
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test"
    assert data["status"] == "created"
```

---

## CI/CD Integration

### GitHub Actions (if configured)

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: password
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: make install

      - name: Run tests
        run: make test
```

### Pre-commit Hooks

```bash
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: make test-unit
        language: system
        pass_filenames: false
```

---

## Related Files

**Test Configuration**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/tests/conftest.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/pyproject.toml`

**Unit Test Examples**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/tests/unit/test_session_service.py`
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/tests/unit/domain/entities/test_session.py`

**Integration Test Examples**:
- `/workspace/me/repositories/claude-code-sdk-tests/ai-agent/ai-agent-api/tests/integration/repositories/test_hook_execution_repository_integration.py`

---

## Keywords

testing, pytest, pytest-asyncio, unit-tests, integration-tests, e2e-tests, test-coverage, mocking, fixtures, aaa-pattern, async-testing, database-testing, test-client, parametrize, test-strategy, tdd, test-pyramid, code-coverage, continuous-integration, test-fixtures, mock-dependencies, assertion, test-best-practices, conftest

---

**Related Documentation**:
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Setup testing environment
- [CODE_PATTERNS.md](./CODE_PATTERNS.md) - Code patterns to test
- [DEBUGGING_GUIDE.md](./DEBUGGING_GUIDE.md) - Debugging failed tests
