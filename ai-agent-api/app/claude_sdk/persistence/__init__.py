"""Persistence layer for Claude SDK data.

This module provides persistence components for saving session data:

- SessionPersister: Persists messages and tool calls
- MetricsPersister: Creates metrics snapshots
- StorageArchiver: Archives working directories to S3 or local storage

Example usage:
    >>> from app.claude_sdk.persistence import (
    ...     SessionPersister,
    ...     MetricsPersister,
    ...     StorageArchiver
    ... )
    >>>
    >>> # Create persisters
    >>> session_persister = SessionPersister(db, session_repo, message_repo, tool_call_repo)
    >>> metrics_persister = MetricsPersister(db, metrics_snapshot_repo)
    >>> storage_archiver = StorageArchiver(
    ...     db, archive_repo,
    ...     storage_provider="s3",
    ...     s3_bucket="my-bucket",
    ...     s3_region="us-east-1"
    ... )
    >>>
    >>> # Persist message
    >>> await session_persister.persist_message(
    ...     session_id=session_id,
    ...     message_type="assistant",
    ...     content="Hello!",
    ...     sequence_number=1
    ... )
    >>>
    >>> # Create metrics snapshot
    >>> await metrics_persister.create_snapshot(
    ...     session_id=session_id,
    ...     snapshot_reason="query_complete",
    ...     total_cost_usd=0.05
    ... )
    >>>
    >>> # Archive working directory
    >>> archive = await storage_archiver.archive_working_directory(
    ...     session_id=session_id,
    ...     working_dir=Path("/workspace/session_dir")
    ... )
"""
from app.claude_sdk.persistence.session_persister import SessionPersister
from app.claude_sdk.persistence.metrics_persister import MetricsPersister
from app.claude_sdk.persistence.storage_archiver import StorageArchiver

__all__ = [
    "SessionPersister",
    "MetricsPersister",
    "StorageArchiver",
]
