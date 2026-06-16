"""
Yahoo Finance data fetcher via the yfinance library.

Priority 3 (fallback) data source. yfinance is a synchronous library so all
calls are dispatched to a thread-pool executor to avoid blocking the event
loop.

NOTE: yfinance relies on Yahoo Finance's undocumented internal APIs and may
break without notice. Always treat this as a last-resort fallback.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from functools import partial
from typing import Any

from .exceptions import DataFetchError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy import guard
# ---------------------------------------------------------------------------

try:
    import yfinance as yf  # type: ignore[import-untyped]

    _YF_AVAILABLE = True
except ImportError:
    _YF_AVAILABLE = False
    logger.warning(
        "yfinance is not installed. Yahoo Finance fallback will be unavailable. "
        "Install it with: pip install yfinance"
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_yfinance() -> None:
    if not _YF_AVAILABLE:
        raise DataFetchError(
            "yfinance library is not installed. Cannot use Yahoo Finance fallback.",
            source="yahoo",
        )


async def _run_sync(func: Any, *args: Any, **kwargs: Any) -> Any:
    """
    Run a synchronous callable in the default thread-pool executor so it does
    not block the asyncio event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


def _ticker_obj(ticker: str) -> "yf.Ticker":  # type: ignore[name-defined]
    """Return a yfinance Ticker object. Cheap to construct."""
    return yf.Ticker(ticker.upper())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_stock_info(ticker: str) -> dict[str, Any]:
    """
    Fetch general stock information for a ticker via yfinance.

    Returns a dict containing whatever Yahoo Finance provides for `.info`,
    including name, sector, industry, market cap, trailing P/E, dividend yield,
    52-week high/low, etc.

    Raises:
        DataFetchError: if yfinance is not available or the ticker is invalid.
    """
    _require_yfinance()
    logger.info("Yahoo: fetching stock info for %s", ticker)

    def _fetch() -> dict[str, Any]:
        t = _ticker_obj(ticker)
        info = t.info
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None:
            # yfinance returns a sparse dict for invalid tickers
            symbol = info.get("symbol", "")
            if not symbol:
                raise DataFetchError(
                    f"Yahoo Finance returned no data for ticker '{ticker}'. "
                    "The ticker may be invalid or delisted.",
                    source="yahoo",
                )
        return info

    try:
        info = await _run_sync(_fetch)
    except DataFetchError:
        raise
    except Exception as exc:
        raise DataFetchError(
            f"Yahoo Finance get_stock_info failed for '{ticker}': {exc}",
            source="yahoo",
        ) from exc

    return info


async def get_historical_prices(
    ticker: str,
    period: str = "1y",
) -> list[dict[str, Any]]:
    """
    Fetch historical OHLCV price data for a ticker.

    Args:
        ticker: Stock ticker symbol (e.g. "AAPL").
        period: yfinance period string — one of:
            "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"

    Returns:
        List of dicts with keys: date, open, high, low, close, volume,
        dividends, stock_splits. Ordered chronologically (oldest first).

    Raises:
        DataFetchError: if yfinance is not available or the fetch fails.
    """
    _require_yfinance()
    logger.info("Yahoo: fetching historical prices for %s (period=%s)", ticker, period)

    def _fetch() -> list[dict[str, Any]]:
        t = _ticker_obj(ticker)
        hist = t.history(period=period, auto_adjust=True)
        if hist.empty:
            raise DataFetchError(
                f"Yahoo Finance returned empty price history for '{ticker}' "
                f"with period='{period}'.",
                source="yahoo",
            )
        records: list[dict[str, Any]] = []
        for ts, row in hist.iterrows():
            # ts is a pandas Timestamp; convert to ISO 8601 string
            date_str = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            records.append(
                {
                    "date": date_str,
                    "open": float(row.get("Open", 0)),
                    "high": float(row.get("High", 0)),
                    "low": float(row.get("Low", 0)),
                    "close": float(row.get("Close", 0)),
                    "volume": int(row.get("Volume", 0)),
                    "dividends": float(row.get("Dividends", 0)),
                    "stock_splits": float(row.get("Stock Splits", 0)),
                }
            )
        return records

    try:
        return await _run_sync(_fetch)
    except DataFetchError:
        raise
    except Exception as exc:
        raise DataFetchError(
            f"Yahoo Finance get_historical_prices failed for '{ticker}': {exc}",
            source="yahoo",
        ) from exc


async def get_current_price(ticker: str) -> float:
    """
    Fetch the most recent market price for a ticker.

    Uses `info["currentPrice"]` or `info["regularMarketPrice"]` from yfinance.
    For real-time prices you should use a dedicated market-data provider — Yahoo
    Finance prices may be delayed by 15–20 minutes.

    Returns:
        The current (possibly delayed) price as a float.

    Raises:
        DataFetchError: if the price cannot be determined.
    """
    _require_yfinance()
    logger.info("Yahoo: fetching current price for %s", ticker)

    def _fetch() -> float:
        t = _ticker_obj(ticker)
        info = t.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        if price is None:
            # Last resort: pull last close from a 1-day history
            hist = t.history(period="1d")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
        if price is None:
            raise DataFetchError(
                f"Yahoo Finance could not determine current price for '{ticker}'.",
                source="yahoo",
            )
        return float(price)

    try:
        return await _run_sync(_fetch)
    except DataFetchError:
        raise
    except Exception as exc:
        raise DataFetchError(
            f"Yahoo Finance get_current_price failed for '{ticker}': {exc}",
            source="yahoo",
        ) from exc


async def get_options_chain(ticker: str) -> dict[str, Any]:
    """
    Fetch the full options chain for a ticker.

    Returns a dict with keys:
        - expiration_dates: list of available expiration date strings
        - options: dict mapping each expiration date to {"calls": [...], "puts": [...]}
          where each entry is a list of option contract dicts.

    Raises:
        DataFetchError: if yfinance is not available or the ticker has no options.
    """
    _require_yfinance()
    logger.info("Yahoo: fetching options chain for %s", ticker)

    def _fetch() -> dict[str, Any]:
        t = _ticker_obj(ticker)
        expirations: tuple[str, ...] = t.options
        if not expirations:
            raise DataFetchError(
                f"Yahoo Finance returned no options data for '{ticker}'. "
                "The ticker may not have listed options.",
                source="yahoo",
            )

        options: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for exp in expirations:
            chain = t.option_chain(exp)
            calls_df = chain.calls
            puts_df = chain.puts
            options[exp] = {
                "calls": calls_df.to_dict(orient="records") if not calls_df.empty else [],
                "puts": puts_df.to_dict(orient="records") if not puts_df.empty else [],
            }

        return {
            "ticker": ticker.upper(),
            "expiration_dates": list(expirations),
            "options": options,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    try:
        return await _run_sync(_fetch)
    except DataFetchError:
        raise
    except Exception as exc:
        raise DataFetchError(
            f"Yahoo Finance get_options_chain failed for '{ticker}': {exc}",
            source="yahoo",
        ) from exc
