"""Initial schema — create all tables.

Revision ID: 001
Revises:
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(1024), nullable=False),
        sa.Column("full_name", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # companies
    # ------------------------------------------------------------------
    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("ticker", sa.String(20), nullable=False, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("sector", sa.String(200), nullable=True),
        sa.Column("industry", sa.String(200), nullable=True),
        sa.Column("exchange", sa.String(50), nullable=True),
        sa.Column("market_cap", sa.Float(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cik", sa.String(20), nullable=True),
        sa.Column("isin", sa.String(20), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("employees", sa.Integer(), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_companies_ticker", "companies", ["ticker"], unique=True)
    op.create_index("ix_companies_cik", "companies", ["cik"])
    op.create_index("ix_companies_isin", "companies", ["isin"])
    op.create_index("ix_companies_sector_industry", "companies", ["sector", "industry"])
    op.create_index("ix_companies_exchange", "companies", ["exchange"])

    # ------------------------------------------------------------------
    # financial_statements
    # ------------------------------------------------------------------
    op.create_table(
        "financial_statements",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("fiscal_quarter", sa.Integer(), nullable=True),
        sa.Column(
            "statement_type",
            sa.Enum("income", "balance", "cashflow", name="statementtype"),
            nullable=False,
        ),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("filing_url", sa.String(1000), nullable=True),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "company_id", "period", "statement_type", name="uq_financial_statement"
        ),
    )
    op.create_index(
        "ix_financial_statements_company_period",
        "financial_statements",
        ["company_id", "period"],
    )
    op.create_index(
        "ix_financial_statements_fiscal_year",
        "financial_statements",
        ["company_id", "fiscal_year"],
    )

    # ------------------------------------------------------------------
    # financial_ratios
    # ------------------------------------------------------------------
    op.create_table(
        "financial_ratios",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("ratio_name", sa.String(100), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("source_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint("company_id", "period", "ratio_name", name="uq_financial_ratio"),
    )
    op.create_index(
        "ix_financial_ratios_company_period",
        "financial_ratios",
        ["company_id", "period"],
    )
    op.create_index("ix_financial_ratios_ratio_name", "financial_ratios", ["ratio_name"])

    # ------------------------------------------------------------------
    # sec_filings
    # ------------------------------------------------------------------
    op.create_table(
        "sec_filings",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("form_type", sa.String(50), nullable=False),
        sa.Column("filed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_of_report", sa.String(20), nullable=True),
        sa.Column("filing_url", sa.String(1000), nullable=True),
        sa.Column("document_url", sa.String(1000), nullable=True),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_sec_filings_company_form", "sec_filings", ["company_id", "form_type"])
    op.create_index("ix_sec_filings_filed_at", "sec_filings", ["filed_at"])
    op.create_index("ix_sec_filings_processed", "sec_filings", ["processed"])

    # ------------------------------------------------------------------
    # governance_data
    # ------------------------------------------------------------------
    op.create_table(
        "governance_data",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("board_size", sa.Integer(), nullable=True),
        sa.Column("independent_directors", sa.Integer(), nullable=True),
        sa.Column("ceo_chairman_combined", sa.Boolean(), nullable=True),
        sa.Column("insider_ownership_pct", sa.Float(), nullable=True),
        sa.Column("institutional_ownership_pct", sa.Float(), nullable=True),
        sa.Column("executive_comp_total", sa.Float(), nullable=True),
        sa.Column("has_poison_pill", sa.Boolean(), nullable=True),
        sa.Column("has_dual_class", sa.Boolean(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "source_filing_id",
            sa.Integer(),
            sa.ForeignKey("sec_filings.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("company_id", "period", name="uq_governance_data"),
    )
    op.create_index(
        "ix_governance_data_company_period",
        "governance_data",
        ["company_id", "period"],
    )

    # ------------------------------------------------------------------
    # valuation_models
    # ------------------------------------------------------------------
    op.create_table(
        "valuation_models",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "model_type",
            sa.Enum("dcf", "comparable", "ddm", "residual_income", "asset_based", name="modeltype"),
            nullable=False,
        ),
        sa.Column("assumptions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("results", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_valuation_models_company_type", "valuation_models", ["company_id", "model_type"]
    )

    # ------------------------------------------------------------------
    # research_reports
    # ------------------------------------------------------------------
    op.create_table(
        "research_reports",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("report_type", sa.String(100), nullable=False, server_default="full"),
        sa.Column(
            "status",
            sa.Enum("draft", "generating", "completed", "failed", name="reportstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("pdf_path", sa.String(1000), nullable=True),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_research_reports_ticker", "research_reports", ["ticker"])
    op.create_index(
        "ix_research_reports_company_status",
        "research_reports",
        ["company_id", "status"],
    )
    op.create_index("ix_research_reports_created_at", "research_reports", ["created_at"])

    # ------------------------------------------------------------------
    # user_watchlists
    # ------------------------------------------------------------------
    op.create_table(
        "user_watchlists",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.UniqueConstraint("user_id", "company_id", name="uq_user_watchlist"),
    )
    op.create_index("ix_user_watchlists_user_id", "user_watchlists", ["user_id"])

    # ------------------------------------------------------------------
    # analysis_jobs
    # ------------------------------------------------------------------
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "company_id",
            sa.Integer(),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", "cancelled", name="jobstatus"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_analysis_jobs_status", "analysis_jobs", ["status"])
    op.create_index("ix_analysis_jobs_job_type", "analysis_jobs", ["job_type"])
    op.create_index("ix_analysis_jobs_created_at", "analysis_jobs", ["created_at"])
    op.create_index("ix_analysis_jobs_company_id", "analysis_jobs", ["company_id"])


def downgrade() -> None:
    op.drop_table("analysis_jobs")
    op.drop_table("user_watchlists")
    op.drop_table("research_reports")
    op.drop_table("valuation_models")
    op.drop_table("governance_data")
    op.drop_table("sec_filings")
    op.drop_table("financial_ratios")
    op.drop_table("financial_statements")
    op.drop_table("companies")
    op.drop_table("users")

    # Drop custom enum types
    sa.Enum(name="jobstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="reportstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="modeltype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="statementtype").drop(op.get_bind(), checkfirst=True)
