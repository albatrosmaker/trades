"""
Jobs routes — poll analysis job status and list recent jobs.
"""
import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.company import AnalysisJob
from app.models.user import User
from app.schemas.company import AnalysisJobRead

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


# ---------------------------------------------------------------------------
# GET / — list recent jobs
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[AnalysisJobRead])
async def list_jobs(
    limit: int = Query(20, ge=1, le=100),
    job_type: str | None = Query(None, description="Filter by job_type"),
    job_status: str | None = Query(None, alias="status", description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[AnalysisJob]:
    """List recent analysis jobs (newest first)."""
    query = (
        select(AnalysisJob)
        .order_by(AnalysisJob.created_at.desc())
        .limit(limit)
    )
    if job_type:
        query = query.where(AnalysisJob.job_type == job_type)
    if job_status:
        query = query.where(AnalysisJob.status == job_status)

    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /{job_id} — get a single job's status and result
# ---------------------------------------------------------------------------

@router.get("/{job_id}", response_model=AnalysisJobRead)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> AnalysisJob:
    """Retrieve the status and result of a specific analysis job."""
    result = await db.execute(
        select(AnalysisJob).where(AnalysisJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found",
        )
    return job
