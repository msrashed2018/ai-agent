"""
Reports API endpoints.
"""

from typing import Optional
from uuid import UUID
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user, get_db_session
from app.domain.entities import User
from app.repositories.report_repository import ReportRepository
from app.repositories.session_repository import SessionRepository
from app.services.report_service import ReportService
from app.schemas.report import ReportResponse, ReportListResponse
from app.schemas.common import PaginationParams, PaginatedResponse, Links


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ReportResponse:
    """
    Get report details by ID.
    
    Returns report metadata and content structure.
    Use /download endpoint to get the actual file.
    """
    repo = ReportRepository(db)
    report = await repo.get_by_id(str(report_id))
    
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    
    # Check ownership via session
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(str(report.session_id))
    
    if session and session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )
    
    # Build HATEOAS links
    response = ReportResponse.model_validate(report)
    response._links = Links(
        self=f"/api/v1/reports/{report.id}",
        download_html=f"/api/v1/reports/{report.id}/download?format=html",
        download_pdf=f"/api/v1/reports/{report.id}/download?format=pdf",
        download_json=f"/api/v1/reports/{report.id}/download?format=json",
        session=f"/api/v1/sessions/{report.session_id}",
    )
    
    return response


@router.get("", response_model=ReportListResponse)
async def list_reports(
    session_id: Optional[UUID] = Query(None, description="Filter by session ID"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> ReportListResponse:
    """
    List user's reports with pagination and filtering.
    """
    repo = ReportRepository(db)
    
    if session_id:
        # Filter by specific session
        reports = await repo.list_by_session(
            session_id=str(session_id),
            offset=pagination.offset,
            limit=pagination.limit,
        )
    else:
        # Get all reports for user's sessions
        session_repo = SessionRepository(db)
        user_sessions = await session_repo.get_by_user(
            user_id=current_user.id,
            skip=0,
            limit=1000,  # Get all sessions
        )
        session_ids = [str(s.id) for s in user_sessions]
        
        # Get reports for these sessions
        all_reports = []
        for sid in session_ids:
            session_reports = await repo.list_by_session(sid, offset=0, limit=1000)
            all_reports.extend(session_reports)
        
        # Apply pagination manually
        start = pagination.offset
        end = start + pagination.limit
        reports = all_reports[start:end]
    
    # Apply filters
    if report_type:
        reports = [r for r in reports if r.report_type == report_type]
    
    # Get total count
    total = len(reports)
    
    # Convert to response models
    items = []
    for report in reports:
        response = ReportResponse.model_validate(report)
        response._links = Links(
            self=f"/api/v1/reports/{report.id}",
            download_html=f"/api/v1/reports/{report.id}/download?format=html",
        )
        items.append(response)
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/{report_id}/download")
async def download_report(
    report_id: UUID,
    format: str = Query("html", description="Download format (html/pdf/json)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db_session),
) -> FileResponse:
    """
    Download report in specified format.
    
    Supports HTML, PDF, and JSON formats.
    """
    # Get report
    repo = ReportRepository(db)
    report = await repo.get_by_id(str(report_id))
    
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )
    
    # Check ownership
    session_repo = SessionRepository(db)
    session = await session_repo.get_by_id(str(report.session_id))
    
    if session and session.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this report",
        )
    
    # Validate format
    if format not in ["html", "pdf", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Must be html, pdf, or json",
        )
    
    # Get report file path
    service = ReportService(db)
    file_path = await service.get_report_file_path(str(report_id), format)
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file not found in {format} format",
        )
    
    # Determine media type
    media_types = {
        "html": "text/html",
        "pdf": "application/pdf",
        "json": "application/json",
    }
    
    filename = f"{report_id}.{format}"
    
    return FileResponse(
        path=file_path,
        media_type=media_types[format],
        filename=filename,
    )
