from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    Enum as SAEnum, Index, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class StatementType(str, enum.Enum):
    INCOME = "income"
    BALANCE = "balance"
    CASHFLOW = "cashflow"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelType(str, enum.Enum):
    DCF = "dcf"
    COMPARABLE = "comparable"
    DDM = "ddm"
    RESIDUAL_INCOME = "residual_income"
    ASSET_BASED = "asset_based"


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    sector: Mapped[Optional[str]] = mapped_column(String(200))
    industry: Mapped[Optional[str]] = mapped_column(String(200))
    exchange: Mapped[Optional[str]] = mapped_column(String(50))
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cik: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    isin: Mapped[Optional[str]] = mapped_column(String(20), index=True)
    website: Mapped[Optional[str]] = mapped_column(String(500))
    employees: Mapped[Optional[int]] = mapped_column(Integer)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    currency: Mapped[Optional[str]] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    financial_statements: Mapped[list["FinancialStatement"]] = relationship(
        "FinancialStatement", back_populates="company", cascade="all, delete-orphan"
    )
    financial_ratios: Mapped[list["FinancialRatio"]] = relationship(
        "FinancialRatio", back_populates="company", cascade="all, delete-orphan"
    )
    sec_filings: Mapped[list["SECFiling"]] = relationship(
        "SECFiling", back_populates="company", cascade="all, delete-orphan"
    )
    governance_data: Mapped[list["GovernanceData"]] = relationship(
        "GovernanceData", back_populates="company", cascade="all, delete-orphan"
    )
    valuation_models: Mapped[list["ValuationModel"]] = relationship(
        "ValuationModel", back_populates="company", cascade="all, delete-orphan"
    )
    research_reports: Mapped[list["ResearchReport"]] = relationship(
        "ResearchReport", back_populates="company", cascade="all, delete-orphan"
    )
    watchlist_entries: Mapped[list["UserWatchlist"]] = relationship(
        "UserWatchlist", back_populates="company", cascade="all, delete-orphan"
    )
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship(
        "AnalysisJob", back_populates="company", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_companies_sector_industry", "sector", "industry"),
        Index("ix_companies_exchange", "exchange"),
    )

    def __repr__(self) -> str:
        return f"<Company(ticker={self.ticker}, name={self.name})>"


class FinancialStatement(Base):
    __tablename__ = "financial_statements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2023-Q4", "2023-FY"
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_quarter: Mapped[Optional[int]] = mapped_column(Integer)  # 1-4, None for annual
    statement_type: Mapped[StatementType] = mapped_column(
        SAEnum(StatementType), nullable=False
    )
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    filing_url: Mapped[Optional[str]] = mapped_column(String(1000))
    filed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="financial_statements")

    __table_args__ = (
        UniqueConstraint("company_id", "period", "statement_type", name="uq_financial_statement"),
        Index("ix_financial_statements_company_period", "company_id", "period"),
        Index("ix_financial_statements_fiscal_year", "company_id", "fiscal_year"),
    )

    def __repr__(self) -> str:
        return f"<FinancialStatement(company_id={self.company_id}, period={self.period}, type={self.statement_type})>"


class FinancialRatio(Base):
    __tablename__ = "financial_ratios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    ratio_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[Optional[float]] = mapped_column(Float)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="financial_ratios")

    __table_args__ = (
        UniqueConstraint("company_id", "period", "ratio_name", name="uq_financial_ratio"),
        Index("ix_financial_ratios_company_period", "company_id", "period"),
        Index("ix_financial_ratios_ratio_name", "ratio_name"),
    )

    def __repr__(self) -> str:
        return f"<FinancialRatio(company_id={self.company_id}, period={self.period}, ratio={self.ratio_name})>"


class SECFiling(Base):
    __tablename__ = "sec_filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    form_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "10-K", "10-Q", "8-K"
    filed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    period_of_report: Mapped[Optional[str]] = mapped_column(String(20))
    filing_url: Mapped[Optional[str]] = mapped_column(String(1000))
    document_url: Mapped[Optional[str]] = mapped_column(String(1000))
    processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    content_text: Mapped[Optional[str]] = mapped_column(Text)
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="sec_filings")
    governance_entries: Mapped[list["GovernanceData"]] = relationship(
        "GovernanceData", back_populates="source_filing"
    )

    __table_args__ = (
        Index("ix_sec_filings_company_form", "company_id", "form_type"),
        Index("ix_sec_filings_filed_at", "filed_at"),
        Index("ix_sec_filings_processed", "processed"),
    )

    def __repr__(self) -> str:
        return f"<SECFiling(company_id={self.company_id}, form={self.form_type}, filed={self.filed_at})>"


class GovernanceData(Base):
    __tablename__ = "governance_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    board_size: Mapped[Optional[int]] = mapped_column(Integer)
    independent_directors: Mapped[Optional[int]] = mapped_column(Integer)
    ceo_chairman_combined: Mapped[Optional[bool]] = mapped_column(Boolean)
    insider_ownership_pct: Mapped[Optional[float]] = mapped_column(Float)
    institutional_ownership_pct: Mapped[Optional[float]] = mapped_column(Float)
    executive_comp_total: Mapped[Optional[float]] = mapped_column(Float)
    has_poison_pill: Mapped[Optional[bool]] = mapped_column(Boolean)
    has_dual_class: Mapped[Optional[bool]] = mapped_column(Boolean)
    data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    source_filing_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("sec_filings.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="governance_data")
    source_filing: Mapped[Optional["SECFiling"]] = relationship(
        "SECFiling", back_populates="governance_entries"
    )

    __table_args__ = (
        UniqueConstraint("company_id", "period", name="uq_governance_data"),
        Index("ix_governance_data_company_period", "company_id", "period"),
    )

    def __repr__(self) -> str:
        return f"<GovernanceData(company_id={self.company_id}, period={self.period})>"


class ValuationModel(Base):
    __tablename__ = "valuation_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_type: Mapped[ModelType] = mapped_column(SAEnum(ModelType), nullable=False)
    assumptions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    results: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="valuation_models")

    __table_args__ = (
        Index("ix_valuation_models_company_type", "company_id", "model_type"),
    )

    def __repr__(self) -> str:
        return f"<ValuationModel(company_id={self.company_id}, type={self.model_type})>"


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ticker: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False)  # initiation, update, deep_dive
    status: Mapped[ReportStatus] = mapped_column(
        SAEnum(ReportStatus), nullable=False, default=ReportStatus.DRAFT
    )
    content: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(1000))
    created_by_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="research_reports")

    __table_args__ = (
        Index("ix_research_reports_company_status", "company_id", "status"),
        Index("ix_research_reports_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ResearchReport(company_id={self.company_id}, type={self.report_type}, status={self.status})>"


class UserWatchlist(Base):
    __tablename__ = "user_watchlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    company: Mapped["Company"] = relationship("Company", back_populates="watchlist_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_watchlist"),
        Index("ix_user_watchlists_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserWatchlist(user_id={self.user_id}, company_id={self.company_id})>"


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    company_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), nullable=False, default=JobStatus.PENDING
    )
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="analysis_jobs")

    __table_args__ = (
        Index("ix_analysis_jobs_status", "status"),
        Index("ix_analysis_jobs_job_type", "job_type"),
        Index("ix_analysis_jobs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AnalysisJob(id={self.id}, type={self.job_type}, status={self.status})>"
