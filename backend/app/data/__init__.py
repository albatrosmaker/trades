"""
backend.app.data — Primary source financial data ingestion layer.

Sources (by trust priority):
  1. SEC EDGAR  — regulatory filings, highest trust  (edgar.py)
  2. FMP        — structured financials               (fmp.py)
  3. Yahoo      — price data fallback                 (yahoo.py)
  5. News       — supplementary context ONLY          (news.py)

Entry point for callers:
    from backend.app.data.data_orchestrator import DataOrchestrator
    bundle = await DataOrchestrator().fetch_company_data(ticker="AAPL")
"""

from .data_orchestrator import CompanyDataBundle, DataOrchestrator, DataSourceEntry
from .exceptions import (
    DataFetchError,
    DataQualityError,
    InsufficientDataError,
    RateLimitError,
)

__all__ = [
    # Orchestrator
    "DataOrchestrator",
    "CompanyDataBundle",
    "DataSourceEntry",
    # Exceptions
    "DataFetchError",
    "RateLimitError",
    "DataQualityError",
    "InsufficientDataError",
]
