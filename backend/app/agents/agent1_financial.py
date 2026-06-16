"""
agent1_financial.py — Financial Statement Analyst agent.

Analyzes pre-calculated financial ratios from the calculation engine and
produces a structured assessment of revenue trends, profitability, cash flow
quality, and balance sheet health.

Input: list of CalculationResult dicts produced by financial_ratios.py
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from .base import SYSTEM_PROMPT_BASE, AgentOutput, BaseAgent, Evidence, MODEL

logger = logging.getLogger(__name__)

_ROLE = "Senior Financial Statement Analyst specializing in fundamental analysis"

_SYSTEM_PROMPT = SYSTEM_PROMPT_BASE.format(role=_ROLE) + """
You will receive a packet of pre-calculated financial ratios and metrics for a
public company. Analyze the data and produce a structured JSON response that
matches the schema below EXACTLY.

OUTPUT SCHEMA:
{
  "revenue_analysis": {
    "trend": "<accelerating|decelerating|stable|volatile>",
    "cagr_3y": <number or null>,
    "commentary": "<string citing specific growth rates from data>",
    "evidence_refs": ["<metric_name_1>", "<metric_name_2>"]
  },
  "profitability_analysis": {
    "gross_margin_trend": "<expanding|contracting|stable>",
    "operating_leverage": "<positive|negative|neutral>",
    "commentary": "<string>",
    "evidence_refs": []
  },
  "cash_flow_quality": {
    "fcf_conversion": <number or null>,
    "accruals_ratio": <number or null>,
    "commentary": "<string>",
    "evidence_refs": []
  },
  "balance_sheet_health": {
    "leverage_assessment": "<conservative|moderate|aggressive|distressed>",
    "liquidity_assessment": "<strong|adequate|tight|critical>",
    "commentary": "<string>",
    "evidence_refs": []
  },
  "financial_strength_score": <0-100>,
  "growth_score": <0-100>,
  "profitability_score": <0-100>,
  "key_strengths": ["<specific strength with data point>"],
  "key_concerns": ["<specific concern with data point>"],
  "analyst_summary": "<3-5 sentence professional summary>"
}

Rules for evidence_refs: list the exact metric_name values from the data
packet that support each section. If a metric is missing or its value is null,
note "insufficient data" in the commentary — do NOT invent a figure.
"""

_USER_PROMPT_TEMPLATE = """
TICKER: {ticker}

FINANCIAL METRICS DATA PACKET:
{metrics_json}

DATA QUALITY NOTES:
{quality_notes}

Analyze the financial data above and return your assessment as valid JSON
matching the schema in your system prompt. Cite specific metric names and
values from the data packet. Where data is missing, state "insufficient data".
"""


class FinancialAnalystAgent(BaseAgent):
    """
    Agent 1 — Financial Statement Analysis.

    Analyzes pre-calculated financial ratios and returns a structured
    assessment with scored dimensions and evidence-backed commentary.
    """

    async def analyze(self, data_bundle: Any) -> AgentOutput:
        """
        Analyze pre-calculated financial ratios.

        Args:
            data_bundle: dict with keys:
                - "ticker": str
                - "calculation_results": list of CalculationResult dicts
                - "quality_notes": list[str] (optional)

        Returns:
            AgentOutput with financial statement analysis.
        """
        ticker = ""
        quality_notes: list[str] = []
        calc_results: list[dict] = []

        if isinstance(data_bundle, dict):
            ticker = data_bundle.get("ticker", "UNKNOWN")
            quality_notes = data_bundle.get("quality_notes", [])
            raw = data_bundle.get("calculation_results", data_bundle.get("results", []))
            if isinstance(raw, list):
                calc_results = [
                    r if isinstance(r, dict) else vars(r) for r in raw
                ]
        elif isinstance(data_bundle, list):
            calc_results = [
                r if isinstance(r, dict) else vars(r) for r in data_bundle
            ]

        evidence = self._build_evidence_from_data(
            {"calculation_results": calc_results}
        )

        metrics_json = json.dumps(calc_results, indent=2, default=str)
        quality_str = "\n".join(quality_notes) if quality_notes else "None reported."

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            ticker=ticker,
            metrics_json=metrics_json,
            quality_notes=quality_str,
        )

        response_text, tokens_used = await self._run_analysis(_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_structured_output(response_text)

        missing_data = [
            e.metric_name or e.claim
            for e in evidence
            if e.value is None
        ]

        # Derive overall confidence from evidence coverage
        total = len(evidence)
        populated = sum(1 for e in evidence if e.value is not None)
        confidence = (populated / total) if total > 0 else 0.0

        data_quality_warnings: list[str] = list(quality_notes)
        if not calc_results:
            data_quality_warnings.append(
                "No calculation results provided — analysis based on empty data packet."
            )

        return AgentOutput(
            agent_name="FinancialAnalystAgent",
            ticker=ticker,
            analysis=parsed,
            evidence=evidence,
            confidence=round(confidence, 3),
            data_quality_warnings=data_quality_warnings,
            missing_data=missing_data,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_used=MODEL,
            tokens_used=tokens_used,
        )
