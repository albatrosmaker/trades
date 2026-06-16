"""
Financial Modeling Prep (FMP) API client.

Priority 2 data source — used to fill gaps when EDGAR data is unavailable or
insufficient.

Base URL: https://financialmodelingprep.com/api/v3/

The FMP API key is read from the environment variable FMP_API_KEY.
All functions raise DataFetchError if the key is missing or requests fail.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from .exceptions import DataFetchError, RateLimitError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
_MAX_RETRIES = 3
_BACKOFF_BASE = 2.0  # seconds
_USER_AGENT = "AI Research Platform research@example.com"

# FMP free tier is 250 calls/day; paid tiers vary. We conservatively cap at
# 5 req/sec to avoid hitting burst limits.
_RATE_SEMAPHORE = asyncio.Semaphore(5)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """
    Return the FMP API key from the environment.

    Raises:
        DataFetchError: if FMP_API_KEY is not set.
    """
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        raise DataFetchError(
            "FMP_API_KEY environment variable is not set. "
            "Set it to your Financial Modeling Prep API key.",
            source="fmp",
        )
    return key


def _build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=FMP_BASE_URL,
        headers={"User-Agent": _USER_AGENT},
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
    )


async def _get(
    endpoint: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Perform a GET request to the FMP API with retries and rate limiting.

    Injects the API key automatically.

    Returns:
        Parsed JSON response (list or dict).

    Raises:
        RateLimitError: on HTTP 429 after retries exhausted.
        DataFetchError: on any other error or non-200 response.
    """
    api_key = _get_api_key()
    request_params: dict[str, Any] = {"apikey": api_key}
    if params:
        request_params.update(params)

    last_exc: Exception | None = None

    async with _RATE_SEMAPHORE:
        for attempt in range(_MAX_RETRIES):
            try:
                async with _build_client() as client:
                    response = await client.get(endpoint, params=request_params)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 60))
                    if attempt < _MAX_RETRIES - 1:
                        wait = retry_after or (_BACKOFF_BASE ** (attempt + 1))
                        logger.warning(
                            "FMP rate limited on %s, waiting %.1fs (attempt %d/%d)",
                            endpoint,
                            wait,
                            attempt + 1,
                            _MAX_RETRIES,
                        )
                        await asyncio.sleep(wait)
                        continue
                    raise RateLimitError(
                        f"FMP rate limit exceeded after {_MAX_RETRIES} attempts: {endpoint}",
                        source="fmp",
                        retry_after=retry_after,
                    )

                if response.status_code == 401:
                    raise DataFetchError(
                        f"FMP API key is invalid or expired (HTTP 401): {endpoint}",
                        source="fmp",
                        status_code=401,
                    )

                if response.status_code >= 500 and attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "FMP server error %d on %s, retrying in %.1fs",
                        response.status_code,
                        endpoint,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                if response.status_code != 200:
                    raise DataFetchError(
                        f"FMP returned HTTP {response.status_code} for {endpoint}",
                        source="fmp",
                        status_code=response.status_code,
                    )

                data = response.json()

                # FMP returns {"Error Message": "..."} on bad requests
                if isinstance(data, dict) and "Error Message" in data:
                    raise DataFetchError(
                        f"FMP API error for {endpoint}: {data['Error Message']}",
                        source="fmp",
                    )

                return data

            except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "FMP connection error on %s (%s), retrying in %.1fs",
                        endpoint,
                        exc,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

    raise DataFetchError(
        f"FMP fetch failed after {_MAX_RETRIES} attempts for {endpoint}: {last_exc}",
        source="fmp",
    ) from last_exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_income_statement(
    ticker: str,
    period: str = "annual",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch income statements for a ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        period: "annual" or "quarter".
        limit: Number of periods to return (max depends on FMP plan).

    Returns:
        List of income statement dicts ordered newest-first.
    """
    logger.info("FMP: fetching income statement for %s (%s, limit=%d)", ticker, period, limit)
    data = await _get(
        f"/income-statement/{ticker.upper()}",
        params={"period": period, "limit": limit},
    )
    return data if isinstance(data, list) else []


async def get_balance_sheet(
    ticker: str,
    period: str = "annual",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch balance sheets for a ticker.

    Args:
        ticker: Stock ticker symbol.
        period: "annual" or "quarter".
        limit: Number of periods to return.

    Returns:
        List of balance sheet dicts ordered newest-first.
    """
    logger.info("FMP: fetching balance sheet for %s (%s, limit=%d)", ticker, period, limit)
    data = await _get(
        f"/balance-sheet-statement/{ticker.upper()}",
        params={"period": period, "limit": limit},
    )
    return data if isinstance(data, list) else []


async def get_cash_flow(
    ticker: str,
    period: str = "annual",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """
    Fetch cash flow statements for a ticker.

    Args:
        ticker: Stock ticker symbol.
        period: "annual" or "quarter".
        limit: Number of periods to return.

    Returns:
        List of cash flow statement dicts ordered newest-first.
    """
    logger.info("FMP: fetching cash flow for %s (%s, limit=%d)", ticker, period, limit)
    data = await _get(
        f"/cash-flow-statement/{ticker.upper()}",
        params={"period": period, "limit": limit},
    )
    return data if isinstance(data, list) else []


async def get_key_metrics(
    ticker: str,
    period: str = "annual",
) -> list[dict[str, Any]]:
    """
    Fetch key financial metrics (P/E, EV/EBITDA, FCF yield, etc.) for a ticker.

    Args:
        ticker: Stock ticker symbol.
        period: "annual" or "quarter".

    Returns:
        List of key metrics dicts ordered newest-first.
    """
    logger.info("FMP: fetching key metrics for %s (%s)", ticker, period)
    data = await _get(
        f"/key-metrics/{ticker.upper()}",
        params={"period": period},
    )
    return data if isinstance(data, list) else []


async def get_financial_ratios(ticker: str) -> list[dict[str, Any]]:
    """
    Fetch financial ratios (liquidity, solvency, profitability) for a ticker.

    Returns:
        List of financial ratio dicts ordered newest-first.
    """
    logger.info("FMP: fetching financial ratios for %s", ticker)
    data = await _get(f"/ratios/{ticker.upper()}")
    return data if isinstance(data, list) else []


async def get_company_profile(ticker: str) -> dict[str, Any]:
    """
    Fetch the company profile (name, sector, industry, market cap, description,
    website, CEO, employees, etc.) for a ticker.

    Returns:
        Dict with company profile fields.

    Raises:
        DataFetchError: if no profile is found for the ticker.
    """
    logger.info("FMP: fetching company profile for %s", ticker)
    data = await _get(f"/profile/{ticker.upper()}")
    if isinstance(data, list) and data:
        return data[0]
    raise DataFetchError(
        f"FMP returned no company profile for ticker '{ticker}'",
        source="fmp",
    )


async def get_peers(ticker: str) -> list[str]:
    """
    Fetch the list of peer company tickers for a given ticker.

    Returns:
        List of ticker strings.
    """
    logger.info("FMP: fetching peers for %s", ticker)
    data = await _get(f"/stock_peers", params={"symbol": ticker.upper()})
    if isinstance(data, list) and data:
        return data[0].get("peersList", [])
    return []


async def get_earnings_surprises(ticker: str) -> list[dict[str, Any]]:
    """
    Fetch historical earnings surprises (actual vs. estimated EPS) for a ticker.

    Returns:
        List of earnings surprise dicts with fields: date, actualEarningResult,
        estimatedEarning, symbol.
    """
    logger.info("FMP: fetching earnings surprises for %s", ticker)
    data = await _get(f"/earnings-surprises/{ticker.upper()}")
    return data if isinstance(data, list) else []


async def get_analyst_estimates(ticker: str) -> list[dict[str, Any]]:
    """
    Fetch analyst consensus estimates (revenue, EPS, EBITDA) for a ticker.

    Returns:
        List of analyst estimate dicts ordered by period.
    """
    logger.info("FMP: fetching analyst estimates for %s", ticker)
    data = await _get(f"/analyst-estimates/{ticker.upper()}")
    return data if isinstance(data, list) else []


async def search_ticker(query: str) -> list[dict[str, Any]]:
    """
    Search for tickers and company names matching a query string.

    Args:
        query: Company name or partial ticker.

    Returns:
        List of dicts with keys: symbol, name, currency, stockExchange,
        exchangeShortName.
    """
    logger.info("FMP: searching tickers for '%s'", query)
    data = await _get(
        "/search",
        params={"query": query, "limit": 20},
    )
    return data if isinstance(data, list) else []
