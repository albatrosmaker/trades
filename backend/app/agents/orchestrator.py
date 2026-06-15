"""
orchestrator.py — ResearchOrchestrator coordinates the full AI research pipeline.

Flow:
  1. Fetch raw company data via DataOrchestrator
  2. Run financial ratio calculations on the raw data
  3. Run agents 1–4 in parallel (asyncio.gather)
  4. Feed all results to agent 5 (Investment Committee)
  5. Return FullResearchResult

Design principles:
  - Agents never see raw market data — they receive pre-computed packets.
  - DCF assumptions are never invented — callers must supply them explicitly.
  - All errors are logged and surfaced in data_quality_warnings; the pipeline
    does not fail silently.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ..data.data_orchestrator import CompanyDataBundle, DataOrchestrator
from .agent1_financial import FinancialAnalystAgent
from .agent2_governance import GovernanceAnalystAgent
from .agent3_valuation import ValuationAnalystAgent
from .agent4_risk import RiskAnalystAgent
from .agent5_investment_committee import InvestmentCommitteeAgent
from .base import AgentOutput

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class FullResearchResult:
    """
    Complete research output aggregating all five agent analyses.

    data_quality_score mirrors the DataOrchestrator score (0–100).
    total_evidence_count is the sum of evidence items across all agents.
    """

    ticker: str
    company_name: str
    financial_analysis: AgentOutput
    governance_analysis: AgentOutput
    valuation_analysis: AgentOutput
    risk_analysis: AgentOutput
    investment_committee: AgentOutput
    data_quality_score: float
    total_evidence_count: int
    generated_at: str  # ISO timestamp
    analysis_duration_seconds: float


# ---------------------------------------------------------------------------
# Helpers: build agent-specific data bundles from CompanyDataBundle
# ---------------------------------------------------------------------------


def _extract_risk_factors_text(latest_10k: dict) -> str:
    """
    Extract risk factors text from a 10-K filing dict.

    Tries common keys used by the EDGAR parser. Returns empty string
    if none are found.
    """
    for key in (
        "risk_factors",
        "riskFactors",
        "item_1a",
        "Item 1A",
        "risk_factors_text",
    ):
        value = latest_10k.get(key, "")
        if value and isinstance(value, str):
            return value

    # Fallback: look inside a nested "sections" dict
    sections = latest_10k.get("sections", {})
    if isinstance(sections, dict):
        for key in ("risk_factors", "item_1a", "1A"):
            value = sections.get(key, "")
            if value and isinstance(value, str):
                return value

    return ""


def _build_financial_bundle(
    bundle: CompanyDataBundle,
    calculation_results: list[dict],
) -> dict:
    return {
        "ticker": bundle.ticker,
        "calculation_results": calculation_results,
        "quality_notes": bundle.missing_data_fields,
    }


def _build_governance_bundle(bundle: CompanyDataBundle) -> dict:
    company_name = bundle.company_profile.get("companyName", bundle.ticker)
    return {
        "ticker": bundle.ticker,
        "company_name": company_name,
        "proxy_data": bundle.proxy_data,
        "insider_transactions": bundle.insider_transactions,
        "quality_notes": bundle.missing_data_fields,
    }


def _build_valuation_bundle(
    bundle: CompanyDataBundle,
    valuation_metrics: dict,
    comparable_companies: list,
    dcf_assumptions: dict | None,
    dcf_results: dict | None,
) -> dict:
    company_name = bundle.company_profile.get("companyName", bundle.ticker)
    return {
        "ticker": bundle.ticker,
        "company_name": company_name,
        "current_price": bundle.current_price,
        "valuation_metrics": valuation_metrics,
        "comparable_companies": comparable_companies,
        "dcf_assumptions": dcf_assumptions,
        "dcf_results": dcf_results,
        "quality_notes": bundle.missing_data_fields,
    }


def _build_risk_bundle(
    bundle: CompanyDataBundle,
    calculation_results: list[dict],
) -> dict:
    company_name = bundle.company_profile.get("companyName", bundle.ticker)
    risk_factors_text = _extract_risk_factors_text(bundle.latest_10k)
    return {
        "ticker": bundle.ticker,
        "company_name": company_name,
        "risk_factors_text": risk_factors_text,
        "financial_metrics": calculation_results,
        "recent_news": bundle.recent_news,
        "quality_notes": bundle.missing_data_fields,
    }


# ---------------------------------------------------------------------------
# Calculation engine integration
# ---------------------------------------------------------------------------


def _run_calculation_engine(bundle: CompanyDataBundle) -> list[dict]:
    """
    Run the financial ratio calculation engine on the raw data bundle.

    Returns a list of CalculationResult dicts. Any engine errors are
    caught and logged — the pipeline continues with partial results.
    """
    try:
        from ..calculations.financial_ratios import (
            calculate_all_ratios,
        )
        from ..calculations.field_mappings import normalize_fmp_data

        if not bundle.income_statements:
            logger.warning(
                "No income statements for %s — skipping ratio calculation.",
                bundle.ticker,
            )
            return []

        # Normalise the most recent period data
        latest_income = bundle.income_statements[0] if bundle.income_statements else {}
        latest_balance = bundle.balance_sheets[0] if bundle.balance_sheets else {}
        latest_cf = bundle.cash_flow_statements[0] if bundle.cash_flow_statements else {}
        prior_balance = bundle.balance_sheets[1] if len(bundle.balance_sheets) > 1 else {}

        normalized = normalize_fmp_data(
            income_stmt=latest_income,
            balance_sheet=latest_balance,
            cash_flow_stmt=latest_cf,
        )
        prior_normalized = normalize_fmp_data(
            income_stmt={},
            balance_sheet=prior_balance,
            cash_flow_stmt={},
        ) if prior_balance else None

        results = calculate_all_ratios(
            current=normalized,
            prior=prior_normalized,
        )

        return [vars(r) if not isinstance(r, dict) else r for r in results]

    except ImportError as exc:
        logger.warning("Calculation engine not available: %s", exc)
        return []
    except Exception as exc:
        logger.error(
            "Calculation engine failed for %s: %s",
            bundle.ticker,
            exc,
            exc_info=True,
        )
        return []


def _run_valuation_engine(
    bundle: CompanyDataBundle,
    calculation_results: list[dict],
    dcf_assumptions: dict | None,
) -> tuple[dict, list, dict | None]:
    """
    Run the valuation engine on pre-calculated metrics.

    Returns (valuation_metrics, comparable_companies, dcf_results).
    dcf_results is None when assumptions are not provided.
    """
    valuation_metrics: dict = {}
    comparable_companies: list = []
    dcf_results: dict | None = None

    try:
        # Build a minimal valuation_metrics dict from calculation results
        metric_map = {
            r["metric_name"]: r["value"]
            for r in calculation_results
            if isinstance(r, dict) and r.get("value") is not None
        }

        # Extract common valuation multiples from the company profile
        profile = bundle.company_profile
        valuation_metrics = {
            "pe_ratio": profile.get("pe") or profile.get("priceEarningsRatioTTM"),
            "ev_ebitda": profile.get("ev_ebitda") or profile.get("enterpriseValueOverEBITDA"),
            "ev_revenue": profile.get("ev_revenue") or profile.get("evToRevenue"),
            "p_fcf": profile.get("p_fcf") or profile.get("priceToFreeCashFlowsRatioTTM"),
            "market_cap": profile.get("mktCap"),
            "current_price": bundle.current_price,
            **metric_map,
        }
        # Remove None values
        valuation_metrics = {k: v for k, v in valuation_metrics.items() if v is not None}

        # DCF is only attempted when assumptions are explicitly provided
        if dcf_assumptions:
            try:
                from ..calculations.valuation import run_dcf

                dcf_results = run_dcf(
                    assumptions=dcf_assumptions,
                    financial_metrics=metric_map,
                )
            except (ImportError, Exception) as exc:
                logger.warning("DCF calculation failed: %s", exc)
                dcf_results = None

    except Exception as exc:
        logger.error("Valuation engine failed for %s: %s", bundle.ticker, exc)

    return valuation_metrics, comparable_companies, dcf_results


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class ResearchOrchestrator:
    """
    Coordinates the full AI research pipeline for a single company.

    Usage:
        orchestrator = ResearchOrchestrator()
        result = await orchestrator.run_full_analysis(ticker="AAPL")
    """

    def __init__(self) -> None:
        self._data_orchestrator = DataOrchestrator()
        self._agent1 = FinancialAnalystAgent()
        self._agent2 = GovernanceAnalystAgent()
        self._agent3 = ValuationAnalystAgent()
        self._agent4 = RiskAnalystAgent()
        self._agent5 = InvestmentCommitteeAgent()

    async def run_full_analysis(
        self,
        ticker: str,
        cik: str | None = None,
        dcf_assumptions: dict | None = None,
    ) -> FullResearchResult:
        """
        Run the complete AI research pipeline for a company.

        Steps:
          1. Fetch data via DataOrchestrator
          2. Run calculation engine (financial ratios + valuation metrics)
          3. Run agents 1–4 in parallel
          4. Feed results to agent 5 (Investment Committee)
          5. Return FullResearchResult

        Args:
            ticker: Stock ticker symbol (e.g. "AAPL").
            cik: Optional SEC CIK. Auto-resolved from ticker if omitted.
            dcf_assumptions: Optional dict with WACC, terminal_growth_rate,
                projection_years. If None, DCF analysis is skipped and the
                valuation agent will note "assumptions_required".

        Returns:
            FullResearchResult with all five agent outputs.

        Raises:
            RuntimeError: if data fetch or any agent call fails critically.
        """
        start_time = time.monotonic()

        ticker = ticker.upper().strip()
        logger.info("ResearchOrchestrator: starting full analysis for %s", ticker)

        # ------------------------------------------------------------------ #
        # Step 1: Fetch data                                                   #
        # ------------------------------------------------------------------ #
        bundle: CompanyDataBundle = await self._data_orchestrator.fetch_company_data(
            ticker=ticker,
            cik=cik,
            raise_on_insufficient_data=False,
        )
        company_name = bundle.company_profile.get("companyName", ticker)

        # ------------------------------------------------------------------ #
        # Step 2: Run calculation engines                                      #
        # ------------------------------------------------------------------ #
        calculation_results = _run_calculation_engine(bundle)
        valuation_metrics, comparable_companies, dcf_results = _run_valuation_engine(
            bundle, calculation_results, dcf_assumptions
        )

        # ------------------------------------------------------------------ #
        # Step 3: Build per-agent data bundles                                 #
        # ------------------------------------------------------------------ #
        financial_bundle = _build_financial_bundle(bundle, calculation_results)
        governance_bundle = _build_governance_bundle(bundle)
        valuation_bundle = _build_valuation_bundle(
            bundle, valuation_metrics, comparable_companies, dcf_assumptions, dcf_results
        )
        risk_bundle = _build_risk_bundle(bundle, calculation_results)

        # ------------------------------------------------------------------ #
        # Step 4: Run agents 1–4 in parallel                                  #
        # ------------------------------------------------------------------ #
        logger.info("ResearchOrchestrator: running agents 1-4 in parallel for %s", ticker)

        (
            financial_output,
            governance_output,
            valuation_output,
            risk_output,
        ) = await asyncio.gather(
            self._safe_analyze(self._agent1, financial_bundle, "FinancialAnalystAgent", ticker),
            self._safe_analyze(self._agent2, governance_bundle, "GovernanceAnalystAgent", ticker),
            self._safe_analyze(self._agent3, valuation_bundle, "ValuationAnalystAgent", ticker),
            self._safe_analyze(self._agent4, risk_bundle, "RiskAnalystAgent", ticker),
        )

        # ------------------------------------------------------------------ #
        # Step 5: Investment Committee synthesis                               #
        # ------------------------------------------------------------------ #
        logger.info(
            "ResearchOrchestrator: running Investment Committee agent for %s", ticker
        )
        committee_bundle = {
            "ticker": ticker,
            "company_name": company_name,
            "current_price": bundle.current_price,
            "financial_output": financial_output,
            "governance_output": governance_output,
            "valuation_output": valuation_output,
            "risk_output": risk_output,
        }
        investment_committee = await self._safe_analyze(
            self._agent5, committee_bundle, "InvestmentCommitteeAgent", ticker
        )

        # ------------------------------------------------------------------ #
        # Step 6: Aggregate result                                             #
        # ------------------------------------------------------------------ #
        all_outputs = [
            financial_output,
            governance_output,
            valuation_output,
            risk_output,
            investment_committee,
        ]
        total_evidence = sum(len(o.evidence) for o in all_outputs)
        duration = round(time.monotonic() - start_time, 2)

        logger.info(
            "ResearchOrchestrator: completed analysis for %s in %.1fs | "
            "evidence_items=%d | data_quality=%.1f",
            ticker,
            duration,
            total_evidence,
            bundle.data_quality_score,
        )

        return FullResearchResult(
            ticker=ticker,
            company_name=company_name,
            financial_analysis=financial_output,
            governance_analysis=governance_output,
            valuation_analysis=valuation_output,
            risk_analysis=risk_output,
            investment_committee=investment_committee,
            data_quality_score=bundle.data_quality_score,
            total_evidence_count=total_evidence,
            generated_at=datetime.now(timezone.utc).isoformat(),
            analysis_duration_seconds=duration,
        )

    # ---------------------------------------------------------------------- #
    # Private helpers                                                          #
    # ---------------------------------------------------------------------- #

    async def _safe_analyze(
        self,
        agent: Any,
        data_bundle: dict,
        agent_name: str,
        ticker: str,
    ) -> AgentOutput:
        """
        Run an agent's analyze() method and return its output safely.

        On failure, returns a degraded AgentOutput with the error recorded
        in data_quality_warnings rather than crashing the pipeline.
        """
        try:
            return await agent.analyze(data_bundle)
        except Exception as exc:
            logger.error(
                "Agent %s failed for %s: %s",
                agent_name,
                ticker,
                exc,
                exc_info=True,
            )
            from .base import MODEL
            return AgentOutput(
                agent_name=agent_name,
                ticker=ticker,
                analysis={
                    "error": str(exc),
                    "status": "agent_failed",
                },
                evidence=[],
                confidence=0.0,
                data_quality_warnings=[f"Agent failed: {exc}"],
                missing_data=["agent_output"],
                generated_at=datetime.now(timezone.utc).isoformat(),
                model_used=MODEL,
                tokens_used=0,
            )
