"""Audit service for logging all operations."""
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLogModel


class AuditService:
    """Service for comprehensive audit logging."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        action_type: str,
        user_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        action_details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log an action to the audit trail."""
        audit_log = AuditLogModel(
            user_id=user_id,
            session_id=session_id,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action_details=action_details or {},
            status=status,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            created_at=datetime.utcnow(),
        )

        self.db.add(audit_log)
        await self.db.flush()
        return audit_log

    async def log_session_created(
        self,
        session_id: UUID,
        user_id: UUID,
        mode: str,
        sdk_options: dict,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log session creation."""
        return await self.log_action(
            action_type="session.created",
            user_id=user_id,
            session_id=session_id,
            resource_type="session",
            resource_id=session_id,
            action_details={
                "mode": mode,
                "sdk_options": sdk_options,
            },
            ip_address=ip_address,
            request_id=request_id,
        )

    async def log_session_terminated(
        self,
        session_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log session termination."""
        return await self.log_action(
            action_type="session.terminated",
            user_id=user_id,
            session_id=session_id,
            resource_type="session",
            resource_id=session_id,
            action_details={"reason": reason} if reason else {},
            request_id=request_id,
        )

    async def log_tool_executed(
        self,
        session_id: UUID,
        user_id: UUID,
        tool_name: str,
        tool_use_id: str,
        tool_input: dict,
        status: str = "success",
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log tool execution."""
        return await self.log_action(
            action_type="tool.executed",
            user_id=user_id,
            session_id=session_id,
            resource_type="tool",
            action_details={
                "tool_name": tool_name,
                "tool_use_id": tool_use_id,
                "tool_input": tool_input,
            },
            status=status,
            error_message=error_message,
            request_id=request_id,
        )

    async def log_permission_decision(
        self,
        session_id: UUID,
        user_id: UUID,
        tool_name: str,
        decision: str,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log permission decision."""
        return await self.log_action(
            action_type=f"permission.{decision}",
            user_id=user_id,
            session_id=session_id,
            resource_type="permission",
            action_details={
                "tool_name": tool_name,
                "decision": decision,
                "reason": reason,
            },
            status="success" if decision == "allow" else "denied",
            request_id=request_id,
        )

    async def log_task_executed(
        self,
        task_id: UUID,
        user_id: UUID,
        execution_id: UUID,
        trigger_type: str,
        status: str = "success",
        error_message: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log task execution."""
        return await self.log_action(
            action_type="task.executed",
            user_id=user_id,
            resource_type="task",
            resource_id=task_id,
            action_details={
                "execution_id": str(execution_id),
                "trigger_type": trigger_type,
            },
            status=status,
            error_message=error_message,
            request_id=request_id,
        )

    async def log_report_generated(
        self,
        report_id: UUID,
        session_id: UUID,
        user_id: UUID,
        report_type: str,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log report generation."""
        return await self.log_action(
            action_type="report.generated",
            user_id=user_id,
            session_id=session_id,
            resource_type="report",
            resource_id=report_id,
            action_details={"report_type": report_type},
            request_id=request_id,
        )

    async def log_api_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[UUID] = None,
        status_code: int = 200,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> AuditLogModel:
        """Log API request."""
        return await self.log_action(
            action_type="api.request",
            user_id=user_id,
            resource_type="api",
            action_details={
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
            status="success" if 200 <= status_code < 400 else "failure",
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

    async def log_authentication(
        self,
        user_id: UUID,
        auth_method: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> AuditLogModel:
        """Log authentication attempt."""
        return await self.log_action(
            action_type=f"auth.{auth_method}",
            user_id=user_id if success else None,
            resource_type="authentication",
            action_details={"method": auth_method},
            status="success" if success else "failure",
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_quota_exceeded(
        self,
        user_id: UUID,
        quota_type: str,
        current_value: int,
        limit: int,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log quota exceeded event."""
        return await self.log_action(
            action_type="quota.exceeded",
            user_id=user_id,
            resource_type="quota",
            action_details={
                "quota_type": quota_type,
                "current_value": current_value,
                "limit": limit,
            },
            status="denied",
            request_id=request_id,
        )

    async def log_template_created(
        self,
        template_id: UUID,
        user_id: UUID,
        template_name: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log template creation."""
        return await self.log_action(
            action_type="template.created",
            user_id=user_id,
            resource_type="session_template",
            resource_id=template_id,
            action_details={
                "template_name": template_name,
            },
            ip_address=ip_address,
            request_id=request_id,
        )

    async def log_template_updated(
        self,
        template_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log template update."""
        return await self.log_action(
            action_type="template.updated",
            user_id=user_id,
            resource_type="session_template",
            resource_id=template_id,
            ip_address=ip_address,
            request_id=request_id,
        )

    async def log_template_deleted(
        self,
        template_id: UUID,
        user_id: UUID,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> AuditLogModel:
        """Log template deletion."""
        return await self.log_action(
            action_type="template.deleted",
            user_id=user_id,
            resource_type="session_template",
            resource_id=template_id,
            ip_address=ip_address,
            request_id=request_id,
        )
