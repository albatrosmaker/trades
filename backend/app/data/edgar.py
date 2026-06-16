"""
SEC EDGAR data fetcher.

Uses the free public EDGAR APIs — no API key required.
Base URLs:
  - https://data.sec.gov          (XBRL facts, submissions)
  - https://efts.sec.gov          (full-text search)
  - https://www.sec.gov/cgi-bin   (legacy CGI endpoints)

Rate limit: EDGAR enforces ≤10 requests/second per IP. We enforce this
ourselves with an asyncio.Semaphore and a fixed inter-request delay.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any
from urllib.parse import urljoin

import httpx

from .exceptions import DataFetchError, RateLimitError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_SEC_GOV = "https://data.sec.gov"
EFTS_SEC_GOV = "https://efts.sec.gov"
WWW_SEC_GOV = "https://www.sec.gov"

_USER_AGENT = "AI Research Platform research@example.com"
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.5  # seconds; retried after base^attempt
_RATE_LIMIT_RPS = 10  # max requests per second to all EDGAR endpoints
_MIN_REQUEST_INTERVAL = 1.0 / _RATE_LIMIT_RPS  # 0.1 seconds

# Module-level semaphore and timestamp for rate limiting (shared across all
# calls within the same process).
_semaphore = asyncio.Semaphore(_RATE_LIMIT_RPS)
_last_request_time: float = 0.0
_rate_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_cik(cik: str) -> str:
    """Zero-pad a CIK to 10 digits as EDGAR expects."""
    return cik.strip().lstrip("0").zfill(10)


async def _wait_for_rate_limit() -> None:
    """Ensure we never exceed _RATE_LIMIT_RPS across concurrent callers."""
    global _last_request_time
    async with _rate_lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < _MIN_REQUEST_INTERVAL:
            await asyncio.sleep(_MIN_REQUEST_INTERVAL - elapsed)
        _last_request_time = time.monotonic()


def _build_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        headers={"User-Agent": _USER_AGENT, "Accept-Encoding": "gzip, deflate"},
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
    )


async def _get(url: str, params: dict[str, Any] | None = None) -> httpx.Response:
    """
    Perform a GET request with exponential-backoff retries and rate limiting.

    Raises:
        RateLimitError: when EDGAR returns 429 and retries are exhausted.
        DataFetchError: on any other non-2xx response or connection error.
    """
    last_exc: Exception | None = None
    async with _semaphore:
        for attempt in range(_MAX_RETRIES):
            await _wait_for_rate_limit()
            try:
                async with _build_client() as client:
                    response = await client.get(url, params=params)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", 60))
                    if attempt < _MAX_RETRIES - 1:
                        wait = retry_after or (_BACKOFF_BASE ** (attempt + 1))
                        logger.warning(
                            "EDGAR rate limited on %s, waiting %.1fs (attempt %d/%d)",
                            url,
                            wait,
                            attempt + 1,
                            _MAX_RETRIES,
                        )
                        await asyncio.sleep(wait)
                        continue
                    raise RateLimitError(
                        f"EDGAR rate limit exceeded after {_MAX_RETRIES} attempts: {url}",
                        source="edgar",
                        retry_after=retry_after,
                    )

                if response.status_code == 200:
                    return response

                # Retry on 5xx server errors
                if response.status_code >= 500 and attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "EDGAR server error %d on %s, retrying in %.1fs",
                        response.status_code,
                        url,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                raise DataFetchError(
                    f"EDGAR returned HTTP {response.status_code} for {url}",
                    source="edgar",
                    status_code=response.status_code,
                )

            except (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError) as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    wait = _BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        "EDGAR connection error on %s (%s), retrying in %.1fs",
                        url,
                        exc,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

    raise DataFetchError(
        f"EDGAR fetch failed after {_MAX_RETRIES} attempts for {url}: {last_exc}",
        source="edgar",
    ) from last_exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_company_facts(cik: str) -> dict[str, Any]:
    """
    Fetch all XBRL company facts for a given CIK.

    Returns the parsed JSON from:
        https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json

    The response contains structured financial data tagged in XBRL, including
    US-GAAP and IFRS concepts across all reported periods.
    """
    cik_padded = _normalize_cik(cik)
    url = f"{DATA_SEC_GOV}/api/xbrl/companyfacts/CIK{cik_padded}.json"
    logger.info("Fetching company facts for CIK %s", cik_padded)
    response = await _get(url)
    return response.json()


async def get_company_submissions(cik: str) -> dict[str, Any]:
    """
    Fetch the full submissions history for a company.

    Returns the parsed JSON from:
        https://data.sec.gov/submissions/CIK{cik}.json

    Includes company metadata (name, SIC, exchanges, addresses) and a list
    of recent filings with accession numbers, form types, and dates.
    """
    cik_padded = _normalize_cik(cik)
    url = f"{DATA_SEC_GOV}/submissions/CIK{cik_padded}.json"
    logger.info("Fetching submissions for CIK %s", cik_padded)
    response = await _get(url)
    return response.json()


async def search_company(query: str) -> list[dict[str, Any]]:
    """
    Search for companies on EDGAR using the full-text search API.

    Returns a list of dicts with keys: cik, name, ticker, exchange.
    Uses the EDGAR company search endpoint.
    """
    # EDGAR company search (not full-text filing search)
    url = f"{WWW_SEC_GOV}/cgi-bin/browse-edgar"
    params = {
        "company": query,
        "CIK": "",
        "type": "",
        "dateb": "",
        "owner": "include",
        "count": "40",
        "search_text": "",
        "action": "getcompany",
        "output": "atom",
    }
    logger.info("Searching EDGAR for company: %s", query)
    response = await _get(url, params=params)

    # Parse the Atom feed response
    results: list[dict[str, Any]] = []
    content = response.text

    # Extract company entries from Atom XML using simple pattern matching
    # (avoids lxml dependency; EDGAR Atom feed is well-structured)
    entry_pattern = re.compile(r"<entry>(.*?)</entry>", re.DOTALL)
    cik_pattern = re.compile(r"<cik>(\d+)</cik>")
    name_pattern = re.compile(r"<company-name>(.*?)</company-name>")
    ticker_pattern = re.compile(r"<assigned-sic-desc>.*?</assigned-sic-desc>", re.DOTALL)

    for entry in entry_pattern.finditer(content):
        block = entry.group(1)
        cik_match = cik_pattern.search(block)
        name_match = name_pattern.search(block)
        if cik_match and name_match:
            results.append(
                {
                    "cik": cik_match.group(1).zfill(10),
                    "name": name_match.group(1).strip(),
                }
            )

    # If Atom parsing yielded nothing, fall back to the JSON company tickers
    if not results:
        try:
            json_url = f"{DATA_SEC_GOV}/files/company_tickers.json"
            json_resp = await _get(json_url)
            tickers_data = json_resp.json()
            query_lower = query.lower()
            for _idx, company in tickers_data.items():
                if (
                    query_lower in company.get("title", "").lower()
                    or query_lower in company.get("ticker", "").lower()
                ):
                    results.append(
                        {
                            "cik": str(company["cik_str"]).zfill(10),
                            "name": company.get("title", ""),
                            "ticker": company.get("ticker", ""),
                        }
                    )
                    if len(results) >= 20:
                        break
        except Exception as exc:
            logger.warning("Fallback ticker search failed: %s", exc)

    return results


async def get_filing_index(cik: str, accession_number: str) -> dict[str, Any]:
    """
    Fetch the filing index page for a specific accession number.

    Returns a dict with filing metadata and a list of documents included in
    the filing (names, types, descriptions, URLs).

    accession_number format: "0001234567-23-000001" (with or without dashes)
    """
    cik_padded = _normalize_cik(cik)
    # Normalize accession number: remove dashes for the URL path
    acc_no_clean = accession_number.replace("-", "")
    # Re-insert dashes for the JSON index filename
    acc_no_dashed = f"{acc_no_clean[:10]}-{acc_no_clean[10:12]}-{acc_no_clean[12:]}"

    url = (
        f"{DATA_SEC_GOV}/submissions/CIK{cik_padded}/"
        f"{acc_no_dashed.replace('-', '')}/index.json"
    )
    # EDGAR JSON index path
    index_url = (
        f"{WWW_SEC_GOV}/Archives/edgar/data/{cik_padded.lstrip('0')}/"
        f"{acc_no_clean}/{acc_no_dashed}-index.json"
    )
    logger.info("Fetching filing index for CIK %s, accession %s", cik_padded, acc_no_dashed)

    try:
        response = await _get(index_url)
        data = response.json()
    except DataFetchError:
        # Fallback: HTML index
        html_url = (
            f"{WWW_SEC_GOV}/Archives/edgar/data/{cik_padded.lstrip('0')}/"
            f"{acc_no_clean}/{acc_no_dashed}-index.htm"
        )
        response = await _get(html_url)
        # Return minimal metadata from HTML
        return {
            "accession_number": acc_no_dashed,
            "cik": cik_padded,
            "raw_html": response.text,
            "documents": [],
        }

    return {
        "accession_number": acc_no_dashed,
        "cik": cik_padded,
        "filing_date": data.get("filingDate", ""),
        "form_type": data.get("formType", ""),
        "documents": data.get("files", []),
    }


async def get_filing_document(url: str) -> str:
    """
    Fetch the text content of a specific filing document by URL.

    Returns the raw text content. The caller is responsible for parsing HTML,
    XBRL, or plain text as appropriate.
    """
    if not url.startswith("http"):
        url = urljoin(WWW_SEC_GOV, url)
    logger.info("Fetching filing document: %s", url)
    response = await _get(url)
    return response.text


async def _get_filings_by_form_type(
    cik: str, form_type: str, limit: int
) -> list[dict[str, Any]]:
    """
    Internal helper: return the most recent `limit` filings of a given form
    type from the company's submissions JSON.
    """
    submissions = await get_company_submissions(cik)
    filings_data = submissions.get("filings", {}).get("recent", {})

    form_types: list[str] = filings_data.get("form", [])
    accession_numbers: list[str] = filings_data.get("accessionNumber", [])
    filing_dates: list[str] = filings_data.get("filingDate", [])
    primary_docs: list[str] = filings_data.get("primaryDocument", [])
    descriptions: list[str] = filings_data.get("primaryDocDescription", [])

    results: list[dict[str, Any]] = []
    cik_padded = _normalize_cik(cik)

    for i, ft in enumerate(form_types):
        if ft.upper() == form_type.upper():
            acc_no = accession_numbers[i] if i < len(accession_numbers) else ""
            acc_no_clean = acc_no.replace("-", "")
            primary_doc = primary_docs[i] if i < len(primary_docs) else ""
            doc_url = (
                f"{WWW_SEC_GOV}/Archives/edgar/data/"
                f"{cik_padded.lstrip('0')}/{acc_no_clean}/{primary_doc}"
                if primary_doc
                else ""
            )
            results.append(
                {
                    "form_type": ft,
                    "accession_number": acc_no,
                    "filing_date": filing_dates[i] if i < len(filing_dates) else "",
                    "primary_document": primary_doc,
                    "primary_doc_description": descriptions[i] if i < len(descriptions) else "",
                    "document_url": doc_url,
                    "cik": cik_padded,
                }
            )
            if len(results) >= limit:
                break

    return results


async def get_latest_10k(cik: str) -> dict[str, Any]:
    """
    Fetch metadata and document URL for the most recent 10-K filing.

    Returns a dict with filing metadata. To retrieve the actual document text,
    call `get_filing_document(result["document_url"])`.
    """
    logger.info("Fetching latest 10-K for CIK %s", cik)
    filings = await _get_filings_by_form_type(cik, "10-K", limit=1)
    if not filings:
        raise DataFetchError(
            f"No 10-K filings found for CIK {cik}",
            source="edgar",
        )
    return filings[0]


async def get_latest_10q(cik: str) -> dict[str, Any]:
    """
    Fetch metadata and document URL for the most recent 10-Q filing.

    Returns a dict with filing metadata. To retrieve the actual document text,
    call `get_filing_document(result["document_url"])`.
    """
    logger.info("Fetching latest 10-Q for CIK %s", cik)
    filings = await _get_filings_by_form_type(cik, "10-Q", limit=1)
    if not filings:
        raise DataFetchError(
            f"No 10-Q filings found for CIK {cik}",
            source="edgar",
        )
    return filings[0]


async def get_8k_filings(cik: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Fetch the most recent `limit` 8-K filings for the given CIK.

    Returns a list of dicts with accession numbers, dates, and document URLs.
    8-K filings announce material company events (earnings, M&A, leadership
    changes, etc.).
    """
    logger.info("Fetching up to %d 8-K filings for CIK %s", limit, cik)
    return await _get_filings_by_form_type(cik, "8-K", limit=limit)


async def get_insider_transactions(cik: str) -> list[dict[str, Any]]:
    """
    Fetch recent Form 4 (insider transaction) filings for a company.

    Each returned dict includes the accession number, filing date, and the
    URL of the primary Form 4 XML document. Full transaction details require
    parsing the XML via `get_filing_document`.
    """
    logger.info("Fetching Form 4 insider transactions for CIK %s", cik)
    return await _get_filings_by_form_type(cik, "4", limit=50)


async def get_proxy_statement(cik: str) -> dict[str, Any]:
    """
    Fetch metadata for the most recent DEF 14A (proxy statement) filing.

    The proxy statement contains information about executive compensation,
    board composition, and shareholder proposals.
    """
    logger.info("Fetching DEF 14A proxy statement for CIK %s", cik)
    filings = await _get_filings_by_form_type(cik, "DEF 14A", limit=1)
    if not filings:
        # Try DEFA14A as fallback
        filings = await _get_filings_by_form_type(cik, "DEFA14A", limit=1)
    if not filings:
        raise DataFetchError(
            f"No DEF 14A proxy statement found for CIK {cik}",
            source="edgar",
        )
    return filings[0]
