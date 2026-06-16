"""
Valuation routes — DCF modeling and comparable company analysis.
"""
from datetime import datetime, timezone
from typing import Any, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_active_user
from app.models.company import Company, FinancialStatement, FinancialRatio, ValuationModel
from app.models.user import User
from app.schemas.company import DCFAssumptions, DCFResult, PeerCompanyRead

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/valuation", tags=["Valuation"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _resolve_company(ticker: str, db: AsyncSession) -> Company:
    result = await db.execute(
        select(Company).where(func.upper(Company.ticker) == ticker.upper())
    )
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{ticker.upper()}' not found",
        )
    return company


def _run_dcf(
    assumptions: DCFAssumptions,
    base_revenue: Optional[float],
    base_ebitda_margin: Optional[float],
    shares_outstanding: Optional[float],
    current_price: Optional[float],
) -> dict[str, Any]:
    """
    Core DCF calculation.  Returns a dict of results.

    All monetary values are in the same units as the input financial data
    (typically thousands or millions depending on the source).
    """
    wacc = assumptions.wacc
    tgr = assumptions.terminal_growth_rate
    years = assumptions.projection_years

    # --- Revenue projections ---
    growth_rates = assumptions.revenue_growth_rates or [0.05] * years
    # Pad or truncate to exactly `years` entries
    if len(growth_rates) < years:
        growth_rates = growth_rates + [growth_rates[-1]] * (years - len(growth_rates))
    growth_rates = growth_rates[:years]

    # --- EBITDA margin projections ---
    ebitda_margins = assumptions.ebitda_margins or [base_ebitda_margin or 0.15] * years
    if len(ebitda_margins) < years:
        ebitda_margins = ebitda_margins + [ebitda_margins[-1]] * (years - len(ebitda_margins))
    ebitda_margins = ebitda_margins[:years]

    capex_pct = assumptions.capex_pct_revenue or 0.05
    nwc_pct = assumptions.nwc_pct_revenue or 0.02
    tax_rate = assumptions.tax_rate or 0.21

    revenues: list[float] = []
    fcfs: list[float] = []
    rev = base_revenue or 1_000_000  # fallback unit

    for i in range(years):
        rev = rev * (1 + growth_rates[i])
        revenues.append(rev)
        ebit = rev * ebitda_margins[i]  # simplified: EBITDA ≈ EBIT for DCF
        nopat = ebit * (1 - tax_rate)
        capex = rev * capex_pct
        delta_nwc = rev * nwc_pct * growth_rates[i]
        fcf = nopat - capex - delta_nwc
        fcfs.append(fcf)

    # --- Discount FCFs ---
    pv_fcfs = [fcf / (1 + wacc) ** (i + 1) for i, fcf in enumerate(fcfs)]
    pv_fcf_total = sum(pv_fcfs)

    # --- Terminal value (Gordon Growth) ---
    terminal_fcf = fcfs[-1] * (1 + tgr)
    terminal_value = terminal_fcf / (wacc - tgr)
    pv_terminal = terminal_value / (1 + wacc) ** years

    enterprise_value = pv_fcf_total + pv_terminal

    # --- Bridge to equity ---
    debt = assumptions.debt or 0.0
    cash = assumptions.cash or 0.0
    equity_value = enterprise_value - debt + cash

    shares = assumptions.shares_outstanding or shares_outstanding or 1.0
    intrinsic_per_share = equity_value / shares if shares else None

    upside = None
    if intrinsic_per_share and current_price:
        upside = (intrinsic_per_share - current_price) / current_price * 100

    return {
        "enterprise_value": round(enterprise_value, 2),
        "equity_value": round(equity_value, 2),
        "pv_fcf": round(pv_fcf_total, 2),
        "pv_terminal_value": round(pv_terminal, 2),
        "terminal_value": round(terminal_value, 2),
        "projected_fcf": [round(f, 2) for f in fcfs],
        "projected_revenues": [round(r, 2) for r in revenues],
        "intrinsic_value_per_share": round(intrinsic_per_share, 2) if intrinsic_per_share else None,
        "upside_downside_pct": round(upside, 2) if upside is not None else None,
    }


# ---------------------------------------------------------------------------
# POST /{ticker}/dcf
# ---------------------------------------------------------------------------

@router.post("/{ticker}/dcf", response_model=DCFResult)
async def run_dcf(
    ticker: str,
    assumptions: DCFAssumptions,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> DCFResult:
    """
    Run a Discounted Cash Flow valuation with user-provided assumptions.

    Required fields: wacc, terminal_growth_rate, projection_years.
    """
    company = await _resolve_company(ticker, db)

    # Try to pull latest income statement for base metrics
    fs_result = await db.execute(
        select(FinancialStatement)
        .where(
            FinancialStatement.company_id == company.id,
            FinancialStatement.statement_type == "income",
        )
        .order_by(FinancialStatement.fiscal_year.desc())
        .limit(1)
    )
    latest_income = fs_result.scalar_one_or_none()

    base_revenue: Optional[float] = None
    base_ebitda_margin: Optional[float] = None

    if latest_income and latest_income.data:
        data = latest_income.data
        base_revenue = data.get("revenue") or data.get("totalRevenue") or data.get("revenues")
        ebitda = data.get("ebitda") or data.get("EBITDA")
        if base_revenue and ebitda:
            base_ebitda_margin = ebitda / base_revenue

    # Current price and shares from company metadata
    current_price: Optional[float] = None
    shares_outstanding: Optional[float] = None

    results = _run_dcf(
        assumptions=assumptions,
        base_revenue=base_revenue,
        base_ebitda_margin=base_ebitda_margin,
        shares_outstanding=shares_outstanding,
        current_price=current_price,
    )

    # Persist the model
    model = ValuationModel(
        company_id=company.id,
        model_type="dcf",
        assumptions=assumptions.model_dump(),
        results=results,
        created_by_user_id=current_user.id,
    )
    db.add(model)
    await db.flush()

    logger.info("DCF computed", ticker=ticker, model_id=model.id, user_id=current_user.id)

    return DCFResult(
        ticker=ticker.upper(),
        assumptions=assumptions,
        model_id=model.id,
        created_at=datetime.now(timezone.utc),
        current_price=current_price,
        **results,
    )


# ---------------------------------------------------------------------------
# GET /{ticker}/comps
# ---------------------------------------------------------------------------

@router.get("/{ticker}/comps", response_model=list[PeerCompanyRead])
async def get_comps(
    ticker: str,
    limit: int = Query(10, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> list[PeerCompanyRead]:
    """
    Comparable company analysis — returns peer companies with key trading multiples.
    Peers are matched on industry, then sector if industry unavailable.
    """
    company = await _resolve_company(ticker, db)

    if not company.industry and not company.sector:
        return []

    filter_col = Company.industry if company.industry else Company.sector
    filter_val = company.industry or company.sector

    result = await db.execute(
        select(Company)
        .where(Company.id != company.id, filter_col == filter_val)
        .order_by(Company.market_cap.desc().nulls_last())
        .limit(limit)
    )
    peers = result.scalars().all()

    comp_list: list[PeerCompanyRead] = []
    for peer in peers:
        # Attempt to pull recent ratios from DB
        ratios_result = await db.execute(
            select(FinancialRatio)
            .where(
                FinancialRatio.company_id == peer.id,
                FinancialRatio.ratio_name.in_(["pe_ratio", "ev_ebitda", "price_to_book", "revenue_growth"]),
            )
            .order_by(FinancialRatio.period.desc())
            .limit(4)
        )
        ratios = {r.ratio_name: r.value for r in ratios_result.scalars().all()}

        comp_list.append(
            PeerCompanyRead(
                ticker=peer.ticker,
                name=peer.name,
                sector=peer.sector,
                industry=peer.industry,
                market_cap=peer.market_cap,
                pe_ratio=ratios.get("pe_ratio"),
                ev_ebitda=ratios.get("ev_ebitda"),
                price_to_book=ratios.get("price_to_book"),
                revenue_growth=ratios.get("revenue_growth"),
            )
        )

    return comp_list
