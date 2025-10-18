"""Message repository for database operations."""
from typing import Optional, List
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import MessageModel
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[MessageModel]):
    """Repository for message database operations."""

    def __init__(self, db: AsyncSession):
        super().__init__(MessageModel, db)

    async def get_by_session(
        self,
        session_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MessageModel]:
        """Get all messages for a session ordered by sequence."""
        result = await self.db.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.sequence_number)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_session_and_type(
        self,
        session_id: UUID,
        message_type: str,
    ) -> List[MessageModel]:
        """Get messages by session and type."""
        result = await self.db.execute(
            select(MessageModel).where(
                and_(
                    MessageModel.session_id == session_id,
                    MessageModel.message_type == message_type
                )
            ).order_by(MessageModel.sequence_number)
        )
        return list(result.scalars().all())

    async def get_result_message(
        self,
        session_id: UUID,
    ) -> Optional[MessageModel]:
        """Get result message for a session."""
        result = await self.db.execute(
            select(MessageModel).where(
                and_(
                    MessageModel.session_id == session_id,
                    MessageModel.message_type == 'result'
                )
            ).order_by(MessageModel.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_message(
        self,
        session_id: UUID,
    ) -> Optional[MessageModel]:
        """Get the latest message in a session."""
        result = await self.db.execute(
            select(MessageModel)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.sequence_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_by_session(self, session_id: UUID) -> int:
        """Count messages in a session."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count())
            .select_from(MessageModel)
            .where(MessageModel.session_id == session_id)
        )
        return result.scalar_one()

    async def get_next_sequence_number(self, session_id: UUID) -> int:
        """Get the next sequence number for a session."""
        result = await self.db.execute(
            select(MessageModel.sequence_number)
            .where(MessageModel.session_id == session_id)
            .order_by(MessageModel.sequence_number.desc())
            .limit(1)
        )
        last_sequence = result.scalar_one_or_none()
        return (last_sequence or 0) + 1

    async def search_content(
        self,
        session_id: UUID,
        search_text: str,
        limit: int = 50,
    ) -> List[MessageModel]:
        """Search messages by content text."""
        # Using JSONB contains operator
        result = await self.db.execute(
            select(MessageModel)
            .where(
                and_(
                    MessageModel.session_id == session_id,
                    MessageModel.content.op('@>')(f'{{"text": "{search_text}"}}')
                )
            )
            .order_by(MessageModel.sequence_number)
            .limit(limit)
        )
        return list(result.scalars().all())
