"""Test configuration for domain layer tests."""

import pytest
from uuid import uuid4
from datetime import datetime


@pytest.fixture
def sample_uuid():
    """Generate a sample UUID."""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID."""
    return uuid4()


@pytest.fixture
def sample_org_id():
    """Generate a sample organization ID."""
    return uuid4()


@pytest.fixture
def sample_session_id():
    """Generate a sample session ID."""
    return uuid4()


@pytest.fixture
def sample_timestamp():
    """Generate a sample timestamp."""
    return datetime.utcnow()
