"""
Company routes — search, profile, financials, filings, governance, analysis triggers.
"""
from typing import Any, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db, get_current_active_user
from app.models.company import (
    AnalysisJob,
    Company,
    FinancialRatio,
    FinancialStatement,
    GovernanceData,
    ResearchReport,
    SECFiling,
)
from app.models.user import User
from app.schemas.company import (
    AnalysisJobRead,
    CompanyListItem,
    CompanyRead,
    FinancialRatioRead,
    FinancialStatementRead,
    GovernanceDataRead,
    ResearchReportCreate,
    ResearchReportRead,
    SECFilingRead,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/companies", tags=["Companies"])


# ---------------------------------------------------------------------------
# Helper: resolve ticker → Company row or 404
# ---------------------------------------------------------------------------

async def _get_company_by_ticker(ticker: str, db: AsyncSession) -> Company:
    result = await db.execute(
        select(Company).where(func.upper(Company.ticker) == ticker.upper())
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ticker '{ticker.upper()}' not found",
        )
    return company


# ---------------------------------------------------------------------------
# GET /search
# ---------------------------------------------------------------------------

@router.get("/search", response_model=list[CompanyListItem])
async def search_companies(
    q: str = Query(..., min_length=1, max_length=100, description="Ticker or company name"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Company]:
    """Search companies by ticker symbol or name (case-insensitive, partial match)."""
    pattern = f"%{q.upper()}%"
    result = await db.execute(
        select(Company)
        .where(
            or_(
                func.upper(Company.ticker).like(pattern),
                func.upper(Company.name).like(f"%{q.upper()}%"),
            )
        )
        .order_by(Company.ticker)
        .limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /{ticker}
# ---------------------------------------------------------------------------

@router.get("/{ticker}", response_model=CompanyRead)
async def get_company(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Company:
    """Get company profile."""
    return await _get_company_by_ticker(ticker, db)


# ---------------------------------------------------------------------------
# GET /{ticker}/financials
# ---------------------------------------------------------------------------

@router.get("/{ticker}/financials", response_model=list[FinancialStatementRead])
async def get_financials(
    ticker: str,
    statement_type: Optional[str] = Query(None, description="Filter by type: income/balance/cashflow"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[FinancialStatement]:
    """List historical financial statements for a company."""
    company = await _get_company_by_ticker(ticker, db)

    query = (
        select(FinancialStatement)
        .where(FinancialStatement.company_id == company.id)
        .order_by(FinancialStatement.fiscal_year.desc(), FinancialStatement.fiscal_quarter.desc())
        .limit(limit)
    )
    if statement_type:
        query = query.where(FinancialStatement.statement_type == statement_type)

    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /{ticker}/ratios
# ---------------------------------------------------------------------------

@router.get("/{ticker}/ratios", response_model=list[FinancialRatioRead])
async def get_ratios(
    ticker: str,
    period: Optional[str] = Query(None, description="Filter by period, e.g. '2023-FY'"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[FinancialRatio]:
    """List calculated financial ratios for a company."""
    company = await _get_company_by_ticker(ticker, db)

    query = (
        select(FinancialRatio)
        .where(FinancialRatio.company_id == company.id)
        .order_by(FinancialRatio.period.desc(), FinancialRatio.ratio_name)
        .limit(limit)
    )
    if period:
        query = query.where(FinancialRatio.period == period)

    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /{ticker}/filings
# ---------------------------------------------------------------------------

@router.get("/{ticker}/filings", response_model=list[SECFilingRead])
async def get_filings(
    ticker: str,
    form_type: Optional[str] = Query(None, description="Filter by form type, e.g. '10-K'"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[SECFiling]:
    """List SEC filings for a company."""
    company = await _get_company_by_ticker(ticker, db)

    query = (
        select(SECFiling)
        .where(SECFiling.company_id == company.id)
        .order_by(SECFiling.filed_at.desc())
        .limit(limit)
    )
    if form_type:
        query = query.where(SECFiling.form_type == form_type.upper())

    result = await db.execute(query)
    return result.scalars().all()


# ---------------------------------------------------------------------------
# GET /{ticker}/governance
# ---------------------------------------------------------------------------

@router.get("/{ticker}/governance", response_model=list[GovernanceDataRead])
async def get_governance(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[GovernanceData]:
    """Get governance data for a company, ordered by most recent period first."""
    company = await _get_company_by_ticker(ticker, db)

    result = await db.execute(
        select(GovernanceData)
        .where(GovernanceData.company_id == company.id)
        .order_by(GovernanceData.period.desc())
        .limit(10)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# POST /{ticker}/analyze — trigger full analysis job
# ---------------------------------------------------------------------------

@router.post("/{ticker}/analyze", response_model=AnalysisJobRead, status_code=status.HTTP_202_ACCEPTED)
async def trigger_analysis(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AnalysisJob:
    """
    Queue a full AI-powered equity research analysis for a company.
    Returns a job record immediately; poll /api/v1/jobs/{job_id} for status.
    """
    company = await _get_company_by_ticker(ticker, db)

    from app.models.company import JobStatus

    job = AnalysisJob(
        company_id=company.id,
        job_type="full_analysis",
        status=JobStatus.PENDING,
    )
    db.add(job)
    await db.flush()

    logger.info(
        "Analysis job queued",
        job_id=job.id,
        ticker=ticker,
        user_id=current_user.id,
    )

    # TODO: dispatch to Celery — e.g. `run_full_analysis.delay(job.id)`
    return job


# ---------------------------------------------------------------------------
# GET /{ticker}/reports
# ---------------------------------------------------------------------------

@router.get("/{ticker}/reports", response_model=list[ResearchReportRead])
async def get_reports(
    ticker: str,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[ResearchReport]:
    """List research reports for a company."""
    company = await _get_company_by_ticker(ticker, db)

    result = await db.execute(
        select(ResearchReport)
        .where(ResearchReport.company_id == company.id)
        .order_by(ResearchReport.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# POST /{ticker}/reports — create a new research report
# ---------------------------------------------------------------------------

@router.post("/{ticker}/reports", response_model=ResearchReportRead, status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    ticker: str,
    body: ResearchReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResearchReport:
    """Trigger generation of a new research report for this company."""
    company = await _get_company_by_ticker(ticker, db)

    from app.models.company import ReportStatus

    report = ResearchReport(
        company_id=company.id,
        ticker=ticker.upper(),
        report_type=body.report_type,
        status=ReportStatus.DRAFT,
        content={},
        created_by_user_id=current_user.id,
    )
    db.add(report)
    await db.flush()

    logger.info("Research report queued", report_id=report.id, ticker=ticker, user_id=current_user.id)
    # TODO: dispatch to Celery — e.g. `generate_report.delay(report.id, body.dcf_assumptions)`
    return report


# ---------------------------------------------------------------------------
# GET /{ticker}/peers
# ---------------------------------------------------------------------------

@router.get("/{ticker}/peers", response_model=list[CompanyListItem])
async def get_peers(
    ticker: str,
    limit: int = Query(10, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[Company]:
    """
    Return peer companies in the same sector/industry.
    Excludes the queried company itself.
    """
    company = await _get_company_by_ticker(ticker, db)

    if not company.industry and not company.sector:
        return []

    # Match on industry first, fall back to sector
    filters = []
    if company.industry:
        filters.append(Company.industry == company.industry)
    elif company.sector:
        filters.append(Company.sector == company.sector)

    result = await db.execute(
        select(Company)
        .where(Company.id != company.id, *filters)
        .order_by(Company.market_cap.desc().nulls_last())
        .limit(limit)
    )
    return result.scalars().all()
