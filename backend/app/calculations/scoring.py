"""
scoring.py — Composite scoring engine for AI Equity Research Platform.

Translates raw financial metrics into normalised 0–100 scores with letter
grades, actionable strength/weakness observations, and full methodology
transparency.

Design principles:
  1. Scores are always computed from CalculationResult objects produced by
     financial_ratios.py — NEVER from manually entered numbers.
  2. Each scoring function documents its benchmark thresholds so analysts can
     audit why a particular score was assigned.
  3. Benchmarks are conservative and general-purpose; they can be overridden
     per-industry by passing a benchmark_overrides dict.
  4. ScoreResult carries both quantitative scores and qualitative observations
     so the LLM layer can produce human-readable commentary grounded in data.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

from .financial_ratios import CalculationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# ScoreResult — the return type for every scoring function
# ---------------------------------------------------------------------------

@dataclass
class ScoreResult:
    """
    Output of a composite scoring calculation.

    Attributes:
        score:             0–100 composite score for the category.
        grade:             Letter grade (A/B/C/D/F).
        component_scores:  Dict of {sub-metric: 0-100 score}.
        weights_used:      Dict of {sub-metric: weight} — must sum to 1.0.
        strengths:         Specific observations WITH data values where the
                           company outperforms benchmarks.
        weaknesses:        Specific observations WITH data values where the
                           company underperforms benchmarks.
        methodology_notes: Explanations of scoring approach, benchmarks used,
                           data gaps, and caveats.
        data_coverage:     Fraction of expected inputs that were present (0–1).
    """
    score: float
    grade: str
    component_scores: dict[str, float]
    weights_used: dict[str, float]
    strengths: list[str]
    weaknesses: list[str]
    methodology_notes: list[str]
    data_coverage: float = 1.0


# ---------------------------------------------------------------------------
# Internal utilities
# ---------------------------------------------------------------------------

def _grade(score: float) -> str:
    """Convert a 0–100 score to a letter grade."""
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _linear_score(
    value: float,
    bad: float,
    good: float,
    reverse: bool = False,
) -> float:
    """
    Map a metric value to a 0–100 score using linear interpolation between
    a 'bad' threshold (→ 0) and a 'good' threshold (→ 100).

    Args:
        value:   The metric value.
        bad:     Value that maps to score 0.
        good:    Value that maps to score 100.
        reverse: If True, lower values are better (e.g., debt ratios).

    Returns:
        Score clamped to [0, 100].
    """
    if reverse:
        bad, good = good, bad  # invert so "good" still maps to 100

    if good == bad:
        return 50.0

    raw = (value - bad) / (good - bad) * 100.0
    return max(0.0, min(100.0, raw))


def _get_val(result: Optional[CalculationResult]) -> Optional[float]:
    """Safely extract the float value from a CalculationResult (or None)."""
    if result is None:
        return None
    return result.value


def _find(
    results: list[CalculationResult], metric_name: str
) -> Optional[CalculationResult]:
    """Find a CalculationResult by metric_name in a list."""
    for r in results:
        if r.metric_name == metric_name:
            return r
    return None


def _weighted_average(
    component_scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """
    Compute a weighted average, skipping components that scored exactly -1
    (sentinel for 'data unavailable') and redistributing their weights.
    """
    total_weight = 0.0
    total_score = 0.0
    for name, score in component_scores.items():
        if score < 0:  # -1 sentinel = data unavailable
            continue
        w = weights.get(name, 0.0)
        total_score += score * w
        total_weight += w

    if total_weight == 0:
        return 0.0
    return total_score / total_weight


# ---------------------------------------------------------------------------
# Benchmark sets — conservative, cross-industry defaults.
# Pass benchmark_overrides to override specific keys for sector analysis.
# ---------------------------------------------------------------------------

DEFAULT_LIQUIDITY_BENCHMARKS = {
    "current_ratio":   {"bad": 0.5, "good": 2.5},
    "quick_ratio":     {"bad": 0.3, "good": 1.5},
    "cash_ratio":      {"bad": 0.05, "good": 0.5},
}

DEFAULT_LEVERAGE_BENCHMARKS = {
    "debt_to_equity":  {"bad": 3.0, "good": 0.0, "reverse": True},
    "debt_to_ebitda":  {"bad": 6.0, "good": 0.0, "reverse": True},
    "interest_coverage":{"bad": 1.0, "good": 10.0},
}

DEFAULT_PROFITABILITY_BENCHMARKS = {
    "gross_margin":            {"bad": 0.0,  "good": 0.70},
    "operating_margin":        {"bad": -0.10, "good": 0.30},
    "net_profit_margin":       {"bad": -0.10, "good": 0.25},
    "ebitda_margin":           {"bad": 0.0,  "good": 0.40},
    "return_on_equity":        {"bad": 0.0,  "good": 0.30},
    "return_on_invested_capital": {"bad": 0.0, "good": 0.25},
}

DEFAULT_CASH_GENERATION_BENCHMARKS = {
    "fcf_margin":       {"bad": -0.05, "good": 0.25},
    "fcf_conversion":   {"bad": 0.0,   "good": 1.5},
    "capex_intensity":  {"bad": 0.20,  "good": 0.01, "reverse": True},
}

DEFAULT_GROWTH_BENCHMARKS = {
    "revenue_growth_yoy":    {"bad": -0.10, "good": 0.30},
    "net_income_growth_yoy": {"bad": -0.20, "good": 0.40},
    "ebitda_growth_yoy":     {"bad": -0.15, "good": 0.35},
    "fcf_growth_yoy":        {"bad": -0.20, "good": 0.40},
}


# ---------------------------------------------------------------------------
# ScoringEngine
# ---------------------------------------------------------------------------

class ScoringEngine:
    """
    Produces composite 0–100 scores across five dimensions:
      - Financial Strength (liquidity + leverage + profitability + cash generation)
      - Growth
      - Profitability (standalone, suitable for peer comparison)
      - Governance
      - Risk

    Usage:
        engine = ScoringEngine()
        ratios = calculator.compute_all(income_stmt, balance_sheet, cf_stmt)
        score = engine.financial_strength_score(list(ratios.values()))
        print(score.score, score.grade, score.strengths)
    """

    def __init__(
        self,
        benchmark_overrides: Optional[dict] = None,
    ) -> None:
        """
        Args:
            benchmark_overrides: Flat dict of {benchmark_key: {bad, good, [reverse]}}
                                 to override specific default benchmarks.
                                 Example: {"gross_margin": {"bad": 0.10, "good": 0.80}}
        """
        self._overrides = benchmark_overrides or {}

    def _benchmark(self, key: str, defaults: dict) -> dict:
        """Return benchmark dict, applying any override for the given key."""
        return self._overrides.get(key, defaults.get(key, {}))

    def _score_metric(
        self,
        result: Optional[CalculationResult],
        benchmarks: dict,
        key: str,
        label: str,
        strengths: list[str],
        weaknesses: list[str],
        notes: list[str],
    ) -> float:
        """
        Score a single CalculationResult against benchmarks.

        Returns a 0–100 score, or -1 if data is unavailable.
        Appends to strengths/weaknesses/notes in-place.
        """
        bm = self._benchmark(key, benchmarks)
        if not bm:
            notes.append(f"No benchmark defined for {key}; skipping")
            return -1.0

        val = _get_val(result)
        if val is None or (result is not None and result.confidence < 0.3):
            notes.append(
                f"{label}: data unavailable or low confidence "
                f"(confidence={result.confidence if result else 'N/A'}); excluded from score"
            )
            return -1.0

        score = _linear_score(
            val, bm["bad"], bm["good"], reverse=bm.get("reverse", False)
        )

        val_pct = f"{val:.1%}" if abs(val) < 10 else f"{val:.2f}x"

        if score >= 70:
            strengths.append(
                f"{label}: {val_pct} "
                f"(score {score:.0f}/100 — above benchmark threshold of "
                f"{bm['good']:.1%} if bm['good'] < 10 else f\"{bm['good']:.2f}\")"
            )
        elif score <= 35:
            weaknesses.append(
                f"{label}: {val_pct} "
                f"(score {score:.0f}/100 — below minimum threshold of "
                f"{bm['bad']:.1%} if bm['bad'] < 10 else f\"{bm['bad']:.2f}\")"
            )

        if result and result.notes:
            for n in result.notes:
                notes.append(f"  [{key}] {n}")

        return score

    # =========================================================================
    # FINANCIAL STRENGTH SCORE
    # =========================================================================

    def financial_strength_score(
        self,
        ratios: list[CalculationResult],
        benchmark_overrides: Optional[dict] = None,
    ) -> ScoreResult:
        """
        Compute a composite Financial Strength score (0–100).

        Category weights:
          - Liquidity       20%  (current ratio, quick ratio, cash ratio)
          - Leverage        20%  (D/E, net debt/EBITDA, interest coverage)
          - Profitability   30%  (gross margin, op margin, net margin, EBITDA margin, ROIC, ROE)
          - Cash Generation 30%  (FCF margin, FCF conversion, CapEx intensity)

        Each sub-category score is the simple average of its constituent metrics.

        A company scoring above 70 is considered financially healthy; above 85
        is exceptional. Below 40 signals financial distress risk.
        """
        bm_overrides = benchmark_overrides or self._overrides
        strengths: list[str] = []
        weaknesses: list[str] = []
        notes: list[str] = [
            "Financial Strength score weights: Liquidity 20%, Leverage 20%, "
            "Profitability 30%, Cash Generation 30%."
        ]
        component_scores: dict[str, float] = {}

        # ── Liquidity sub-scores ─────────────────────────────────────────────
        liq_weights = {"current_ratio": 0.40, "quick_ratio": 0.40, "cash_ratio": 0.20}
        liq_scores: dict[str, float] = {}
        for key, label in [
            ("current_ratio", "Current Ratio"),
            ("quick_ratio", "Quick Ratio"),
            ("cash_ratio", "Cash Ratio"),
        ]:
            liq_scores[key] = self._score_metric(
                _find(ratios, key), DEFAULT_LIQUIDITY_BENCHMARKS,
                key, label, strengths, weaknesses, notes
            )
        liquidity_score = _weighted_average(liq_scores, liq_weights)
        component_scores["liquidity"] = liquidity_score
        notes.append(f"Liquidity sub-score: {liquidity_score:.1f}/100")

        # ── Leverage sub-scores ──────────────────────────────────────────────
        lev_weights = {
            "debt_to_equity": 0.30, "debt_to_ebitda": 0.40, "interest_coverage": 0.30
        }
        lev_scores: dict[str, float] = {}
        for key, label in [
            ("debt_to_equity", "Debt-to-Equity"),
            ("debt_to_ebitda", "Net Debt / EBITDA"),
            ("interest_coverage", "Interest Coverage"),
        ]:
            lev_scores[key] = self._score_metric(
                _find(ratios, key), DEFAULT_LEVERAGE_BENCHMARKS,
                key, label, strengths, weaknesses, notes
            )
        leverage_score = _weighted_average(lev_scores, lev_weights)
        component_scores["leverage"] = leverage_score
        notes.append(f"Leverage sub-score: {leverage_score:.1f}/100")

        # ── Profitability sub-scores ─────────────────────────────────────────
        prof_weights = {
            "gross_margin": 0.20,
            "operating_margin": 0.20,
            "net_profit_margin": 0.20,
            "ebitda_margin": 0.20,
            "return_on_equity": 0.10,
            "return_on_invested_capital": 0.10,
        }
        prof_scores: dict[str, float] = {}
        for key, label in [
            ("gross_margin", "Gross Margin"),
            ("operating_margin", "Operating Margin"),
            ("net_profit_margin", "Net Profit Margin"),
            ("ebitda_margin", "EBITDA Margin"),
            ("return_on_equity", "Return on Equity"),
            ("return_on_invested_capital", "ROIC"),
        ]:
            prof_scores[key] = self._score_metric(
                _find(ratios, key), DEFAULT_PROFITABILITY_BENCHMARKS,
                key, label, strengths, weaknesses, notes
            )
        profitability_score = _weighted_average(prof_scores, prof_weights)
        component_scores["profitability"] = profitability_score
        notes.append(f"Profitability sub-score: {profitability_score:.1f}/100")

        # ── Cash Generation sub-scores ───────────────────────────────────────
        cg_weights = {
            "fcf_margin": 0.40, "fcf_conversion": 0.40, "capex_intensity": 0.20
        }
        cg_scores: dict[str, float] = {}
        for key, label in [
            ("fcf_margin", "FCF Margin"),
            ("fcf_conversion", "FCF Conversion"),
            ("capex_intensity", "CapEx Intensity"),
        ]:
            cg_scores[key] = self._score_metric(
                _find(ratios, key), DEFAULT_CASH_GENERATION_BENCHMARKS,
                key, label, strengths, weaknesses, notes
            )
        cash_gen_score = _weighted_average(cg_scores, cg_weights)
        component_scores["cash_generation"] = cash_gen_score
        notes.append(f"Cash Generation sub-score: {cash_gen_score:.1f}/100")

        # ── Composite ────────────────────────────────────────────────────────
        category_weights = {
            "liquidity": 0.20, "leverage": 0.20,
            "profitability": 0.30, "cash_generation": 0.30,
        }
        composite = _weighted_average(component_scores, category_weights)

        # Data coverage
        all_expected = set(liq_weights) | set(lev_weights) | set(prof_weights) | set(cg_weights)
        present = sum(
            1 for key in all_expected
            if _get_val(_find(ratios, key)) is not None
        )
        data_coverage = present / len(all_expected) if all_expected else 0.0

        if data_coverage < 0.6:
            notes.append(
                f"WARNING: Only {data_coverage:.0%} of expected metrics present. "
                "Score reliability is reduced — obtain more complete financial data."
            )

        return ScoreResult(
            score=round(composite, 1),
            grade=_grade(composite),
            component_scores=component_scores,
            weights_used=category_weights,
            strengths=strengths,
            weaknesses=weaknesses,
            methodology_notes=notes,
            data_coverage=data_coverage,
        )

    # =========================================================================
    # GROWTH SCORE
    # =========================================================================

    def growth_score(
        self,
        growth_metrics: list[CalculationResult],
        benchmark_overrides: Optional[dict] = None,
    ) -> ScoreResult:
        """
        Composite Growth Score (0–100).

        Sub-components and weights:
          - Revenue growth YoY        30%
          - Net income growth YoY     25%
          - EBITDA growth YoY         25%
          - FCF growth YoY            20%

        A consistency bonus of up to +5 points is applied when all four
        metrics are positive simultaneously (broad-based growth).

        Benchmarks:
          - 30%+ growth → 100/100 (exceptional, typical of high-growth companies)
          - 10–30% → ~50–85/100 (strong to very strong)
          - 0–10% → ~30–50/100 (modest growth)
          - <0% → <30/100 (declining)
          - <-10% → <10/100 (sharp decline)
        """
        bm_overrides = benchmark_overrides or self._overrides
        strengths: list[str] = []
        weaknesses: list[str] = []
        notes: list[str] = [
            "Growth score weights: Revenue 30%, Net Income 25%, EBITDA 25%, FCF 20%."
        ]
        component_scores: dict[str, float] = {}

        weights = {
            "revenue_growth_yoy": 0.30,
            "net_income_growth_yoy": 0.25,
            "ebitda_growth_yoy": 0.25,
            "fcf_growth_yoy": 0.20,
        }

        labels = {
            "revenue_growth_yoy": "Revenue Growth (YoY)",
            "net_income_growth_yoy": "Net Income Growth (YoY)",
            "ebitda_growth_yoy": "EBITDA Growth (YoY)",
            "fcf_growth_yoy": "FCF Growth (YoY)",
        }

        for key, label in labels.items():
            component_scores[key] = self._score_metric(
                _find(growth_metrics, key), DEFAULT_GROWTH_BENCHMARKS,
                key, label, strengths, weaknesses, notes
            )

        composite = _weighted_average(component_scores, weights)

        # Consistency bonus: all four metrics positive
        all_vals = [_get_val(_find(growth_metrics, k)) for k in weights]
        valid_vals = [v for v in all_vals if v is not None]
        if valid_vals and all(v > 0 for v in valid_vals):
            bonus = min(5.0, composite * 0.05)
            composite = min(100.0, composite + bonus)
            notes.append(
                f"Consistency bonus of {bonus:.1f} points applied: "
                "all available growth metrics are positive."
            )

        data_coverage = sum(1 for v in all_vals if v is not None) / len(weights)

        return ScoreResult(
            score=round(composite, 1),
            grade=_grade(composite),
            component_scores=component_scores,
            weights_used=weights,
            strengths=strengths,
            weaknesses=weaknesses,
            methodology_notes=notes,
            data_coverage=data_coverage,
        )

    # =========================================================================
    # PROFITABILITY SCORE
    # =========================================================================

    def profitability_score(
        self,
        profitability_metrics: list[CalculationResult],
        peer_metrics: Optional[list[CalculationResult]] = None,
        benchmark_overrides: Optional[dict] = None,
    ) -> ScoreResult:
        """
        Standalone Profitability Score (0–100).

        When peer_metrics is provided, the benchmark for each metric is
        dynamically set to the peer median (±1 standard deviation for
        good/bad thresholds). This enables true peer-relative scoring.

        Sub-components and weights:
          - Gross Margin          20%
          - Operating Margin      20%
          - Net Profit Margin     15%
          - EBITDA Margin         20%
          - ROE                   12.5%
          - ROIC                  12.5%

        Methodology note on peer comparison:
          Peer median becomes the "average" (score ~55); peer 75th percentile
          maps to ~85 (strong); peer 25th percentile maps to ~35 (weak).
          This ensures the score is industry-context-aware.
        """
        bm_overrides = benchmark_overrides or self._overrides
        strengths: list[str] = []
        weaknesses: list[str] = []
        notes: list[str] = []
        component_scores: dict[str, float] = {}

        weights = {
            "gross_margin": 0.20,
            "operating_margin": 0.20,
            "net_profit_margin": 0.15,
            "ebitda_margin": 0.20,
            "return_on_equity": 0.125,
            "return_on_invested_capital": 0.125,
        }

        if peer_metrics:
            notes.append(
                "Peer comparison mode: benchmarks derived from peer median and quartiles."
            )
            dynamic_benchmarks = self._derive_peer_benchmarks(peer_metrics, list(weights.keys()))
        else:
            notes.append(
                "Absolute benchmark mode: cross-industry defaults applied "
                "(no peer group provided)."
            )
            dynamic_benchmarks = DEFAULT_PROFITABILITY_BENCHMARKS

        labels = {
            "gross_margin": "Gross Margin",
            "operating_margin": "Operating Margin",
            "net_profit_margin": "Net Profit Margin",
            "ebitda_margin": "EBITDA Margin",
            "return_on_equity": "Return on Equity (ROE)",
            "return_on_invested_capital": "ROIC",
        }

        for key, label in labels.items():
            component_scores[key] = self._score_metric(
                _find(profitability_metrics, key),
                dynamic_benchmarks,
                key,
                label,
                strengths,
                weaknesses,
                notes,
            )

        composite = _weighted_average(component_scores, weights)
        all_vals = [_get_val(_find(profitability_metrics, k)) for k in weights]
        data_coverage = sum(1 for v in all_vals if v is not None) / len(weights)

        return ScoreResult(
            score=round(composite, 1),
            grade=_grade(composite),
            component_scores=component_scores,
            weights_used=weights,
            strengths=strengths,
            weaknesses=weaknesses,
            methodology_notes=notes,
            data_coverage=data_coverage,
        )

    def _derive_peer_benchmarks(
        self,
        peer_results: list[CalculationResult],
        metric_names: list[str],
    ) -> dict[str, dict]:
        """
        Compute dynamic benchmarks from a set of peer CalculationResults.

        For each metric:
          - "bad"  = 25th percentile of peer values
          - "good" = 75th percentile of peer values

        Falls back to default benchmarks when fewer than 3 peer data points
        are available for a given metric.
        """
        import numpy as np

        benchmarks: dict[str, dict] = {}

        for metric in metric_names:
            peer_vals = [
                r.value for r in peer_results
                if r.metric_name == metric and r.value is not None
            ]
            if len(peer_vals) >= 3:
                arr = np.array(peer_vals)
                p25 = float(np.percentile(arr, 25))
                p75 = float(np.percentile(arr, 75))
                # Determine directionality: higher is better for margins/returns
                is_reverse = metric in {"capex_intensity", "debt_to_equity", "debt_to_ebitda"}
                benchmarks[metric] = {
                    "bad": p25,
                    "good": p75,
                    "reverse": is_reverse,
                }
            else:
                default = DEFAULT_PROFITABILITY_BENCHMARKS.get(metric)
                if default:
                    benchmarks[metric] = default

        return benchmarks

    # =========================================================================
    # GOVERNANCE SCORE
    # =========================================================================

    def governance_score(
        self,
        governance_data: dict,
    ) -> ScoreResult:
        """
        Governance Score (0–100) based on qualitative and semi-quantitative
        governance indicators.

        Expected keys in governance_data (all optional — missing = excluded):

          board_independence_pct: float    — fraction of independent directors (0–1)
          ceo_chair_separation: bool       — True if CEO ≠ Chairman
          audit_committee_independent: bool — True if audit committee fully independent
          compensation_tied_to_performance: bool — True if >50% comp is performance-based
          insider_ownership_pct: float     — fraction of shares held by insiders (0–1)
          institutional_ownership_pct: float — fraction held by institutions
          has_dual_class_shares: bool      — True = potential governance concern
          shareholder_rights_score: int    — 1–5 scale (ISS/similar)
          say_on_pay_approval_pct: float   — most recent say-on-pay vote % approval
          board_tenure_avg_years: float    — average director tenure

        Weights:
          - Board independence         25%
          - Compensation alignment     25%
          - Ownership structure        20%
          - Shareholder rights         15%
          - Audit / oversight          15%
        """
        strengths: list[str] = []
        weaknesses: list[str] = []
        notes: list[str] = [
            "Governance score weights: Board Independence 25%, "
            "Compensation Alignment 25%, Ownership Structure 20%, "
            "Shareholder Rights 15%, Audit/Oversight 15%."
        ]
        component_scores: dict[str, float] = {}
        weights = {
            "board_independence": 0.25,
            "compensation_alignment": 0.25,
            "ownership_structure": 0.20,
            "shareholder_rights": 0.15,
            "audit_oversight": 0.15,
        }

        # ── Board Independence ────────────────────────────────────────────────
        bd_indep = governance_data.get("board_independence_pct")
        ceo_chair = governance_data.get("ceo_chair_separation")
        bd_score = -1.0

        if bd_indep is not None:
            bd_indep_score = _linear_score(bd_indep, 0.40, 0.85)
            if bd_indep >= 0.75:
                strengths.append(
                    f"Board is {bd_indep:.0%} independent "
                    f"(threshold for strong governance: ≥75%)"
                )
            elif bd_indep < 0.50:
                weaknesses.append(
                    f"Board independence is low: {bd_indep:.0%} "
                    f"(below 50% minimum best practice)"
                )
        else:
            bd_indep_score = 50.0  # neutral when unknown
            notes.append("Board independence % not provided; neutral score applied")

        if ceo_chair is not None:
            ceo_bonus = 10.0 if ceo_chair else -10.0
            bd_indep_score = max(0.0, min(100.0, bd_indep_score + ceo_bonus))
            if ceo_chair:
                strengths.append("CEO and Chairman roles are separated (governance best practice)")
            else:
                weaknesses.append("CEO also serves as Chairman — combined role reduces board oversight")

        component_scores["board_independence"] = bd_indep_score

        # ── Compensation Alignment ────────────────────────────────────────────
        comp_perf = governance_data.get("compensation_tied_to_performance")
        sop = governance_data.get("say_on_pay_approval_pct")
        comp_score = 50.0  # neutral default

        if comp_perf is True:
            comp_score = min(100.0, comp_score + 30.0)
            strengths.append("Compensation is tied to performance metrics")
        elif comp_perf is False:
            comp_score = max(0.0, comp_score - 30.0)
            weaknesses.append("Compensation is not primarily performance-based")

        if sop is not None:
            sop_score = _linear_score(sop, 0.60, 0.95)
            comp_score = (comp_score + sop_score) / 2.0
            if sop >= 0.90:
                strengths.append(
                    f"Strong say-on-pay support: {sop:.0%} shareholder approval"
                )
            elif sop < 0.70:
                weaknesses.append(
                    f"Low say-on-pay approval: {sop:.0%} "
                    f"(below 70% — indicates shareholder dissatisfaction with compensation)"
                )

        component_scores["compensation_alignment"] = comp_score

        # ── Ownership Structure ───────────────────────────────────────────────
        insider_own = governance_data.get("insider_ownership_pct")
        inst_own = governance_data.get("institutional_ownership_pct")
        dual_class = governance_data.get("has_dual_class_shares")
        own_score = 50.0

        if insider_own is not None:
            # Sweet spot: 5–20% insider ownership aligns incentives without
            # entrenching management. >40% may entrench; <2% lacks skin in game.
            if 0.05 <= insider_own <= 0.20:
                own_score = min(100.0, own_score + 20.0)
                strengths.append(
                    f"Insider ownership at {insider_own:.0%} — "
                    f"well-aligned incentive range (5–20%)"
                )
            elif insider_own < 0.02:
                own_score = max(0.0, own_score - 15.0)
                weaknesses.append(
                    f"Low insider ownership ({insider_own:.0%}) — "
                    f"limited management skin in the game"
                )
            elif insider_own > 0.40:
                own_score = max(0.0, own_score - 10.0)
                weaknesses.append(
                    f"High insider concentration ({insider_own:.0%}) — "
                    f"potential entrenchment risk"
                )

        if dual_class is True:
            own_score = max(0.0, own_score - 20.0)
            weaknesses.append(
                "Dual-class share structure reduces public shareholder voting rights"
            )
        elif dual_class is False:
            own_score = min(100.0, own_score + 5.0)
            strengths.append("Single class share structure — equal voting rights")

        component_scores["ownership_structure"] = own_score

        # ── Shareholder Rights ────────────────────────────────────────────────
        shr_rights = governance_data.get("shareholder_rights_score")  # 1–5
        shr_score = -1.0
        if shr_rights is not None:
            shr_score = _linear_score(float(shr_rights), 1.0, 5.0)
            if shr_rights >= 4:
                strengths.append(
                    f"Shareholder rights score: {shr_rights}/5 (strong)"
                )
            elif shr_rights <= 2:
                weaknesses.append(
                    f"Shareholder rights score: {shr_rights}/5 (weak)"
                )
        component_scores["shareholder_rights"] = shr_score

        # ── Audit / Oversight ─────────────────────────────────────────────────
        audit_indep = governance_data.get("audit_committee_independent")
        audit_score = 50.0
        if audit_indep is True:
            audit_score = 85.0
            strengths.append("Audit committee is fully independent")
        elif audit_indep is False:
            audit_score = 25.0
            weaknesses.append(
                "Audit committee is not fully independent — "
                "oversight integrity may be compromised"
            )
        else:
            notes.append("Audit committee independence data not provided; neutral score applied")

        component_scores["audit_oversight"] = audit_score

        composite = _weighted_average(component_scores, weights)
        present = sum(1 for v in component_scores.values() if v >= 0)
        data_coverage = present / len(weights)

        if data_coverage < 0.5:
            notes.append(
                f"Limited governance data: only {data_coverage:.0%} of expected "
                "fields provided. Governance score should be treated as preliminary."
            )

        return ScoreResult(
            score=round(composite, 1),
            grade=_grade(composite),
            component_scores=component_scores,
            weights_used=weights,
            strengths=strengths,
            weaknesses=weaknesses,
            methodology_notes=notes,
            data_coverage=data_coverage,
        )

    # =========================================================================
    # RISK SCORE
    # =========================================================================

    def risk_score(
        self,
        risk_factors: dict,
    ) -> ScoreResult:
        """
        Risk Score (0–100, higher = lower risk / better risk profile).

        Synthesises quantitative risk factors (from financial ratios) and
        qualitative risk indicators into a single risk score.

        Expected keys in risk_factors (all optional):

        Quantitative (CalculationResult objects):
          leverage_result:        CalculationResult for debt_to_ebitda
          interest_coverage_result: CalculationResult for interest_coverage
          current_ratio_result:   CalculationResult for current_ratio
          fcf_margin_result:      CalculationResult for fcf_margin

        Qualitative (bool or float):
          revenue_concentration_pct: float  — % revenue from top customer (0–1)
          geographic_concentration: bool    — True if >70% revenue from one region
          customer_count_small: bool        — True if <10 customers
          regulatory_risk_high: bool        — True if subject to heavy regulation risk
          management_tenure_avg_years: float
          audit_opinion_clean: bool         — True = unqualified audit opinion
          material_weakness_reported: bool  — True = SEC-disclosed material weakness
          litigation_material: bool         — True = material pending litigation

        Weights:
          - Financial risk        40%  (leverage, coverage, liquidity, FCF)
          - Concentration risk    25%  (revenue, customer, geographic)
          - Operational risk      20%  (management, material weakness, litigation)
          - Regulatory risk       15%
        """
        strengths: list[str] = []
        weaknesses: list[str] = []
        notes: list[str] = [
            "Risk score: higher score = LOWER risk. "
            "Weights: Financial 40%, Concentration 25%, Operational 20%, Regulatory 15%."
        ]
        component_scores: dict[str, float] = {}
        weights = {
            "financial_risk": 0.40,
            "concentration_risk": 0.25,
            "operational_risk": 0.20,
            "regulatory_risk": 0.15,
        }

        # ── Financial Risk ────────────────────────────────────────────────────
        fin_scores: list[float] = []

        leverage = risk_factors.get("leverage_result")
        if isinstance(leverage, CalculationResult) and leverage.value is not None:
            s = _linear_score(leverage.value, 6.0, 0.0, reverse=True)
            fin_scores.append(s)
            if leverage.value > 4.0:
                weaknesses.append(
                    f"Elevated leverage: Net Debt/EBITDA = {leverage.value:.1f}x "
                    f"(threshold of concern: >4x)"
                )
            elif leverage.value < 1.5:
                strengths.append(
                    f"Low leverage: Net Debt/EBITDA = {leverage.value:.1f}x "
                    f"(strong balance sheet)"
                )

        ic = risk_factors.get("interest_coverage_result")
        if isinstance(ic, CalculationResult) and ic.value is not None:
            s = _linear_score(ic.value, 1.0, 10.0)
            fin_scores.append(s)
            if ic.value < 2.0:
                weaknesses.append(
                    f"Thin interest coverage: {ic.value:.1f}x "
                    f"(below 2x signals debt service risk)"
                )
            elif ic.value > 8.0:
                strengths.append(
                    f"Strong interest coverage: {ic.value:.1f}x"
                )

        cr = risk_factors.get("current_ratio_result")
        if isinstance(cr, CalculationResult) and cr.value is not None:
            s = _linear_score(cr.value, 0.5, 2.5)
            fin_scores.append(s)
            if cr.value < 1.0:
                weaknesses.append(
                    f"Current ratio below 1.0: {cr.value:.2f}x "
                    f"(current liabilities exceed current assets)"
                )

        fcf_m = risk_factors.get("fcf_margin_result")
        if isinstance(fcf_m, CalculationResult) and fcf_m.value is not None:
            s = _linear_score(fcf_m.value, -0.05, 0.20)
            fin_scores.append(s)
            if fcf_m.value < 0:
                weaknesses.append(
                    f"Negative FCF margin: {fcf_m.value:.1%} — "
                    f"company is cash-burning; requires external financing"
                )

        component_scores["financial_risk"] = (
            sum(fin_scores) / len(fin_scores) if fin_scores else -1.0
        )

        # ── Concentration Risk ────────────────────────────────────────────────
        conc_scores: list[float] = []

        rev_conc = risk_factors.get("revenue_concentration_pct")
        if rev_conc is not None:
            s = _linear_score(float(rev_conc), 0.50, 0.05, reverse=True)
            conc_scores.append(s)
            if rev_conc > 0.30:
                weaknesses.append(
                    f"High revenue concentration: top customer represents "
                    f"{rev_conc:.0%} of revenue"
                )
            elif rev_conc < 0.10:
                strengths.append(
                    f"Well-diversified revenue: largest customer is "
                    f"{rev_conc:.0%} of total"
                )

        if risk_factors.get("geographic_concentration"):
            conc_scores.append(20.0)
            weaknesses.append(
                "Geographic concentration: >70% of revenue from single region"
            )
        elif "geographic_concentration" in risk_factors:
            conc_scores.append(80.0)
            strengths.append("Geographically diversified revenue base")

        if risk_factors.get("customer_count_small"):
            conc_scores.append(15.0)
            weaknesses.append(
                "Small customer count (<10) creates material customer loss risk"
            )

        component_scores["concentration_risk"] = (
            sum(conc_scores) / len(conc_scores) if conc_scores else -1.0
        )

        # ── Operational Risk ──────────────────────────────────────────────────
        op_scores: list[float] = []

        mgmt_tenure = risk_factors.get("management_tenure_avg_years")
        if mgmt_tenure is not None:
            s = _linear_score(float(mgmt_tenure), 1.0, 8.0)
            op_scores.append(s)
            if mgmt_tenure < 2.0:
                weaknesses.append(
                    f"Short average management tenure: {mgmt_tenure:.1f} years "
                    f"(high turnover risk)"
                )
            elif mgmt_tenure >= 6.0:
                strengths.append(
                    f"Experienced management team: avg tenure {mgmt_tenure:.1f} years"
                )

        if risk_factors.get("material_weakness_reported"):
            op_scores.append(5.0)
            weaknesses.append(
                "Material weakness in internal controls reported to SEC — "
                "financial reporting reliability risk"
            )
        elif "material_weakness_reported" in risk_factors:
            op_scores.append(90.0)
            strengths.append("No material weaknesses in internal controls reported")

        if risk_factors.get("audit_opinion_clean") is False:
            op_scores.append(10.0)
            weaknesses.append(
                "Audit opinion is not clean (qualified / going concern) — "
                "significant financial reporting risk"
            )
        elif risk_factors.get("audit_opinion_clean"):
            op_scores.append(85.0)

        if risk_factors.get("litigation_material"):
            op_scores.append(30.0)
            weaknesses.append(
                "Material litigation pending — potential for significant financial liability"
            )

        component_scores["operational_risk"] = (
            sum(op_scores) / len(op_scores) if op_scores else -1.0
        )

        # ── Regulatory Risk ───────────────────────────────────────────────────
        reg_risk = risk_factors.get("regulatory_risk_high")
        if reg_risk is True:
            component_scores["regulatory_risk"] = 25.0
            weaknesses.append(
                "High regulatory risk: company operates in heavily regulated sector "
                "with material compliance exposure"
            )
        elif reg_risk is False:
            component_scores["regulatory_risk"] = 80.0
            strengths.append("Low regulatory risk environment")
        else:
            component_scores["regulatory_risk"] = -1.0
            notes.append("Regulatory risk classification not provided; excluded from score")

        composite = _weighted_average(component_scores, weights)
        present = sum(1 for v in component_scores.values() if v >= 0)
        data_coverage = present / len(weights)

        return ScoreResult(
            score=round(composite, 1),
            grade=_grade(composite),
            component_scores=component_scores,
            weights_used=weights,
            strengths=strengths,
            weaknesses=weaknesses,
            methodology_notes=notes,
            data_coverage=data_coverage,
        )
