"""Test configuration and fixtures for AI-Agent-API-Service.

Provides common test fixtures, database setup, and mock configurations
for unit, integration, and end-to-end tests.
"""

import asyncio
import os
import sys
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment variables BEFORE any imports
test_env = {
    "ENVIRONMENT": "test",
    "DATABASE_URL": "postgresql+asyncpg://aiagent_test:password_test@localhost:5433/aiagent_test_db",
    "DATABASE_POOL_SIZE": "5",
    "DATABASE_MAX_OVERFLOW": "10",
    "REDIS_URL": "redis://localhost:6380/0",
    "CELERY_BROKER_URL": "redis://localhost:6380/1",
    "CELERY_RESULT_BACKEND": "redis://localhost:6380/2",
    "ANTHROPIC_API_KEY": "test_api_key",
    "SECRET_KEY": "test_secret_key_32_character_minimum",
    "LOG_LEVEL": "DEBUG",
}

for key, value in test_env.items():
    os.environ[key] = value

# Add repository root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Lazy import of app - only needed for integration/e2e tests
_app = None
_settings = None
_Base = None
_get_db = None
_User = None
_Session = None
_SessionMode = None
_SessionStatus = None
_SDKOptions = None
_UserModel = None
_OrganizationModel = None
_SessionModel = None


def get_app():
    """Lazily import and return FastAPI app."""
    global _app
    if _app is None:
        from main import app as _app_temp
        _app = _app_temp
    return _app


def get_settings():
    """Lazily import and return settings."""
    global _settings
    if _settings is None:
        from app.core.config import settings as _settings_temp
        _settings = _settings_temp
    return _settings


def get_Base():
    """Lazily import and return SQLAlchemy Base."""
    global _Base
    if _Base is None:
        from app.database.base import Base as _Base_temp
        _Base = _Base_temp
    return _Base


def get_get_db():
    """Lazily import and return get_db."""
    global _get_db
    if _get_db is None:
        from app.database.session import get_db as _get_db_temp
        _get_db = _get_db_temp
    return _get_db


# Import domain entities and value objects (always available)
from app.domain.entities.user import User
from app.domain.entities.session import Session, SessionMode, SessionStatus
from app.domain.value_objects.sdk_options import SDKOptions

# Try to import database models - these might not always be available
try:
    from app.models.user import UserModel, OrganizationModel
    from app.models.session import SessionModel
except ImportError:
    # Models might not be available in all test contexts
    UserModel = None
    OrganizationModel = None
    SessionModel = None


# Test Database Configuration
TEST_DATABASE_URL = "postgresql+asyncpg://aiagent_test:password_test@localhost:5433/aiagent_test_db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Create async database engine for tests."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    # Create all tables
    Base = get_Base()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    Base = get_Base()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def override_get_db(db_session):
    """Override database dependency for testing."""
    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture
def client(override_get_db):
    """Create test client with overridden dependencies."""
    app = get_app()
    get_db = get_get_db()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    app = get_app()
    get_db = get_get_db()
    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# User Fixtures
@pytest_asyncio.fixture
async def test_organization(db_session: AsyncSession) -> OrganizationModel:
    """Create test organization."""
    org = OrganizationModel(
        id=uuid4(),
        name="Test Organization",
        slug="test-org",
        plan="pro",
        max_users=10,
        max_sessions_per_month=1000,
        max_storage_gb=100,
    )
    db_session.add(org)
    await db_session.commit()
    await db_session.refresh(org)
    return org


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_organization: OrganizationModel) -> UserModel:
    """Create test user."""
    user = UserModel(
        id=uuid4(),
        organization_id=test_organization.id,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        password_hash="$2b$12$test_hashed_password",
        role="user",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession, test_organization: OrganizationModel) -> UserModel:
    """Create admin user."""
    user = UserModel(
        id=uuid4(),
        organization_id=test_organization.id,
        email="admin@example.com",
        username="admin",
        full_name="Admin User",
        password_hash="$2b$12$admin_hashed_password",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_session_model(db_session: AsyncSession, test_user: UserModel) -> SessionModel:
    """Create test session model."""
    session = SessionModel(
        id=uuid4(),
        user_id=test_user.id,
        name="Test Session",
        description="Test session for testing",
        mode="interactive",
        status="created",
        sdk_options={
            "model": "claude-sonnet-4-5",
            "max_turns": 10,
            "permission_mode": "default",
        },
        working_directory_path="/tmp/test-workdir",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


# Domain Entity Fixtures
@pytest.fixture
def test_user_entity() -> User:
    """Create test user domain entity."""
    return User(
        id=uuid4(),
        organization_id=uuid4(),
        email="entity@example.com",
        username="entityuser",
        full_name="Entity User",
        role="user",
        is_active=True,
        is_verified=True,
    )


@pytest.fixture
def test_session_entity() -> Session:
    """Create test session domain entity."""
    return Session(
        id=uuid4(),
        user_id=uuid4(),
        name="Entity Session",
        description="Test session entity",
        mode=SessionMode.INTERACTIVE,
        status=SessionStatus.CREATED,
        sdk_options=SDKOptions(
            model="claude-sonnet-4-5",
            max_turns=10,
            permission_mode="default",
        ),
        working_directory_path="/tmp/entity-workdir",
    )


# Mock Fixtures for External Dependencies
@pytest.fixture
def mock_claude_sdk_client():
    """Mock Claude SDK client."""
    mock_client = AsyncMock()
    mock_client.connect.return_value = None
    mock_client.disconnect.return_value = None
    mock_client.query.return_value = None
    mock_client.receive_response.return_value = AsyncMock()
    return mock_client


@pytest.fixture
def mock_mcp_config_builder():
    """Mock MCP config builder."""
    mock_builder = AsyncMock()
    mock_builder.build_session_mcp_config.return_value = {
        "kubernetes_readonly": {
            "command": "python",
            "args": ["-m", "kubemind.mcp.kubernetes"],
            "env": {"K8S_CONTEXT": "test"},
        },
        "database": {
            "type": "stdio",
            "command": "python",
            "args": ["-m", "kubemind.mcp.database"],
        },
    }
    return mock_builder


@pytest.fixture
def mock_permission_service():
    """Mock permission service."""
    mock_service = AsyncMock()
    mock_service.create_permission_callback.return_value = AsyncMock()
    mock_service.check_tool_permission.return_value = AsyncMock()
    return mock_service


@pytest.fixture
def mock_storage_manager():
    """Mock storage manager."""
    mock_manager = AsyncMock()
    mock_manager.create_working_directory.return_value = "/tmp/test-workdir"
    mock_manager.get_working_directory.return_value = "/tmp/test-workdir"
    mock_manager.cleanup_old_archives.return_value = None
    return mock_manager


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    mock_service = AsyncMock()
    mock_service.log_session_created.return_value = None
    mock_service.log_permission_allowed.return_value = None
    mock_service.log_permission_denied.return_value = None
    mock_service.log_tool_executed.return_value = None
    # Template audit methods
    mock_service.log_template_created.return_value = None
    mock_service.log_template_updated.return_value = None
    mock_service.log_template_deleted.return_value = None
    return mock_service


@pytest.fixture
def mock_event_broadcaster():
    """Mock event broadcaster."""
    mock_broadcaster = AsyncMock()
    mock_broadcaster.broadcast_message.return_value = None
    mock_broadcaster.subscribe.return_value = "subscriber_id"
    mock_broadcaster.unsubscribe.return_value = None
    return mock_broadcaster


# Authentication Fixtures
@pytest.fixture
def auth_headers():
    """Create authentication headers for test requests."""
    # This would normally contain a valid JWT token
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def mock_get_current_user(test_user):
    """Mock current user dependency."""
    async def _mock_get_current_user():
        return test_user
    return _mock_get_current_user


# Environment Configuration
# Note: Environment variables are set at module import time above
# This fixture is kept for backward compatibility
@pytest.fixture(autouse=True)
def test_environment():
    """Test environment is already configured at module level."""
    yield


# Test Data Fixtures
@pytest.fixture
def sample_sdk_message():
    """Sample SDK message for testing."""
    return {
        "type": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Hello! I can help you with various tasks.",
            }
        ],
    }


@pytest.fixture
def sample_tool_use_message():
    """Sample tool use message for testing."""
    return {
        "type": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "tool_use_123",
                "name": "mcp__kubernetes_readonly__list_pods",
                "input": {"namespace": "default"},
            }
        ],
    }


@pytest.fixture
def sample_mcp_server_config():
    """Sample MCP server configuration."""
    return {
        "name": "test_server",
        "description": "Test MCP Server",
        "config_type": "stdio",
        "config": {
            "command": "python",
            "args": ["-m", "test.mcp.server"],
            "env": {"TEST_ENV": "true"},
        },
        "is_enabled": True,
        "is_global": False,
    }


# Test Utilities
class MockAsyncIterator:
    """Mock async iterator for testing streams."""
    
    def __init__(self, items):
        self.items = items
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item


@pytest.fixture
def mock_sdk_message_stream():
    """Mock SDK message stream."""
    messages = [
        {"type": "user", "content": "Hello"},
        {"type": "assistant", "content": [{"type": "text", "text": "Hi there!"}]},
    ]
    return MockAsyncIterator(messages)


# Cleanup
@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """Clean up after each test."""
    yield
    # Any cleanup code here


# Pytest plugins configuration
pytest_plugins = [
    "pytest_asyncio",
]
