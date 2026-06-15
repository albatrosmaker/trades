"""
financial_ratios.py — Core financial ratio calculation engine.

Design principles:
  1. ALL metrics are computed from raw inputs — never hard-coded or assumed.
  2. Every result carries the formula string, the actual input values used,
     and a confidence score so results are fully auditable.
  3. Missing data is handled gracefully: return None value + confidence=0
     rather than raising exceptions.
  4. Averaging logic (e.g., average assets for ROA) uses two-period average
     when prior-period data is available; falls back to single-period with
     a confidence penalty and a note.

Data contract:
  All input dicts must use *internal* field names as defined in field_mappings.py.
  Call normalize_edgar_data() / normalize_fmp_data() before passing data here.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CalculationResult — the single return type for every calculation
# ---------------------------------------------------------------------------

@dataclass
class CalculationResult:
    """
    Fully-auditable container for a single computed financial metric.

    Attributes:
        metric_name:  Snake-case name of the metric (e.g. "gross_margin").
        value:        The computed float, or None if calculation failed.
        formula:      Human-readable formula string (e.g. "(Revenue - COGS) / Revenue").
        inputs:       Dict of {label: actual_value} used in the formula so the
                      caller can reproduce the result independently.
        period:       Fiscal period identifier (e.g. "FY", "Q1", "TTM").
        fiscal_year:  Four-digit fiscal year (e.g. 2024).
        source:       Data provider string (e.g. "EDGAR", "FMP").
        confidence:   0.0–1.0. 1.0 = all inputs present; 0.0 = calculation
                      impossible; intermediate values for estimated inputs.
        notes:        Free-text observations (e.g. "D&A estimated from CF stmt").
    """
    metric_name: str
    value: Optional[float]
    formula: str
    inputs: dict
    period: str
    fiscal_year: int
    source: str
    confidence: float
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_divide(
    numerator: Optional[float],
    denominator: Optional[float],
    *,
    zero_result: Optional[float] = None,
) -> Optional[float]:
    """
    Return numerator / denominator, or None/zero_result on failure.

    Args:
        zero_result: Value to return when denominator is exactly 0.
                     Defaults to None (undefined rather than ±inf).
    """
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return zero_result
    return numerator / denominator


def _get(data: dict, *keys: str) -> Optional[float]:
    """
    Try a sequence of field names and return the first non-None numeric value.

    Supports fallback aliases within a single statement dict without requiring
    callers to know which alias was populated.
    """
    for key in keys:
        val = data.get(key)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return None


def _average(a: Optional[float], b: Optional[float]) -> tuple[Optional[float], bool]:
    """
    Return the average of two values and whether both were present.

    Returns:
        (average_value, both_present)
        If only one value is present, returns that value alone with
        both_present=False (single-period approximation).
    """
    if a is not None and b is not None:
        return (a + b) / 2.0, True
    if a is not None:
        return a, False
    if b is not None:
        return b, False
    return None, False


def _confidence_from_missing(total_inputs: int, missing_count: int) -> float:
    """
    Simple confidence model: 1.0 when all inputs present, degrades linearly.

    A missing primary input that makes calculation impossible yields 0.0.
    """
    if total_inputs == 0:
        return 0.0
    present = total_inputs - missing_count
    return round(present / total_inputs, 3)


def _null_result(
    metric_name: str,
    formula: str,
    period: str,
    fiscal_year: int,
    source: str,
    missing_fields: list[str],
) -> CalculationResult:
    """Construct a zero-confidence result for when required data is absent."""
    note = f"Cannot calculate: missing required fields: {', '.join(missing_fields)}"
    logger.warning("[%s] %s", metric_name, note)
    return CalculationResult(
        metric_name=metric_name,
        value=None,
        formula=formula,
        inputs={f: None for f in missing_fields},
        period=period,
        fiscal_year=fiscal_year,
        source=source,
        confidence=0.0,
        notes=[note],
    )


# ---------------------------------------------------------------------------
# FinancialRatioCalculator
# ---------------------------------------------------------------------------

class FinancialRatioCalculator:
    """
    Computes financial ratios from raw (normalised) statement dicts.

    All methods accept dicts whose keys are internal field names
    (see field_mappings.py). Every method returns a CalculationResult.

    Usage:
        calc = FinancialRatioCalculator(source="FMP", period="FY", fiscal_year=2024)
        result = calc.gross_margin(income_stmt)
        print(result.value, result.formula, result.inputs)
    """

    def __init__(
        self,
        source: str = "unknown",
        period: str = "FY",
        fiscal_year: int = 0,
    ) -> None:
        self.source = source
        self.period = period
        self.fiscal_year = fiscal_year

    # ── Context helpers ──────────────────────────────────────────────────────

    def _ctx(self, metric_name: str, formula: str) -> dict:
        """Return common kwargs for CalculationResult construction."""
        return dict(
            metric_name=metric_name,
            formula=formula,
            period=self.period,
            fiscal_year=self.fiscal_year,
            source=self.source,
        )

    # =========================================================================
    # PROFITABILITY RATIOS
    # =========================================================================

    def gross_margin(self, income_stmt: dict) -> CalculationResult:
        """
        Gross Margin = (Revenue - Cost of Revenue) / Revenue

        Measures how much of each revenue dollar remains after paying direct
        production costs. Higher margins indicate pricing power and/or low
        production costs relative to peers.
        """
        ctx = self._ctx("gross_margin", "(Revenue - Cost of Revenue) / Revenue")
        revenue = _get(income_stmt, "revenue")
        cogs = _get(income_stmt, "cost_of_revenue")

        # Some statements provide gross_profit directly; use it as a cross-check
        # or fallback when COGS is absent.
        gross_profit_direct = _get(income_stmt, "gross_profit")

        inputs = {"revenue": revenue, "cost_of_revenue": cogs}
        notes: list[str] = []

        if revenue is None:
            return _null_result("gross_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["revenue"])

        gross_profit: Optional[float]
        if cogs is not None:
            gross_profit = revenue - cogs
            confidence = 1.0
        elif gross_profit_direct is not None:
            gross_profit = gross_profit_direct
            inputs["gross_profit_direct"] = gross_profit_direct
            inputs["cost_of_revenue"] = None
            notes.append("COGS not available; gross profit taken directly from statement")
            confidence = 0.9
        else:
            return _null_result("gross_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["cost_of_revenue"])

        value = _safe_divide(gross_profit, revenue)
        return CalculationResult(
            **ctx,
            value=value,
            inputs=inputs,
            confidence=confidence,
            notes=notes,
        )

    def operating_margin(self, income_stmt: dict) -> CalculationResult:
        """
        Operating Margin = Operating Income / Revenue

        Captures profitability from core operations, excluding interest and
        taxes. Also known as EBIT margin when D&A is included in COGS/OpEx.
        """
        ctx = self._ctx("operating_margin", "Operating Income / Revenue")
        revenue = _get(income_stmt, "revenue")
        op_income = _get(income_stmt, "operating_income")
        notes: list[str] = []

        missing = [k for k, v in {"revenue": revenue, "operating_income": op_income}.items()
                   if v is None]
        if missing:
            return _null_result("operating_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        value = _safe_divide(op_income, revenue)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={"revenue": revenue, "operating_income": op_income},
            confidence=1.0,
            notes=notes,
        )

    def net_profit_margin(self, income_stmt: dict) -> CalculationResult:
        """
        Net Profit Margin = Net Income / Revenue

        The bottom-line margin after all costs, including interest and taxes.
        Heavily influenced by capital structure and tax planning vs. operating
        efficiency; compare with operating_margin for full picture.
        """
        ctx = self._ctx("net_profit_margin", "Net Income / Revenue")
        revenue = _get(income_stmt, "revenue")
        net_income = _get(income_stmt, "net_income")

        missing = [k for k, v in {"revenue": revenue, "net_income": net_income}.items()
                   if v is None]
        if missing:
            return _null_result("net_profit_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        value = _safe_divide(net_income, revenue)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={"revenue": revenue, "net_income": net_income},
            confidence=1.0,
            notes=[],
        )

    def ebitda(self, income_stmt: dict) -> CalculationResult:
        """
        EBITDA = Operating Income + Depreciation & Amortization

        A proxy for operating cash generation before working capital and capex.
        Used extensively in valuation multiples (EV/EBITDA).

        Note: EBITDA is not a GAAP measure. It excludes stock-based compensation,
        restructuring, and other non-recurring items that may be material.
        """
        ctx = self._ctx("ebitda", "Operating Income + D&A")
        op_income = _get(income_stmt, "operating_income")
        da = _get(income_stmt, "depreciation_and_amortization",
                  "depreciation", "amortization")
        notes: list[str] = []

        # Some providers give EBITDA directly
        ebitda_direct = _get(income_stmt, "ebitda")
        if ebitda_direct is not None and (op_income is None or da is None):
            notes.append("EBITDA taken directly from statement (components not available)")
            return CalculationResult(
                **ctx,
                value=ebitda_direct,
                inputs={"ebitda_direct": ebitda_direct},
                confidence=0.85,
                notes=notes,
            )

        if op_income is None:
            return _null_result("ebitda", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["operating_income"])

        confidence = 1.0
        if da is None:
            notes.append(
                "D&A not found in income statement; EBITDA approximated as Operating Income. "
                "Obtain D&A from cash flow statement for accuracy."
            )
            da = 0.0
            confidence = 0.5
        else:
            notes.append("D&A sourced from income statement line item")

        value = op_income + da
        return CalculationResult(
            **ctx,
            value=value,
            inputs={"operating_income": op_income, "depreciation_and_amortization": da},
            confidence=confidence,
            notes=notes,
        )

    def ebitda_margin(self, income_stmt: dict) -> CalculationResult:
        """
        EBITDA Margin = EBITDA / Revenue

        Expresses EBITDA as a percentage of revenue. Widely used for
        cross-company comparisons because it strips out capital structure
        differences and accounting for asset depreciation.
        """
        ctx = self._ctx("ebitda_margin", "EBITDA / Revenue")
        revenue = _get(income_stmt, "revenue")
        notes: list[str] = []

        if revenue is None:
            return _null_result("ebitda_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["revenue"])

        ebitda_result = self.ebitda(income_stmt)
        ebitda_val = ebitda_result.value

        if ebitda_val is None:
            return _null_result("ebitda_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source,
                                ["operating_income", "depreciation_and_amortization"])

        notes.extend(ebitda_result.notes)
        value = _safe_divide(ebitda_val, revenue)
        confidence = round(ebitda_result.confidence * 1.0, 3)

        return CalculationResult(
            **ctx,
            value=value,
            inputs={"ebitda": ebitda_val, "revenue": revenue},
            confidence=confidence,
            notes=notes,
        )

    def return_on_assets(
        self,
        income_stmt: dict,
        balance_sheet: dict,
        prior_balance_sheet: Optional[dict] = None,
    ) -> CalculationResult:
        """
        Return on Assets (ROA) = Net Income / Average Total Assets

        Average total assets uses beginning + ending balance divided by 2,
        which reduces the distortion from mid-year acquisitions or disposals.
        If only one period is available, the single-period figure is used with
        a confidence penalty.
        """
        ctx = self._ctx("return_on_assets", "Net Income / Average Total Assets")
        net_income = _get(income_stmt, "net_income")
        assets_end = _get(balance_sheet, "total_assets")
        assets_beg = _get(prior_balance_sheet or {}, "total_assets") if prior_balance_sheet else None
        notes: list[str] = []

        if net_income is None or assets_end is None:
            missing = [k for k, v in {"net_income": net_income, "total_assets": assets_end}.items()
                       if v is None]
            return _null_result("return_on_assets", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        avg_assets, both = _average(assets_beg, assets_end)
        if not both:
            notes.append(
                "Prior-period total assets not provided; ROA computed on ending balance only "
                "(single-period approximation — may overstate ROA if assets grew during year)"
            )
            confidence = 0.75
        else:
            confidence = 1.0

        value = _safe_divide(net_income, avg_assets)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "net_income": net_income,
                "total_assets_end": assets_end,
                "total_assets_beg": assets_beg,
                "average_total_assets": avg_assets,
            },
            confidence=confidence,
            notes=notes,
        )

    def return_on_equity(
        self,
        income_stmt: dict,
        balance_sheet: dict,
        prior_balance_sheet: Optional[dict] = None,
    ) -> CalculationResult:
        """
        Return on Equity (ROE) = Net Income / Average Shareholders' Equity

        Measures how efficiently management generates profit from equity
        capital. Highly sensitive to leverage (DuPont decomposition:
        ROE = Net Margin × Asset Turnover × Equity Multiplier).
        """
        ctx = self._ctx("return_on_equity", "Net Income / Average Shareholders' Equity")
        net_income = _get(income_stmt, "net_income")
        equity_end = _get(balance_sheet, "shareholders_equity", "total_equity")
        equity_beg = (_get(prior_balance_sheet, "shareholders_equity", "total_equity")
                      if prior_balance_sheet else None)
        notes: list[str] = []

        if net_income is None or equity_end is None:
            missing = [k for k, v in {
                "net_income": net_income, "shareholders_equity": equity_end}.items()
                if v is None]
            return _null_result("return_on_equity", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        avg_equity, both = _average(equity_beg, equity_end)
        if not both:
            notes.append(
                "Prior-period equity not provided; ROE computed on ending equity "
                "(single-period approximation)"
            )
            confidence = 0.75
        else:
            confidence = 1.0

        if avg_equity is not None and avg_equity < 0:
            notes.append(
                "Shareholders' equity is negative; ROE is mathematically defined but "
                "economically misleading — interpret with caution"
            )
            confidence = min(confidence, 0.5)

        value = _safe_divide(net_income, avg_equity)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "net_income": net_income,
                "equity_end": equity_end,
                "equity_beg": equity_beg,
                "average_equity": avg_equity,
            },
            confidence=confidence,
            notes=notes,
        )

    def return_on_invested_capital(
        self,
        income_stmt: dict,
        balance_sheet: dict,
        prior_balance_sheet: Optional[dict] = None,
    ) -> CalculationResult:
        """
        ROIC = NOPAT / Invested Capital

        NOPAT = Operating Income × (1 - Effective Tax Rate)
        Invested Capital = Total Equity + Total Debt - Cash & Equivalents
            (i.e., the capital actually deployed in operations)

        ROIC is the purest measure of operational value creation. When ROIC
        exceeds WACC, the company creates shareholder value; when below, it
        destroys value.
        """
        ctx = self._ctx(
            "return_on_invested_capital",
            "NOPAT / Invested Capital  where NOPAT = EBIT × (1 - Tax Rate) "
            "and Invested Capital = Equity + Debt - Cash",
        )
        op_income = _get(income_stmt, "operating_income")
        tax_expense = _get(income_stmt, "income_tax_expense")
        income_before_tax = _get(income_stmt, "income_before_tax")
        equity = _get(balance_sheet, "shareholders_equity", "total_equity")
        total_debt = _get(balance_sheet, "total_debt", "long_term_debt")
        short_debt = _get(balance_sheet, "short_term_debt") or 0.0
        cash = _get(balance_sheet, "cash_and_equivalents",
                    "cash_and_short_term_investments") or 0.0
        notes: list[str] = []

        if op_income is None or equity is None:
            missing = [k for k, v in {
                "operating_income": op_income, "shareholders_equity": equity}.items()
                if v is None]
            return _null_result("return_on_invested_capital", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        # Effective tax rate
        if tax_expense is not None and income_before_tax and income_before_tax != 0:
            tax_rate = max(0.0, min(tax_expense / income_before_tax, 0.99))
            notes.append(f"Effective tax rate computed from statement: {tax_rate:.1%}")
        else:
            tax_rate = 0.21  # US statutory rate as fallback
            notes.append(
                "Tax rate not derivable from statement; using 21% US statutory rate as proxy"
            )

        nopat = op_income * (1 - tax_rate)

        # Invested Capital
        if total_debt is None:
            total_debt = short_debt
            notes.append(
                "Long-term debt not found; using short-term debt only — "
                "invested capital may be understated"
            )
        else:
            total_debt = total_debt + short_debt

        ic_end = equity + total_debt - cash
        ic_beg = None
        if prior_balance_sheet:
            eq_p = _get(prior_balance_sheet, "shareholders_equity", "total_equity")
            d_p = (_get(prior_balance_sheet, "total_debt", "long_term_debt") or 0.0) + \
                  (_get(prior_balance_sheet, "short_term_debt") or 0.0)
            c_p = _get(prior_balance_sheet, "cash_and_equivalents",
                       "cash_and_short_term_investments") or 0.0
            if eq_p is not None:
                ic_beg = eq_p + d_p - c_p

        avg_ic, both = _average(ic_beg, ic_end)
        if not both:
            notes.append("Single-period invested capital used (prior balance sheet absent)")
            confidence = 0.70
        else:
            confidence = 0.95

        if avg_ic is None or avg_ic == 0:
            notes.append("Invested capital is zero or undefined; ROIC cannot be calculated")
            value = None
            confidence = 0.0
        else:
            value = _safe_divide(nopat, avg_ic)

        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "operating_income": op_income,
                "tax_rate_used": tax_rate,
                "nopat": nopat,
                "equity": equity,
                "total_debt": total_debt,
                "cash": cash,
                "invested_capital_end": ic_end,
                "invested_capital_beg": ic_beg,
                "average_invested_capital": avg_ic,
            },
            confidence=confidence,
            notes=notes,
        )

    # =========================================================================
    # GROWTH RATIOS
    # =========================================================================

    def _yoy_growth(
        self,
        metric_name: str,
        field: str,
        current_stmt: dict,
        prior_stmt: dict,
        display_name: str,
    ) -> CalculationResult:
        """Generic YoY growth helper: (V_t - V_{t-1}) / |V_{t-1}|"""
        formula = f"({display_name}_t - {display_name}_{{t-1}}) / |{display_name}_{{t-1}}|"
        ctx = self._ctx(metric_name, formula)

        current = _get(current_stmt, field)
        prior = _get(prior_stmt, field)

        missing = [k for k, v in {f"{field}_current": current, f"{field}_prior": prior}.items()
                   if v is None]
        if missing:
            return _null_result(metric_name, formula, self.period,
                                self.fiscal_year, self.source, missing)

        if prior == 0:
            return CalculationResult(
                **ctx,
                value=None,
                inputs={f"{field}_current": current, f"{field}_prior": prior},
                confidence=0.0,
                notes=[f"Cannot calculate growth: prior {display_name} is zero"],
            )

        value = (current - prior) / abs(prior)
        notes: list[str] = []
        if prior < 0 and current > 0:
            notes.append(
                f"Prior period {display_name} was negative and current is positive; "
                "growth rate is technically negative-to-positive (turnaround) — "
                "interpret directionally rather than numerically"
            )

        return CalculationResult(
            **ctx,
            value=value,
            inputs={f"{field}_current": current, f"{field}_prior": prior},
            confidence=1.0,
            notes=notes,
        )

    def revenue_growth_yoy(
        self, current_income: dict, prior_income: dict
    ) -> CalculationResult:
        """Revenue Growth YoY = (Revenue_t - Revenue_{t-1}) / Revenue_{t-1}"""
        return self._yoy_growth(
            "revenue_growth_yoy", "revenue", current_income, prior_income, "Revenue"
        )

    def net_income_growth_yoy(
        self, current_income: dict, prior_income: dict
    ) -> CalculationResult:
        """Net Income Growth YoY = (NetIncome_t - NetIncome_{t-1}) / |NetIncome_{t-1}|"""
        return self._yoy_growth(
            "net_income_growth_yoy", "net_income", current_income, prior_income, "Net Income"
        )

    def ebitda_growth_yoy(
        self, current_income: dict, prior_income: dict
    ) -> CalculationResult:
        """
        EBITDA Growth YoY.

        Computes EBITDA for both periods using the ebitda() method, then
        applies the standard YoY growth formula.
        """
        ctx = self._ctx(
            "ebitda_growth_yoy",
            "(EBITDA_t - EBITDA_{t-1}) / |EBITDA_{t-1}|"
        )
        current_ebitda_result = self.ebitda(current_income)
        prior_ebitda_result = self.ebitda(prior_income)

        ev_curr = current_ebitda_result.value
        ev_prior = prior_ebitda_result.value
        notes = (current_ebitda_result.notes or []) + (prior_ebitda_result.notes or [])

        if ev_curr is None or ev_prior is None:
            missing = (["ebitda_current"] if ev_curr is None else []) + \
                      (["ebitda_prior"] if ev_prior is None else [])
            return _null_result("ebitda_growth_yoy", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        if ev_prior == 0:
            return CalculationResult(
                **ctx,
                value=None,
                inputs={"ebitda_current": ev_curr, "ebitda_prior": ev_prior},
                confidence=0.0,
                notes=notes + ["Prior EBITDA is zero; growth rate undefined"],
            )

        value = (ev_curr - ev_prior) / abs(ev_prior)
        confidence = round(min(current_ebitda_result.confidence,
                               prior_ebitda_result.confidence), 3)

        return CalculationResult(
            **ctx,
            value=value,
            inputs={"ebitda_current": ev_curr, "ebitda_prior": ev_prior},
            confidence=confidence,
            notes=notes,
        )

    def fcf_growth_yoy(
        self, current_cf: dict, prior_cf: dict
    ) -> CalculationResult:
        """
        FCF Growth YoY = (FCF_t - FCF_{t-1}) / |FCF_{t-1}|

        Uses free_cash_flow() to compute FCF for each period.
        """
        ctx = self._ctx("fcf_growth_yoy", "(FCF_t - FCF_{t-1}) / |FCF_{t-1}|")

        curr_fcf_result = self.free_cash_flow(current_cf)
        prior_fcf_result = self.free_cash_flow(prior_cf)

        cv = curr_fcf_result.value
        pv = prior_fcf_result.value
        notes = (curr_fcf_result.notes or []) + (prior_fcf_result.notes or [])

        if cv is None or pv is None:
            missing = (["fcf_current"] if cv is None else []) + \
                      (["fcf_prior"] if pv is None else [])
            return _null_result("fcf_growth_yoy", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        if pv == 0:
            return CalculationResult(
                **ctx,
                value=None,
                inputs={"fcf_current": cv, "fcf_prior": pv},
                confidence=0.0,
                notes=notes + ["Prior FCF is zero; growth rate undefined"],
            )

        value = (cv - pv) / abs(pv)
        confidence = round(min(curr_fcf_result.confidence, prior_fcf_result.confidence), 3)

        return CalculationResult(
            **ctx,
            value=value,
            inputs={"fcf_current": cv, "fcf_prior": pv},
            confidence=confidence,
            notes=notes,
        )

    # =========================================================================
    # LIQUIDITY RATIOS
    # =========================================================================

    def current_ratio(self, balance_sheet: dict) -> CalculationResult:
        """
        Current Ratio = Current Assets / Current Liabilities

        Measures ability to pay short-term obligations. A ratio below 1.0
        means current liabilities exceed current assets, which may indicate
        liquidity stress. Industry context matters (e.g., retailers often
        run below 1.0 intentionally).
        """
        ctx = self._ctx("current_ratio", "Current Assets / Current Liabilities")
        ca = _get(balance_sheet, "current_assets")
        cl = _get(balance_sheet, "current_liabilities")

        missing = [k for k, v in {"current_assets": ca, "current_liabilities": cl}.items()
                   if v is None]
        if missing:
            return _null_result("current_ratio", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        notes: list[str] = []
        if cl == 0:
            notes.append("Current liabilities are zero; ratio is undefined")
        value = _safe_divide(ca, cl)

        return CalculationResult(
            **ctx,
            value=value,
            inputs={"current_assets": ca, "current_liabilities": cl},
            confidence=1.0,
            notes=notes,
        )

    def quick_ratio(self, balance_sheet: dict) -> CalculationResult:
        """
        Quick Ratio = (Cash + Short-term Investments + Accounts Receivable) / Current Liabilities

        A stricter liquidity test that excludes inventory (which may not be
        quickly convertible to cash). Also called the Acid-Test ratio.
        """
        ctx = self._ctx(
            "quick_ratio",
            "(Cash + Short-term Investments + Accounts Receivable) / Current Liabilities",
        )
        cash = _get(balance_sheet, "cash_and_equivalents",
                    "cash_and_short_term_investments") or 0.0
        st_inv = _get(balance_sheet, "short_term_investments") or 0.0
        ar = _get(balance_sheet, "accounts_receivable") or 0.0
        cl = _get(balance_sheet, "current_liabilities")
        notes: list[str] = []

        # Check which components were actually present
        cash_explicit = _get(balance_sheet, "cash_and_equivalents",
                             "cash_and_short_term_investments")
        ar_explicit = _get(balance_sheet, "accounts_receivable")

        missing_keys: list[str] = []
        if cl is None:
            missing_keys.append("current_liabilities")

        if missing_keys:
            return _null_result("quick_ratio", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing_keys)

        confidence = 1.0
        if cash_explicit is None:
            notes.append("Cash not found; using 0 for quick ratio numerator")
            confidence -= 0.2
        if ar_explicit is None:
            notes.append("Accounts receivable not found; using 0 for quick ratio numerator")
            confidence -= 0.2

        quick_assets = cash + st_inv + ar
        value = _safe_divide(quick_assets, cl)

        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "cash_and_equivalents": cash_explicit,
                "short_term_investments": st_inv,
                "accounts_receivable": ar_explicit,
                "quick_assets": quick_assets,
                "current_liabilities": cl,
            },
            confidence=max(0.0, confidence),
            notes=notes,
        )

    def cash_ratio(self, balance_sheet: dict) -> CalculationResult:
        """
        Cash Ratio = Cash & Cash Equivalents / Current Liabilities

        The most conservative liquidity measure — only counts cash that
        can be deployed immediately. Useful in distress analysis.
        """
        ctx = self._ctx("cash_ratio", "Cash & Equivalents / Current Liabilities")
        cash = _get(balance_sheet, "cash_and_equivalents",
                    "cash_and_short_term_investments")
        cl = _get(balance_sheet, "current_liabilities")

        missing = [k for k, v in {"cash_and_equivalents": cash,
                                   "current_liabilities": cl}.items() if v is None]
        if missing:
            return _null_result("cash_ratio", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        return CalculationResult(
            **ctx,
            value=_safe_divide(cash, cl),
            inputs={"cash_and_equivalents": cash, "current_liabilities": cl},
            confidence=1.0,
            notes=[],
        )

    # =========================================================================
    # LEVERAGE RATIOS
    # =========================================================================

    def net_debt(self, balance_sheet: dict) -> CalculationResult:
        """
        Net Debt = Total Debt - Cash & Cash Equivalents

        Negative net debt means the company is a net cash holder.
        Total debt = long-term debt + short-term debt (+ current portion of LTD).
        """
        ctx = self._ctx(
            "net_debt",
            "Total Debt - Cash & Cash Equivalents  "
            "(Total Debt = Long-term Debt + Short-term Debt)",
        )
        ltd = _get(balance_sheet, "long_term_debt") or 0.0
        std = _get(balance_sheet, "short_term_debt", "current_portion_long_term_debt") or 0.0
        total_debt_direct = _get(balance_sheet, "total_debt")
        cash = _get(balance_sheet, "cash_and_equivalents",
                    "cash_and_short_term_investments")
        notes: list[str] = []

        if cash is None:
            return _null_result("net_debt", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["cash_and_equivalents"])

        if total_debt_direct is not None:
            total_debt = total_debt_direct
            notes.append("Total debt sourced directly from balance sheet")
        else:
            total_debt = ltd + std
            notes.append(
                f"Total debt computed as Long-term Debt ({ltd:,.0f}) + "
                f"Short-term Debt ({std:,.0f})"
            )

        confidence = 1.0 if total_debt_direct is not None else 0.9

        return CalculationResult(
            **ctx,
            value=total_debt - cash,
            inputs={
                "long_term_debt": ltd,
                "short_term_debt": std,
                "total_debt": total_debt,
                "cash_and_equivalents": cash,
            },
            confidence=confidence,
            notes=notes,
        )

    def debt_to_equity(self, balance_sheet: dict) -> CalculationResult:
        """
        Debt-to-Equity = Total Debt / Shareholders' Equity

        A higher ratio means higher financial leverage and more creditor risk.
        Capital-intensive industries (utilities, telecom) typically carry
        higher D/E ratios than asset-light software businesses.
        """
        ctx = self._ctx("debt_to_equity", "Total Debt / Shareholders' Equity")
        equity = _get(balance_sheet, "shareholders_equity", "total_equity")
        total_debt_direct = _get(balance_sheet, "total_debt")
        ltd = _get(balance_sheet, "long_term_debt") or 0.0
        std = _get(balance_sheet, "short_term_debt") or 0.0
        notes: list[str] = []

        if equity is None:
            return _null_result("debt_to_equity", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["shareholders_equity"])

        if total_debt_direct is not None:
            total_debt = total_debt_direct
        else:
            total_debt = ltd + std
            notes.append("Total debt derived from long-term + short-term debt components")

        if equity < 0:
            notes.append(
                "Shareholders' equity is negative; D/E is mathematically defined "
                "but sign is inverted — company is technically insolvent on book basis"
            )

        value = _safe_divide(total_debt, equity)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={"total_debt": total_debt, "shareholders_equity": equity},
            confidence=1.0 if total_debt_direct is not None else 0.9,
            notes=notes,
        )

    def debt_to_ebitda(
        self, balance_sheet: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        Net Debt / EBITDA

        Measures how many years of EBITDA it would take to repay net debt.
        A ratio above 4–5x is generally considered high leverage for most
        industries. Lenders commonly use this as a covenant metric.
        """
        ctx = self._ctx("debt_to_ebitda", "Net Debt / EBITDA")

        nd_result = self.net_debt(balance_sheet)
        ebitda_result = self.ebitda(income_stmt)

        nd = nd_result.value
        ebitda_val = ebitda_result.value
        notes = (nd_result.notes or []) + (ebitda_result.notes or [])

        if nd is None:
            return _null_result("debt_to_ebitda", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["net_debt"])
        if ebitda_val is None or ebitda_val == 0:
            msg = "EBITDA is zero or undefined; Net Debt / EBITDA cannot be calculated"
            logger.warning("[debt_to_ebitda] %s", msg)
            return CalculationResult(
                **ctx,
                value=None,
                inputs={"net_debt": nd, "ebitda": ebitda_val},
                confidence=0.0,
                notes=notes + [msg],
            )

        confidence = round(min(nd_result.confidence, ebitda_result.confidence), 3)
        return CalculationResult(
            **ctx,
            value=_safe_divide(nd, ebitda_val),
            inputs={"net_debt": nd, "ebitda": ebitda_val},
            confidence=confidence,
            notes=notes,
        )

    def interest_coverage(self, income_stmt: dict) -> CalculationResult:
        """
        Interest Coverage Ratio = EBIT / Interest Expense

        How many times operating profit covers interest obligations. Below 1.5x
        is typically a distress signal; below 1.0x means the company cannot
        service its debt from operations.

        EBIT is used (not EBITDA) because interest is paid in cash, and D&A
        is a non-cash charge that does not represent available funds.
        """
        ctx = self._ctx("interest_coverage", "EBIT / Interest Expense")
        op_income = _get(income_stmt, "operating_income")
        interest = _get(income_stmt, "interest_expense")
        notes: list[str] = []

        missing = [k for k, v in {
            "operating_income": op_income, "interest_expense": interest}.items() if v is None]
        if missing:
            return _null_result("interest_coverage", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        # Interest expense is sometimes reported as a negative number (outflow)
        interest_abs = abs(interest)
        if interest < 0:
            notes.append("Interest expense was reported as negative; absolute value used")

        if interest_abs == 0:
            notes.append("Interest expense is zero; company carries no debt cost")
            return CalculationResult(
                **ctx,
                value=None,
                inputs={"operating_income": op_income, "interest_expense": interest},
                confidence=1.0,
                notes=notes,
            )

        return CalculationResult(
            **ctx,
            value=_safe_divide(op_income, interest_abs),
            inputs={"ebit": op_income, "interest_expense": interest_abs},
            confidence=1.0,
            notes=notes,
        )

    # =========================================================================
    # CASH FLOW RATIOS
    # =========================================================================

    def free_cash_flow(self, cash_flow_stmt: dict) -> CalculationResult:
        """
        Free Cash Flow = Operating Cash Flow - Capital Expenditures

        FCF is the cash a business generates after maintaining/expanding its
        asset base. It is the primary valuation driver in DCF analysis and
        the purest indicator of a company's ability to self-fund growth.

        CapEx is typically reported as a negative number in the investing
        section; the absolute value is used here.
        """
        ctx = self._ctx(
            "free_cash_flow",
            "Operating Cash Flow - Capital Expenditures",
        )
        ocf = _get(cash_flow_stmt, "operating_cash_flow")
        capex = _get(cash_flow_stmt, "capital_expenditures")
        notes: list[str] = []

        # Some providers include a pre-computed FCF field
        fcf_direct = _get(cash_flow_stmt, "free_cash_flow")
        if fcf_direct is not None and (ocf is None or capex is None):
            notes.append("FCF taken directly from cash flow statement")
            return CalculationResult(
                **ctx,
                value=fcf_direct,
                inputs={"free_cash_flow_direct": fcf_direct},
                confidence=0.85,
                notes=notes,
            )

        missing = [k for k, v in {
            "operating_cash_flow": ocf, "capital_expenditures": capex}.items() if v is None]
        if missing:
            return _null_result("free_cash_flow", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        # CapEx is often reported as negative (cash outflow); ensure correct sign
        capex_abs = abs(capex)
        if capex > 0:
            notes.append(
                "CapEx was positive in source data; using absolute value "
                "(expected convention: negative outflow)"
            )

        value = ocf - capex_abs
        return CalculationResult(
            **ctx,
            value=value,
            inputs={"operating_cash_flow": ocf, "capital_expenditures": capex_abs},
            confidence=1.0,
            notes=notes,
        )

    def fcf_margin(
        self, cash_flow_stmt: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        FCF Margin = Free Cash Flow / Revenue

        Measures what fraction of revenue is converted to free cash flow.
        High-quality businesses typically show FCF margins consistently above
        their net profit margins (FCF > Net Income → strong earnings quality).
        """
        ctx = self._ctx("fcf_margin", "Free Cash Flow / Revenue")
        revenue = _get(income_stmt, "revenue")

        if revenue is None:
            return _null_result("fcf_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["revenue"])

        fcf_result = self.free_cash_flow(cash_flow_stmt)
        fcf = fcf_result.value

        if fcf is None:
            return _null_result("fcf_margin", ctx["formula"], self.period,
                                self.fiscal_year, self.source,
                                ["operating_cash_flow", "capital_expenditures"])

        return CalculationResult(
            **ctx,
            value=_safe_divide(fcf, revenue),
            inputs={"free_cash_flow": fcf, "revenue": revenue},
            confidence=fcf_result.confidence,
            notes=fcf_result.notes,
        )

    def fcf_conversion(
        self, cash_flow_stmt: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        FCF Conversion = Free Cash Flow / Net Income

        Indicates what fraction of accounting profits are converted to cash.
        Ratios consistently above 1.0 indicate high earnings quality (e.g.,
        non-cash charges inflating book expenses). Ratios below 1.0 may
        suggest aggressive revenue recognition or working capital build-up.
        """
        ctx = self._ctx("fcf_conversion", "Free Cash Flow / Net Income")
        net_income = _get(income_stmt, "net_income")

        if net_income is None:
            return _null_result("fcf_conversion", ctx["formula"], self.period,
                                self.fiscal_year, self.source, ["net_income"])

        fcf_result = self.free_cash_flow(cash_flow_stmt)
        fcf = fcf_result.value

        if fcf is None:
            return _null_result("fcf_conversion", ctx["formula"], self.period,
                                self.fiscal_year, self.source,
                                ["operating_cash_flow", "capital_expenditures"])

        notes = list(fcf_result.notes)
        if net_income == 0:
            notes.append("Net income is zero; FCF conversion ratio undefined")
            return CalculationResult(
                **ctx,
                value=None,
                inputs={"free_cash_flow": fcf, "net_income": net_income},
                confidence=0.0,
                notes=notes,
            )

        return CalculationResult(
            **ctx,
            value=_safe_divide(fcf, net_income),
            inputs={"free_cash_flow": fcf, "net_income": net_income},
            confidence=fcf_result.confidence,
            notes=notes,
        )

    def capex_intensity(
        self, cash_flow_stmt: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        CapEx Intensity = Capital Expenditures / Revenue

        Shows how capital-intensive the business model is. Asset-light
        software companies may be below 2%; utilities and manufacturers
        often exceed 10–15%.
        """
        ctx = self._ctx("capex_intensity", "CapEx / Revenue")
        revenue = _get(income_stmt, "revenue")
        capex = _get(cash_flow_stmt, "capital_expenditures")
        notes: list[str] = []

        missing = [k for k, v in {"revenue": revenue, "capital_expenditures": capex}.items()
                   if v is None]
        if missing:
            return _null_result("capex_intensity", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        capex_abs = abs(capex)
        if capex > 0:
            notes.append("CapEx reported as positive; absolute value used")

        return CalculationResult(
            **ctx,
            value=_safe_divide(capex_abs, revenue),
            inputs={"capital_expenditures": capex_abs, "revenue": revenue},
            confidence=1.0,
            notes=notes,
        )

    # =========================================================================
    # WORKING CAPITAL RATIOS
    # =========================================================================

    def days_sales_outstanding(
        self, balance_sheet: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        Days Sales Outstanding (DSO) = Accounts Receivable / (Revenue / 365)

        The average number of days it takes to collect payment after a sale.
        Rising DSO can indicate collection problems or customers stretching
        payment terms. DSO comparisons must be within the same industry.
        """
        ctx = self._ctx(
            "days_sales_outstanding",
            "Accounts Receivable / (Revenue / 365)",
        )
        ar = _get(balance_sheet, "accounts_receivable")
        revenue = _get(income_stmt, "revenue")

        missing = [k for k, v in {
            "accounts_receivable": ar, "revenue": revenue}.items() if v is None]
        if missing:
            return _null_result("days_sales_outstanding", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        daily_revenue = revenue / 365.0
        value = _safe_divide(ar, daily_revenue)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "accounts_receivable": ar,
                "revenue": revenue,
                "daily_revenue": daily_revenue,
            },
            confidence=1.0,
            notes=[],
        )

    def days_inventory_outstanding(
        self, balance_sheet: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        Days Inventory Outstanding (DIO) = Inventory / (COGS / 365)

        Average number of days inventory is held before being sold.
        High DIO may signal slow-moving inventory or over-purchasing.
        Low DIO can indicate lean operations or supply constraints.
        """
        ctx = self._ctx(
            "days_inventory_outstanding",
            "Inventory / (COGS / 365)",
        )
        inventory = _get(balance_sheet, "inventory")
        cogs = _get(income_stmt, "cost_of_revenue")
        notes: list[str] = []

        missing = [k for k, v in {
            "inventory": inventory, "cost_of_revenue": cogs}.items() if v is None]
        if missing:
            return _null_result("days_inventory_outstanding", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        if cogs == 0:
            notes.append("COGS is zero; DIO undefined")
            return CalculationResult(
                **ctx,
                value=None,
                inputs={"inventory": inventory, "cost_of_revenue": cogs},
                confidence=0.0,
                notes=notes,
            )

        daily_cogs = cogs / 365.0
        value = _safe_divide(inventory, daily_cogs)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "inventory": inventory,
                "cost_of_revenue": cogs,
                "daily_cogs": daily_cogs,
            },
            confidence=1.0,
            notes=notes,
        )

    def days_payable_outstanding(
        self, balance_sheet: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        Days Payable Outstanding (DPO) = Accounts Payable / (COGS / 365)

        Average number of days the company takes to pay its suppliers.
        Higher DPO means more free financing from suppliers; too high may
        strain supplier relationships or indicate financial stress.
        """
        ctx = self._ctx(
            "days_payable_outstanding",
            "Accounts Payable / (COGS / 365)",
        )
        ap = _get(balance_sheet, "accounts_payable")
        cogs = _get(income_stmt, "cost_of_revenue")
        notes: list[str] = []

        missing = [k for k, v in {
            "accounts_payable": ap, "cost_of_revenue": cogs}.items() if v is None]
        if missing:
            return _null_result("days_payable_outstanding", ctx["formula"], self.period,
                                self.fiscal_year, self.source, missing)

        if cogs == 0:
            notes.append("COGS is zero; DPO undefined")
            return CalculationResult(
                **ctx,
                value=None,
                inputs={"accounts_payable": ap, "cost_of_revenue": cogs},
                confidence=0.0,
                notes=notes,
            )

        daily_cogs = cogs / 365.0
        value = _safe_divide(ap, daily_cogs)
        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "accounts_payable": ap,
                "cost_of_revenue": cogs,
                "daily_cogs": daily_cogs,
            },
            confidence=1.0,
            notes=notes,
        )

    def cash_conversion_cycle(
        self, balance_sheet: dict, income_stmt: dict
    ) -> CalculationResult:
        """
        Cash Conversion Cycle (CCC) = DSO + DIO - DPO

        The number of days between spending cash on inventory/inputs and
        receiving cash from customers. A negative CCC (e.g., Amazon) means
        the business collects cash before paying suppliers — a powerful
        working capital advantage.
        """
        ctx = self._ctx(
            "cash_conversion_cycle",
            "DSO + DIO - DPO",
        )
        dso_result = self.days_sales_outstanding(balance_sheet, income_stmt)
        dio_result = self.days_inventory_outstanding(balance_sheet, income_stmt)
        dpo_result = self.days_payable_outstanding(balance_sheet, income_stmt)

        notes: list[str] = []
        confidence_factors: list[float] = []
        available: dict[str, Optional[float]] = {
            "dso": dso_result.value,
            "dio": dio_result.value,
            "dpo": dpo_result.value,
        }

        for name, res in [("DSO", dso_result), ("DIO", dio_result), ("DPO", dpo_result)]:
            if res.value is not None:
                confidence_factors.append(res.confidence)
            else:
                notes.append(f"{name} unavailable: {'; '.join(res.notes)}")

        dso = dso_result.value or 0.0
        dio = dio_result.value or 0.0
        dpo = dpo_result.value or 0.0

        all_present = all(v is not None for v in available.values())
        if not all_present:
            present_names = [k.upper() for k, v in available.items() if v is not None]
            notes.append(
                f"CCC computed from available components only: {present_names}. "
                "Missing components treated as 0, which may understate the cycle."
            )
            if not confidence_factors:
                return _null_result("cash_conversion_cycle", ctx["formula"], self.period,
                                    self.fiscal_year, self.source,
                                    [k for k, v in available.items() if v is None])

        value = dso + dio - dpo
        confidence = round(sum(confidence_factors) / 3.0, 3) if confidence_factors else 0.0

        return CalculationResult(
            **ctx,
            value=value,
            inputs={
                "dso": dso_result.value,
                "dio": dio_result.value,
                "dpo": dpo_result.value,
            },
            confidence=confidence,
            notes=notes,
        )

    # =========================================================================
    # Convenience: compute all ratios in one call
    # =========================================================================

    def compute_all(
        self,
        income_stmt: dict,
        balance_sheet: dict,
        cash_flow_stmt: dict,
        prior_income_stmt: Optional[dict] = None,
        prior_balance_sheet: Optional[dict] = None,
        prior_cash_flow_stmt: Optional[dict] = None,
    ) -> dict[str, CalculationResult]:
        """
        Compute the full suite of financial ratios and return them as a dict
        keyed by metric_name.

        Useful when you want to calculate everything in one pass (e.g., for
        populating a company data model or scoring engine).
        """
        results: dict[str, CalculationResult] = {}

        # Profitability
        results["gross_margin"] = self.gross_margin(income_stmt)
        results["operating_margin"] = self.operating_margin(income_stmt)
        results["net_profit_margin"] = self.net_profit_margin(income_stmt)
        results["ebitda"] = self.ebitda(income_stmt)
        results["ebitda_margin"] = self.ebitda_margin(income_stmt)
        results["return_on_assets"] = self.return_on_assets(
            income_stmt, balance_sheet, prior_balance_sheet
        )
        results["return_on_equity"] = self.return_on_equity(
            income_stmt, balance_sheet, prior_balance_sheet
        )
        results["return_on_invested_capital"] = self.return_on_invested_capital(
            income_stmt, balance_sheet, prior_balance_sheet
        )

        # Growth (only if prior period data available)
        if prior_income_stmt:
            results["revenue_growth_yoy"] = self.revenue_growth_yoy(
                income_stmt, prior_income_stmt
            )
            results["net_income_growth_yoy"] = self.net_income_growth_yoy(
                income_stmt, prior_income_stmt
            )
            results["ebitda_growth_yoy"] = self.ebitda_growth_yoy(
                income_stmt, prior_income_stmt
            )
        if prior_cash_flow_stmt:
            results["fcf_growth_yoy"] = self.fcf_growth_yoy(
                cash_flow_stmt, prior_cash_flow_stmt
            )

        # Liquidity
        results["current_ratio"] = self.current_ratio(balance_sheet)
        results["quick_ratio"] = self.quick_ratio(balance_sheet)
        results["cash_ratio"] = self.cash_ratio(balance_sheet)

        # Leverage
        results["net_debt"] = self.net_debt(balance_sheet)
        results["debt_to_equity"] = self.debt_to_equity(balance_sheet)
        results["debt_to_ebitda"] = self.debt_to_ebitda(balance_sheet, income_stmt)
        results["interest_coverage"] = self.interest_coverage(income_stmt)

        # Cash Flow
        results["free_cash_flow"] = self.free_cash_flow(cash_flow_stmt)
        results["fcf_margin"] = self.fcf_margin(cash_flow_stmt, income_stmt)
        results["fcf_conversion"] = self.fcf_conversion(cash_flow_stmt, income_stmt)
        results["capex_intensity"] = self.capex_intensity(cash_flow_stmt, income_stmt)

        # Working Capital
        results["days_sales_outstanding"] = self.days_sales_outstanding(
            balance_sheet, income_stmt
        )
        results["days_inventory_outstanding"] = self.days_inventory_outstanding(
            balance_sheet, income_stmt
        )
        results["days_payable_outstanding"] = self.days_payable_outstanding(
            balance_sheet, income_stmt
        )
        results["cash_conversion_cycle"] = self.cash_conversion_cycle(
            balance_sheet, income_stmt
        )

        return results
