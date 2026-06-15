"""
DataOrchestrator — coordinates multi-source financial data ingestion.

Fetch priority (highest trust first):
  1. SEC EDGAR  — primary source, regulatory filings, highest trust
  2. FMP        — structured financials, good coverage
  3. Yahoo      — fallback for prices and basic info
  5. News       — supplementary context only (Priority 5, never analytical basis)

The orchestrator attempts to populate every field from the highest-trust
available source, falling back gracefully when a source is unavailable or
returns an error.

A `data_quality_score` (0–100) is computed based on field completeness and
the trust level of the sources used. Analysis should be gated on this score.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from . import edgar, fmp, news, yahoo
from .exceptions import DataFetchError, InsufficientDataError, RateLimitError

logger = logging.getLogger(__name__)

# Minimum quality score required to proceed with analysis.
# Callers can override this threshold when calling fetch_company_data.
DEFAULT_MIN_QUALITY_SCORE = 30.0

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class DataSourceEntry:
    """Records which source provided a particular piece of data."""

    source: str
    trust_level: str  # "high", "medium", "low"
    fields_provided: list[str] = field(default_factory=list)


@dataclass
class CompanyDataBundle:
    """
    Aggregated company data from all available sources.

    Fields are populated in trust-priority order. Missing fields are recorded
    in `missing_data_fields`. The `data_quality_score` (0–100) reflects how
    complete and trustworthy the data is.
    """

    # ---- Company identity / profile ----
    company_profile: dict[str, Any] = field(default_factory=dict)

    # ---- Financial statements ----
    income_statements: list[dict[str, Any]] = field(default_factory=list)
    balance_sheets: list[dict[str, Any]] = field(default_factory=list)
    cash_flow_statements: list[dict[str, Any]] = field(default_factory=list)

    # ---- SEC filings ----
    sec_filings: list[dict[str, Any]] = field(default_factory=list)
    latest_10k: dict[str, Any] = field(default_factory=dict)
    latest_10q: dict[str, Any] = field(default_factory=dict)
    company_facts: dict[str, Any] = field(default_factory=dict)
    insider_transactions: list[dict[str, Any]] = field(default_factory=list)
    proxy_data: dict[str, Any] = field(default_factory=dict)

    # ---- Market data ----
    current_price: float | None = None
    historical_prices: list[dict[str, Any]] = field(default_factory=list)

    # ---- News ----
    recent_news: list[dict[str, Any]] = field(default_factory=list)

    # ---- Quality metadata ----
    data_quality_score: float = 0.0
    data_sources_used: list[DataSourceEntry] = field(default_factory=list)
    missing_data_fields: list[str] = field(default_factory=list)
    fetched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ---- Ticker / CIK ----
    ticker: str = ""
    cik: str = ""


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

# Weights for quality score calculation (must sum to 100)
_FIELD_WEIGHTS: dict[str, float] = {
    "company_profile": 10.0,
    "income_statements": 20.0,
    "balance_sheets": 15.0,
    "cash_flow_statements": 15.0,
    "sec_filings": 10.0,
    "latest_10k": 10.0,
    "latest_10q": 5.0,
    "company_facts": 5.0,
    "insider_transactions": 5.0,
    "proxy_data": 5.0,
}

_TRUST_MULTIPLIERS: dict[str, float] = {
    "edgar": 1.0,
    "fmp": 0.9,
    "yahoo": 0.75,
    "news": 0.0,  # News never contributes to quality score
}


def _compute_quality_score(
    bundle: CompanyDataBundle,
    sources: dict[str, str],  # field_name -> source_name
) -> float:
    """
    Compute the data quality score (0–100) based on which fields are populated
    and which source provided them.

    `sources` maps field names to the name of the source that provided them
    (e.g. {"income_statements": "fmp", "latest_10k": "edgar"}).
    """
    score = 0.0
    for field_name, weight in _FIELD_WEIGHTS.items():
        value = getattr(bundle, field_name, None)
        is_populated = bool(value)
        if is_populated:
            source_name = sources.get(field_name, "unknown")
            multiplier = _TRUST_MULTIPLIERS.get(source_name, 0.5)
            score += weight * multiplier
    return min(round(score, 1), 100.0)


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class DataOrchestrator:
    """
    Coordinates data fetching from EDGAR, FMP, Yahoo Finance, and news sources.

    Usage:
        orchestrator = DataOrchestrator()
        bundle = await orchestrator.fetch_company_data(ticker="AAPL", cik="0000320193")
    """

    async def fetch_company_data(
        self,
        ticker: str,
        cik: str | None = None,
        min_quality_score: float = DEFAULT_MIN_QUALITY_SCORE,
        raise_on_insufficient_data: bool = False,
    ) -> CompanyDataBundle:
        """
        Fetch all available financial data for a company from all sources.

        Attempts sources in trust-priority order:
          1. SEC EDGAR (CIK required for EDGAR; auto-resolved from ticker if not provided)
          2. FMP (fills gaps in financials and profile)
          3. Yahoo Finance (price data and basic info fallback)
          5. News (always last; supplementary context only)

        Args:
            ticker: Stock ticker symbol (e.g. "AAPL"). Required.
            cik: SEC Central Index Key. If None, an attempt is made to resolve
                 it from the ticker via EDGAR's company tickers JSON.
            min_quality_score: Threshold below which InsufficientDataError is
                 raised (only when raise_on_insufficient_data=True).
            raise_on_insufficient_data: If True, raises InsufficientDataError
                 when the computed quality score is below min_quality_score.

        Returns:
            CompanyDataBundle with all fetched data and quality metadata.

        Raises:
            InsufficientDataError: only when raise_on_insufficient_data=True and
                 quality score < min_quality_score.
        """
        ticker = ticker.upper().strip()
        bundle = CompanyDataBundle(ticker=ticker, cik=cik or "")
        sources_used: dict[str, str] = {}  # field_name -> source_name
        source_entries: list[DataSourceEntry] = []

        # ------------------------------------------------------------------ #
        # Step 0: Resolve CIK from ticker if not provided                     #
        # ------------------------------------------------------------------ #
        if not cik:
            cik = await self._resolve_cik(ticker)
            bundle.cik = cik or ""

        resolved_cik = bundle.cik

        # ------------------------------------------------------------------ #
        # Step 1: EDGAR — highest-trust source                                #
        # ------------------------------------------------------------------ #
        edgar_fields: list[str] = []
        edgar_errors: list[str] = []

        if resolved_cik:
            edgar_results = await self._fetch_edgar(resolved_cik, ticker)

            if edgar_results.get("company_facts"):
                bundle.company_facts = edgar_results["company_facts"]
                sources_used["company_facts"] = "edgar"
                edgar_fields.append("company_facts")

            if edgar_results.get("sec_filings"):
                bundle.sec_filings = edgar_results["sec_filings"]
                sources_used["sec_filings"] = "edgar"
                edgar_fields.append("sec_filings")

            if edgar_results.get("latest_10k"):
                bundle.latest_10k = edgar_results["latest_10k"]
                sources_used["latest_10k"] = "edgar"
                edgar_fields.append("latest_10k")

            if edgar_results.get("latest_10q"):
                bundle.latest_10q = edgar_results["latest_10q"]
                sources_used["latest_10q"] = "edgar"
                edgar_fields.append("latest_10q")

            if edgar_results.get("insider_transactions"):
                bundle.insider_transactions = edgar_results["insider_transactions"]
                sources_used["insider_transactions"] = "edgar"
                edgar_fields.append("insider_transactions")

            if edgar_results.get("proxy_data"):
                bundle.proxy_data = edgar_results["proxy_data"]
                sources_used["proxy_data"] = "edgar"
                edgar_fields.append("proxy_data")

            edgar_errors = edgar_results.get("errors", [])
        else:
            logger.warning(
                "No CIK resolved for %s — skipping all EDGAR data.", ticker
            )
            edgar_errors.append("Could not resolve CIK from ticker; EDGAR data skipped.")

        if edgar_fields:
            source_entries.append(
                DataSourceEntry(
                    source="edgar",
                    trust_level="high",
                    fields_provided=edgar_fields,
                )
            )

        # ------------------------------------------------------------------ #
        # Step 2: FMP — structured financials and profile                     #
        # ------------------------------------------------------------------ #
        fmp_fields: list[str] = []
        fmp_results = await self._fetch_fmp(ticker)

        if fmp_results.get("company_profile") and not bundle.company_profile:
            bundle.company_profile = fmp_results["company_profile"]
            sources_used["company_profile"] = "fmp"
            fmp_fields.append("company_profile")

        if fmp_results.get("income_statements"):
            bundle.income_statements = fmp_results["income_statements"]
            sources_used["income_statements"] = "fmp"
            fmp_fields.append("income_statements")

        if fmp_results.get("balance_sheets"):
            bundle.balance_sheets = fmp_results["balance_sheets"]
            sources_used["balance_sheets"] = "fmp"
            fmp_fields.append("balance_sheets")

        if fmp_results.get("cash_flow_statements"):
            bundle.cash_flow_statements = fmp_results["cash_flow_statements"]
            sources_used["cash_flow_statements"] = "fmp"
            fmp_fields.append("cash_flow_statements")

        if fmp_fields:
            source_entries.append(
                DataSourceEntry(
                    source="fmp",
                    trust_level="medium",
                    fields_provided=fmp_fields,
                )
            )

        # ------------------------------------------------------------------ #
        # Step 3: Yahoo Finance — price data and profile fallback             #
        # ------------------------------------------------------------------ #
        yahoo_fields: list[str] = []
        yahoo_results = await self._fetch_yahoo(ticker)

        if yahoo_results.get("stock_info") and not bundle.company_profile:
            # Use Yahoo info to populate a minimal profile when FMP unavailable
            raw_info = yahoo_results["stock_info"]
            bundle.company_profile = {
                "symbol": ticker,
                "companyName": raw_info.get("longName", ""),
                "sector": raw_info.get("sector", ""),
                "industry": raw_info.get("industry", ""),
                "mktCap": raw_info.get("marketCap"),
                "website": raw_info.get("website", ""),
                "description": raw_info.get("longBusinessSummary", ""),
                "source": "yahoo",
            }
            sources_used["company_profile"] = "yahoo"
            yahoo_fields.append("company_profile")

        if yahoo_results.get("current_price") is not None:
            bundle.current_price = yahoo_results["current_price"]
            yahoo_fields.append("current_price")

        if yahoo_results.get("historical_prices"):
            bundle.historical_prices = yahoo_results["historical_prices"]
            yahoo_fields.append("historical_prices")

        if yahoo_fields:
            source_entries.append(
                DataSourceEntry(
                    source="yahoo",
                    trust_level="medium",
                    fields_provided=yahoo_fields,
                )
            )

        # ------------------------------------------------------------------ #
        # Step 5: News — supplementary context only                           #
        # ------------------------------------------------------------------ #
        company_name = bundle.company_profile.get("companyName", ticker)
        news_items = await self._fetch_news(ticker=ticker, company_name=company_name)
        if news_items:
            bundle.recent_news = news_items
            source_entries.append(
                DataSourceEntry(
                    source="news",
                    trust_level="low",
                    fields_provided=["recent_news"],
                )
            )

        # ------------------------------------------------------------------ #
        # Compute quality score and missing fields                            #
        # ------------------------------------------------------------------ #
        bundle.data_sources_used = source_entries

        all_tracked_fields = list(_FIELD_WEIGHTS.keys())
        missing: list[str] = []
        for f_name in all_tracked_fields:
            val = getattr(bundle, f_name, None)
            if not val:
                missing.append(f_name)

        bundle.missing_data_fields = missing + edgar_errors
        bundle.data_quality_score = _compute_quality_score(bundle, sources_used)
        bundle.fetched_at = datetime.now(timezone.utc).isoformat()

        logger.info(
            "DataOrchestrator: completed fetch for %s | quality=%.1f | "
            "sources=%s | missing=%s",
            ticker,
            bundle.data_quality_score,
            [e.source for e in source_entries],
            missing,
        )

        if raise_on_insufficient_data and bundle.data_quality_score < min_quality_score:
            raise InsufficientDataError(
                f"Data quality score {bundle.data_quality_score:.1f} is below the "
                f"minimum threshold of {min_quality_score:.1f} for ticker '{ticker}'. "
                "Insufficient data to support a meaningful analysis.",
                quality_score=bundle.data_quality_score,
                missing_fields=missing,
            )

        return bundle

    # ---------------------------------------------------------------------- #
    # Private fetch helpers                                                   #
    # ---------------------------------------------------------------------- #

    async def _resolve_cik(self, ticker: str) -> str | None:
        """
        Attempt to resolve a CIK from a ticker using EDGAR's company tickers
        mapping.  Returns None on failure (non-fatal).
        """
        try:
            import httpx as _httpx

            async with _httpx.AsyncClient(
                headers={"User-Agent": "AI Research Platform research@example.com"},
                timeout=_httpx.Timeout(15.0),
            ) as client:
                resp = await client.get(
                    "https://data.sec.gov/files/company_tickers.json"
                )
            if resp.status_code == 200:
                tickers_data = resp.json()
                ticker_upper = ticker.upper()
                for _idx, company in tickers_data.items():
                    if company.get("ticker", "").upper() == ticker_upper:
                        return str(company["cik_str"]).zfill(10)
        except Exception as exc:
            logger.warning("CIK resolution failed for %s: %s", ticker, exc)
        return None

    async def _fetch_edgar(
        self, cik: str, ticker: str
    ) -> dict[str, Any]:
        """
        Fetch all EDGAR data for a CIK concurrently.

        Returns a dict of fetched data keyed by field name, plus an "errors"
        list of non-fatal error messages.
        """
        results: dict[str, Any] = {"errors": []}

        async def _safe(coro_fn: Any, key: str, *args: Any, **kwargs: Any) -> None:
            try:
                results[key] = await coro_fn(*args, **kwargs)
            except (DataFetchError, RateLimitError) as exc:
                logger.warning("EDGAR fetch failed for %s (%s): %s", key, cik, exc)
                results["errors"].append(f"edgar.{key}: {exc}")
            except Exception as exc:
                logger.error(
                    "Unexpected error fetching edgar.%s for CIK %s: %s",
                    key,
                    cik,
                    exc,
                    exc_info=True,
                )
                results["errors"].append(f"edgar.{key}: unexpected error: {exc}")

        # Run all EDGAR calls concurrently (EDGAR rate limiting is handled
        # inside each function via the module-level semaphore and lock).
        await asyncio.gather(
            _safe(edgar.get_company_facts, "company_facts", cik),
            _safe(edgar.get_company_submissions, "company_submissions", cik),
            _safe(edgar.get_latest_10k, "latest_10k", cik),
            _safe(edgar.get_latest_10q, "latest_10q", cik),
            _safe(edgar.get_8k_filings, "sec_filings", cik, 20),
            _safe(edgar.get_insider_transactions, "insider_transactions", cik),
            _safe(edgar.get_proxy_statement, "proxy_data", cik),
            return_exceptions=False,
        )

        return results

    async def _fetch_fmp(self, ticker: str) -> dict[str, Any]:
        """
        Fetch structured financial data from FMP concurrently.

        Returns a dict of fetched data keyed by field name. Missing/failed
        fields are omitted (non-fatal).
        """
        results: dict[str, Any] = {}

        async def _safe(coro_fn: Any, key: str, *args: Any, **kwargs: Any) -> None:
            try:
                results[key] = await coro_fn(*args, **kwargs)
            except DataFetchError as exc:
                logger.warning("FMP fetch failed for %s (%s): %s", key, ticker, exc)
            except Exception as exc:
                logger.error(
                    "Unexpected error fetching fmp.%s for %s: %s",
                    key,
                    ticker,
                    exc,
                    exc_info=True,
                )

        await asyncio.gather(
            _safe(fmp.get_company_profile, "company_profile", ticker),
            _safe(fmp.get_income_statement, "income_statements", ticker, "annual", 5),
            _safe(fmp.get_balance_sheet, "balance_sheets", ticker, "annual", 5),
            _safe(fmp.get_cash_flow, "cash_flow_statements", ticker, "annual", 5),
            return_exceptions=False,
        )

        return results

    async def _fetch_yahoo(self, ticker: str) -> dict[str, Any]:
        """
        Fetch Yahoo Finance data concurrently.

        Returns a dict of fetched data keyed by field name. Missing/failed
        fields are omitted (non-fatal).
        """
        results: dict[str, Any] = {}

        async def _safe(coro_fn: Any, key: str, *args: Any, **kwargs: Any) -> None:
            try:
                results[key] = await coro_fn(*args, **kwargs)
            except DataFetchError as exc:
                logger.warning("Yahoo fetch failed for %s (%s): %s", key, ticker, exc)
            except Exception as exc:
                logger.error(
                    "Unexpected error fetching yahoo.%s for %s: %s",
                    key,
                    ticker,
                    exc,
                    exc_info=True,
                )

        await asyncio.gather(
            _safe(yahoo.get_stock_info, "stock_info", ticker),
            _safe(yahoo.get_current_price, "current_price", ticker),
            _safe(yahoo.get_historical_prices, "historical_prices", ticker, "1y"),
            return_exceptions=False,
        )

        return results

    async def _fetch_news(
        self, ticker: str, company_name: str
    ) -> list[dict[str, Any]]:
        """
        Fetch supplementary news. Non-fatal — returns [] on any failure.
        """
        try:
            return await news.get_company_news(
                ticker=ticker, company_name=company_name, limit=20
            )
        except Exception as exc:
            logger.warning("News fetch failed for %s: %s", ticker, exc)
            return []
