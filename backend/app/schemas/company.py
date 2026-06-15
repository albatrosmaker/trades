from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, field_validator


# ---------------------------------------------------------------------------
# Company schemas
# ---------------------------------------------------------------------------

class CompanyBase(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    market_cap: Optional[float] = None
    description: Optional[str] = None
    cik: Optional[str] = None
    isin: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[int] = None
    country: Optional[str] = None
    currency: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyRead(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyListItem(BaseModel):
    """Lightweight company representation for list/search results."""
    id: int
    ticker: str
    name: str
    sector: Optional[str] = None
    exchange: Optional[str] = None
    market_cap: Optional[float] = None
    country: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Financial statement schemas
# ---------------------------------------------------------------------------

class FinancialStatementRead(BaseModel):
    id: int
    company_id: int
    period: str
    fiscal_year: int
    fiscal_quarter: Optional[int] = None
    statement_type: str
    data: dict[str, Any]
    source: Optional[str] = None
    filing_url: Optional[str] = None
    filed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Financial ratio schemas
# ---------------------------------------------------------------------------

class FinancialRatioRead(BaseModel):
    id: int
    company_id: int
    period: str
    ratio_name: str
    value: Optional[float] = None
    calculated_at: datetime
    source_data: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# SEC filing schemas
# ---------------------------------------------------------------------------

class SECFilingRead(BaseModel):
    id: int
    company_id: int
    form_type: str
    filed_at: datetime
    period_of_report: Optional[str] = None
    filing_url: Optional[str] = None
    document_url: Optional[str] = None
    processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Governance schemas
# ---------------------------------------------------------------------------

class GovernanceDataRead(BaseModel):
    id: int
    company_id: int
    period: str
    board_size: Optional[int] = None
    independent_directors: Optional[int] = None
    ceo_chairman_combined: Optional[bool] = None
    insider_ownership_pct: Optional[float] = None
    institutional_ownership_pct: Optional[float] = None
    executive_comp_total: Optional[float] = None
    has_poison_pill: Optional[bool] = None
    has_dual_class: Optional[bool] = None
    data: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Research report schemas
# ---------------------------------------------------------------------------

class ResearchReportCreate(BaseModel):
    ticker: str
    report_type: str = "full"
    dcf_assumptions: Optional[dict[str, Any]] = None

    @field_validator("ticker")
    @classmethod
    def ticker_upper(cls, v: str) -> str:
        return v.upper().strip()


class ResearchReportRead(BaseModel):
    id: int
    company_id: int
    ticker: str
    report_type: str
    status: str
    # All analysis sections are stored inside the `content` JSONB blob.
    # Convenience accessors surface top-level keys when present.
    content: Optional[dict[str, Any]] = None
    pdf_path: Optional[str] = None
    error_message: Optional[str] = None
    created_by_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    # Virtual fields derived from content for API ergonomics
    @property
    def financial_analysis(self) -> Optional[dict[str, Any]]:
        return (self.content or {}).get("financial_analysis")

    @property
    def governance_analysis(self) -> Optional[dict[str, Any]]:
        return (self.content or {}).get("governance_analysis")

    @property
    def valuation_analysis(self) -> Optional[dict[str, Any]]:
        return (self.content or {}).get("valuation_analysis")

    @property
    def risk_analysis(self) -> Optional[dict[str, Any]]:
        return (self.content or {}).get("risk_analysis")

    @property
    def investment_committee(self) -> Optional[dict[str, Any]]:
        return (self.content or {}).get("investment_committee")

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Watchlist schemas
# ---------------------------------------------------------------------------

class WatchlistAdd(BaseModel):
    ticker: str
    notes: Optional[str] = None

    @field_validator("ticker")
    @classmethod
    def ticker_upper(cls, v: str) -> str:
        return v.upper().strip()


class WatchlistItemRead(BaseModel):
    id: int
    user_id: int
    company_id: int
    added_at: datetime
    notes: Optional[str] = None
    company: Optional[CompanyListItem] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Valuation schemas
# ---------------------------------------------------------------------------

class DCFAssumptions(BaseModel):
    wacc: float
    terminal_growth_rate: float
    projection_years: int
    revenue_growth_rates: Optional[list[float]] = None
    ebitda_margins: Optional[list[float]] = None
    capex_pct_revenue: Optional[float] = None
    nwc_pct_revenue: Optional[float] = None
    tax_rate: Optional[float] = None
    debt: Optional[float] = None
    cash: Optional[float] = None
    shares_outstanding: Optional[float] = None

    @field_validator("projection_years")
    @classmethod
    def validate_years(cls, v: int) -> int:
        if not (1 <= v <= 30):
            raise ValueError("projection_years must be between 1 and 30")
        return v

    @field_validator("wacc", "terminal_growth_rate")
    @classmethod
    def validate_rates(cls, v: float) -> float:
        if not (0 < v < 1):
            raise ValueError("Rate must be between 0 and 1 (e.g. 0.10 for 10%)")
        return v


class DCFResult(BaseModel):
    ticker: str
    assumptions: DCFAssumptions
    intrinsic_value_per_share: Optional[float] = None
    enterprise_value: Optional[float] = None
    equity_value: Optional[float] = None
    current_price: Optional[float] = None
    upside_downside_pct: Optional[float] = None
    projected_fcf: Optional[list[float]] = None
    terminal_value: Optional[float] = None
    pv_fcf: Optional[float] = None
    pv_terminal_value: Optional[float] = None
    model_id: Optional[int] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Analysis job schemas
# ---------------------------------------------------------------------------

class AnalysisJobRead(BaseModel):
    id: int
    company_id: Optional[int] = None
    job_type: str
    status: str
    result: Optional[dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Peer / comps schemas
# ---------------------------------------------------------------------------

class PeerCompanyRead(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    price_to_book: Optional[float] = None
    revenue_growth: Optional[float] = None
