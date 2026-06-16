"""
Report routes — retrieve, list, and download research reports.
"""
from pathlib import Path

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.company import ResearchReport
from app.models.user import User
from app.schemas.company import ResearchReportRead

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


# ---------------------------------------------------------------------------
# GET / — list reports for the current user
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ResearchReportRead])
async def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status_filter: str | None = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ResearchReport]:
    """List all research reports created by the current user, newest first."""
    query = (
        select(ResearchReport)
        .where(ResearchReport.created_by_user_id == current_user.id)
        .order_by(ResearchReport.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if status_filter:
        query = query.where(ResearchReport.status == status_filter)

    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /{report_id} — get a single report
# ---------------------------------------------------------------------------

@router.get("/{report_id}", response_model=ResearchReportRead)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResearchReport:
    """Retrieve a research report by ID. Users can only access their own reports."""
    result = await db.execute(
        select(ResearchReport).where(ResearchReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    # Non-superusers can only see their own reports
    if not current_user.is_superuser and report.created_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return report


# ---------------------------------------------------------------------------
# GET /{report_id}/pdf — download generated PDF
# ---------------------------------------------------------------------------

@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> FileResponse:
    """Download the PDF version of a completed research report."""
    result = await db.execute(
        select(ResearchReport).where(ResearchReport.id == report_id)
    )
    report = result.scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if not current_user.is_superuser and report.created_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if not report.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not yet generated for this report",
        )

    pdf_file = Path(report.pdf_path)
    if not pdf_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found on disk",
        )

    filename = f"equity_research_{report.ticker}_{report.id}.pdf"
    return FileResponse(
        path=str(pdf_file),
        media_type="application/pdf",
        filename=filename,
    )
