"""
Financial news fetcher.

Priority 5 data source — news is supplementary context ONLY and must NEVER
serve as the basis for investment recommendations or financial analysis.

Each news item is tagged with trust_level="low" to make this explicit
throughout the pipeline.

Data source: FMP news endpoint (requires FMP_API_KEY). If the key is not
available, functions return an empty list rather than scraping or using
unapproved sources.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from .exceptions import DataFetchError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
_USER_AGENT = "AI Research Platform research@example.com"
_TRUST_LEVEL = "low"  # News is always Priority 5 / low trust

# Explicit disclaimer attached to every news item
_NEWS_DISCLAIMER = (
    "NEWS — supplementary context only. "
    "Do not use as the basis for investment decisions or financial analysis."
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fmp_key_available() -> bool:
    return bool(os.environ.get("FMP_API_KEY", "").strip())


async def _fetch_fmp_news(
    ticker: str,
    limit: int,
) -> list[dict[str, Any]]:
    """
    Fetch stock-specific news from the FMP /stock_news endpoint.

    Returns raw list of FMP news dicts.
    """
    api_key = os.environ.get("FMP_API_KEY", "").strip()
    params = {"tickers": ticker.upper(), "limit": limit, "apikey": api_key}

    async with httpx.AsyncClient(
        headers={"User-Agent": _USER_AGENT},
        timeout=httpx.Timeout(20.0, connect=10.0),
        follow_redirects=True,
    ) as client:
        response = await client.get(f"{FMP_BASE_URL}/stock_news", params=params)

    if response.status_code == 401:
        raise DataFetchError(
            "FMP API key is invalid (HTTP 401) while fetching news.",
            source="fmp_news",
            status_code=401,
        )
    if response.status_code != 200:
        raise DataFetchError(
            f"FMP news endpoint returned HTTP {response.status_code}",
            source="fmp_news",
            status_code=response.status_code,
        )

    data = response.json()
    if isinstance(data, dict) and "Error Message" in data:
        raise DataFetchError(
            f"FMP news API error: {data['Error Message']}",
            source="fmp_news",
        )

    return data if isinstance(data, list) else []


def _normalise_fmp_news_item(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Map an FMP news dict to our standard news item schema.

    Standard fields:
        title         – headline text
        source        – publisher name
        url           – canonical article URL
        published_at  – ISO 8601 datetime string (UTC)
        summary       – article text or teaser (may be empty)
        ticker        – associated ticker
        trust_level   – always "low"
        disclaimer    – explicit warning about news priority
    """
    return {
        "title": raw.get("title", ""),
        "source": raw.get("site", raw.get("publisher", "")),
        "url": raw.get("url", ""),
        "published_at": raw.get("publishedDate", ""),
        "summary": raw.get("text", raw.get("description", "")),
        "ticker": raw.get("symbol", ""),
        "trust_level": _TRUST_LEVEL,
        "disclaimer": _NEWS_DISCLAIMER,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_company_news(
    ticker: str,
    company_name: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Fetch recent financial news articles related to a company.

    Uses the FMP stock_news endpoint when FMP_API_KEY is set. Returns an empty
    list — never raises — when the API key is unavailable, so that callers can
    treat news as optional enrichment.

    Args:
        ticker:       Stock ticker symbol (e.g. "AAPL").
        company_name: Human-readable company name (used for logging only).
        limit:        Maximum number of articles to return (default 20).

    Returns:
        List of news item dicts. Each dict has:
            title        (str)   – article headline
            source       (str)   – publisher name
            url          (str)   – article URL
            published_at (str)   – ISO 8601 datetime string
            summary      (str)   – teaser / body excerpt (may be empty)
            ticker       (str)   – associated ticker
            trust_level  (str)   – always "low"
            disclaimer   (str)   – Priority 5 usage warning

        Returns [] when FMP_API_KEY is not set or the request fails (news is
        optional; a failed news fetch must never block the rest of the pipeline).
    """
    if not _fmp_key_available():
        logger.info(
            "FMP_API_KEY not set — skipping news fetch for %s (%s). "
            "Set FMP_API_KEY to enable news enrichment.",
            ticker,
            company_name,
        )
        return []

    logger.info(
        "Fetching up to %d news articles for %s (%s) via FMP",
        limit,
        ticker,
        company_name,
    )

    try:
        raw_items = await _fetch_fmp_news(ticker=ticker, limit=limit)
    except DataFetchError as exc:
        # News failures are non-fatal; log and return empty
        logger.warning(
            "News fetch failed for %s (%s): %s — returning empty news list.",
            ticker,
            company_name,
            exc,
        )
        return []
    except Exception as exc:
        logger.warning(
            "Unexpected error fetching news for %s: %s — returning empty news list.",
            ticker,
            exc,
        )
        return []

    normalised: list[dict[str, Any]] = []
    for item in raw_items:
        try:
            normalised.append(_normalise_fmp_news_item(item))
        except Exception as exc:
            logger.debug("Skipping malformed news item for %s: %s", ticker, exc)
            continue

    logger.info("Fetched %d news articles for %s", len(normalised), ticker)
    return normalised
