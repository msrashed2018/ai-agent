"""Report service for business logic."""
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report import Report, ReportType, ReportFormat
from app.domain.exceptions import ReportNotFoundError, PermissionDeniedError, SessionNotFoundError
from app.repositories.report_repository import ReportRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.services.storage_manager import StorageManager
from app.services.audit_service import AuditService


class ReportService:
    """Business logic for report generation and management."""

    def __init__(
        self,
        db: AsyncSession,
        report_repo: ReportRepository,
        session_repo: SessionRepository,
        user_repo: UserRepository,
        storage_manager: StorageManager,
        audit_service: AuditService,
    ):
        self.db = db
        self.report_repo = report_repo
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.storage_manager = storage_manager
        self.audit_service = audit_service

    async def generate_from_session(
        self,
        session_id: UUID,
        user_id: UUID,
        title: str,
        description: Optional[str] = None,
        report_type: ReportType = ReportType.AUTO_GENERATED,
        file_format: Optional[ReportFormat] = None,
        tags: Optional[list[str]] = None,
    ) -> Report:
        """Generate a report from session outputs."""
        # Verify session access
        session_model = await self.session_repo.get_by_id(session_id)
        if not session_model:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        if session_model.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin():
                raise PermissionDeniedError("Not authorized to access this session")
        
        # Build report content from session data
        content = await self._build_report_content(session_id)
        
        # Create report entity
        report = Report(
            id=uuid4(),
            session_id=session_id,
            user_id=user_id,
            title=title,
            content=content,
        )
        
        report.description = description
        report.report_type = report_type
        report.file_format = file_format
        report.tags = tags or []
        
        # Save report file if format specified
        if file_format:
            file_content = await self._format_report(content, file_format)
            file_path = await self.storage_manager.save_report(
                report.id,
                file_content,
                file_format.value,
            )
            file_size = file_path.stat().st_size
            report.set_file_output(str(file_path), file_format, file_size)
        
        # Persist
        from app.models.report import ReportModel
        report_model = ReportModel(
            id=report.id,
            session_id=report.session_id,
            user_id=report.user_id,
            title=report.title,
            description=report.description,
            report_type=report.report_type.value,
            content=report.content,
            file_path=report.file_path,
            file_format=report.file_format.value if report.file_format else None,
            file_size_bytes=report.file_size_bytes,
            template_name=report.template_name,
            tags=report.tags,
            is_public=report.is_public,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )
        
        self.db.add(report_model)
        await self.db.flush()
        
        # Audit log
        await self.audit_service.log_report_generated(
            report_id=report.id,
            session_id=session_id,
            user_id=user_id,
            report_type=report_type.value,
        )
        
        await self.db.commit()
        return report

    async def get_report(self, report_id: UUID, user_id: UUID) -> Report:
        """Get report by ID with authorization check."""
        report_model = await self.report_repo.get_by_id(report_id)
        if not report_model:
            raise ReportNotFoundError(f"Report {report_id} not found")
        
        # Check authorization
        if report_model.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin() and not report_model.is_public:
                raise PermissionDeniedError("Not authorized to access this report")
        
        return self._model_to_entity(report_model)

    async def list_reports(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_public: bool = True,
    ) -> list[Report]:
        """List reports for a user."""
        report_models = await self.report_repo.get_by_user(user_id, skip, limit)
        reports = [self._model_to_entity(model) for model in report_models]
        
        # Optionally include public reports
        if include_public:
            public_models = await self.report_repo.get_public_reports(0, limit)
            public_reports = [
                self._model_to_entity(model) 
                for model in public_models 
                if model.user_id != user_id
            ]
            reports.extend(public_reports)
        
        return reports

    async def get_session_reports(
        self,
        session_id: UUID,
        user_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Report]:
        """Get all reports for a session."""
        # Verify session access
        session_model = await self.session_repo.get_by_id(session_id)
        if not session_model:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        if session_model.user_id != user_id:
            user = await self.user_repo.get_by_id(user_id)
            if not user.is_admin():
                raise PermissionDeniedError("Not authorized to access this session")
        
        report_models = await self.report_repo.get_by_session(session_id, skip, limit)
        return [self._model_to_entity(model) for model in report_models]

    async def update_report(
        self,
        report_id: UUID,
        user_id: UUID,
        **updates,
    ) -> Report:
        """Update a report."""
        report = await self.get_report(report_id, user_id)
        
        # Only owner can update
        if report.user_id != user_id:
            raise PermissionDeniedError("Only report owner can update")
        
        # Update entity
        for key, value in updates.items():
            if hasattr(report, key):
                setattr(report, key, value)
        
        report.updated_at = datetime.utcnow()
        
        # Update in database
        await self.report_repo.update(report_id, updated_at=report.updated_at, **updates)
        await self.db.commit()
        
        return report

    async def delete_report(self, report_id: UUID, user_id: UUID) -> bool:
        """Soft delete a report."""
        report = await self.get_report(report_id, user_id)
        
        # Only owner can delete
        if report.user_id != user_id:
            raise PermissionDeniedError("Only report owner can delete")
        
        # Delete file if exists
        if report.file_path:
            await self.storage_manager.delete_report(report_id)
        
        success = await self.report_repo.soft_delete(report_id)
        await self.db.commit()
        return success

    async def set_public(self, report_id: UUID, user_id: UUID, is_public: bool) -> Report:
        """Set report visibility."""
        report = await self.get_report(report_id, user_id)
        
        # Only owner can change visibility
        if report.user_id != user_id:
            raise PermissionDeniedError("Only report owner can change visibility")
        
        report.set_public(is_public)
        await self.report_repo.update(report_id, is_public=is_public, updated_at=datetime.utcnow())
        await self.db.commit()
        
        return report

    async def add_tag(self, report_id: UUID, user_id: UUID, tag: str) -> Report:
        """Add a tag to a report."""
        report = await self.get_report(report_id, user_id)
        
        if report.user_id != user_id:
            raise PermissionDeniedError("Only report owner can add tags")
        
        report.add_tag(tag)
        await self.report_repo.update(report_id, tags=report.tags, updated_at=datetime.utcnow())
        await self.db.commit()
        
        return report

    async def remove_tag(self, report_id: UUID, user_id: UUID, tag: str) -> Report:
        """Remove a tag from a report."""
        report = await self.get_report(report_id, user_id)
        
        if report.user_id != user_id:
            raise PermissionDeniedError("Only report owner can remove tags")
        
        report.remove_tag(tag)
        await self.report_repo.update(report_id, tags=report.tags, updated_at=datetime.utcnow())
        await self.db.commit()
        
        return report

    async def _build_report_content(self, session_id: UUID) -> dict:
        """Build report content from session data."""
        # TODO: Implement comprehensive report content building
        # This should aggregate session messages, tool calls, metrics, etc.
        return {
            "session_id": str(session_id),
            "generated_at": datetime.utcnow().isoformat(),
            "summary": "Session execution summary",
            "sections": [],
            "metrics": {},
        }

    async def _format_report(self, content: dict, format: ReportFormat) -> str:
        """Format report content for file output."""
        if format == ReportFormat.JSON:
            import json
            return json.dumps(content, indent=2)
        
        elif format == ReportFormat.MARKDOWN:
            # Simple markdown formatting
            md = f"# {content.get('summary', 'Report')}\n\n"
            md += f"Generated at: {content.get('generated_at')}\n\n"
            return md
        
        elif format == ReportFormat.HTML:
            # Simple HTML formatting
            html = f"<html><body>"
            html += f"<h1>{content.get('summary', 'Report')}</h1>"
            html += f"<p>Generated at: {content.get('generated_at')}</p>"
            html += "</body></html>"
            return html
        
        elif format == ReportFormat.PDF:
            # TODO: Implement PDF generation (requires library like reportlab)
            raise NotImplementedError("PDF generation not yet implemented")
        
        return str(content)

    def _model_to_entity(self, model) -> Report:
        """Convert database model to domain entity."""
        report = Report(
            id=model.id,
            session_id=model.session_id,
            user_id=model.user_id,
            title=model.title,
            content=model.content,
        )
        
        report.description = model.description
        report.report_type = ReportType(model.report_type)
        report.file_format = ReportFormat(model.file_format) if model.file_format else None
        report.file_path = model.file_path
        report.file_size_bytes = model.file_size_bytes
        report.template_name = model.template_name
        report.tags = model.tags or []
        report.task_execution_id = model.task_execution_id
        report.is_public = model.is_public
        report.created_at = model.created_at
        report.updated_at = model.updated_at
        report.deleted_at = model.deleted_at
        
        return report
