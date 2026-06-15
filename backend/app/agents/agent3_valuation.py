"""
agent3_valuation.py — Valuation Analyst agent.

Performs valuation analysis from pre-calculated multiples and comparable
company data. DCF analysis is only executed when the caller supplies explicit
assumptions (WACC, terminal growth rate, projection period) — if not provided,
the DCF section is marked "assumptions_required" and the agent never invents
figures.

Input: Pre-calculated valuation metrics and comps from the valuation engine,
       plus optional DCF assumptions from the user.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from .base import SYSTEM_PROMPT_BASE, AgentOutput, BaseAgent, Evidence, MODEL

logger = logging.getLogger(__name__)

_ROLE = "Senior Equity Valuation Analyst specializing in intrinsic value and relative valuation"

_DCF_ASSUMPTIONS_REQUIRED = {
    "status": "assumptions_required",
    "message": (
        "DCF requires explicit user-provided assumptions (WACC, terminal growth rate, "
        "projection period). None were provided. Supply dcf_assumptions to enable DCF analysis."
    ),
}

_SYSTEM_PROMPT = SYSTEM_PROMPT_BASE.format(role=_ROLE) + """
You will receive pre-calculated trading multiples, comparable company data, and
optionally a completed DCF model. Analyze only the data provided and return a
structured JSON response matching the schema below EXACTLY.

CRITICAL DCF RULE: If the dcf_analysis field in the input is
{"status": "assumptions_required", ...}, copy it verbatim into your output —
do NOT attempt to calculate or estimate a DCF. NEVER invent WACC, growth rates,
or terminal values.

OUTPUT SCHEMA:
{
  "trading_multiples": {
    "pe_ratio": <number or null>,
    "ev_ebitda": <number or null>,
    "ev_revenue": <number or null>,
    "p_fcf": <number or null>,
    "vs_peers": {
      "pe_premium_discount_pct": <number or null>,
      "ev_ebitda_premium_discount_pct": <number or null>
    }
  },
  "comps_implied_value": {
    "low": <number or null>,
    "midpoint": <number or null>,
    "high": <number or null>,
    "methodology": "<string explaining which multiples and peers were used>"
  },
  "dcf_analysis": <assumptions_required object OR full DCF result from input>,
  "margin_of_safety": <number or null>,
  "valuation_summary": "<cheap|fair|expensive|significantly_overvalued|insufficient_data>",
  "current_price": <number or null>,
  "analyst_summary": "<string>"
}

Rules:
- pe_ratio, ev_ebitda, ev_revenue, p_fcf: use values from the data packet.
  If not available, set to null.
- margin_of_safety: (implied_value_midpoint - current_price) / current_price * 100.
  Set to null if either value is unavailable.
- valuation_summary: base this strictly on the multiples and comps provided.
- All commentary must cite specific metrics from the input.
"""

_USER_PROMPT_TEMPLATE = """
TICKER: {ticker}
COMPANY: {company_name}
CURRENT PRICE: {current_price}

VALUATION METRICS DATA PACKET:
{valuation_json}

COMPARABLE COMPANIES:
{comps_json}

DCF ANALYSIS INPUT:
{dcf_json}

DATA QUALITY NOTES:
{quality_notes}

Analyze the valuation data above and return your assessment as valid JSON
matching the schema in your system prompt. Where data is missing, set fields
to null and note "insufficient data" in your analyst_summary.
"""


class ValuationAnalystAgent(BaseAgent):
    """
    Agent 3 — Valuation Analysis.

    Analyzes pre-calculated multiples and comparable company data.
    DCF analysis requires explicit user-provided assumptions.
    """

    async def analyze(self, data_bundle: Any) -> AgentOutput:
        """
        Analyze valuation metrics and produce a valuation assessment.

        Args:
            data_bundle: dict with keys:
                - "ticker": str
                - "company_name": str (optional)
                - "current_price": float | None
                - "valuation_metrics": dict of pre-calculated metrics
                - "comparable_companies": list of peer multiples dicts
                - "dcf_assumptions": dict | None  — if None, DCF section
                  will be marked "assumptions_required"
                - "dcf_results": dict | None  — pre-computed DCF output
                - "quality_notes": list[str] (optional)

        Returns:
            AgentOutput with valuation assessment.
        """
        ticker = "UNKNOWN"
        company_name = ""
        current_price: float | None = None
        valuation_metrics: dict = {}
        comparable_companies: list = []
        dcf_assumptions: dict | None = None
        dcf_results: dict | None = None
        quality_notes: list[str] = []

        if isinstance(data_bundle, dict):
            ticker = data_bundle.get("ticker", "UNKNOWN")
            company_name = data_bundle.get("company_name", ticker)
            current_price = data_bundle.get("current_price")
            valuation_metrics = data_bundle.get("valuation_metrics", {})
            comparable_companies = data_bundle.get("comparable_companies", [])
            dcf_assumptions = data_bundle.get("dcf_assumptions")
            dcf_results = data_bundle.get("dcf_results")
            quality_notes = data_bundle.get("quality_notes", [])

        # Determine DCF input: only use results if assumptions were explicitly provided
        if dcf_assumptions and dcf_results:
            dcf_input = dcf_results
        else:
            dcf_input = _DCF_ASSUMPTIONS_REQUIRED

        # Build evidence
        evidence: list[Evidence] = []

        def _add_ev(claim: str, value: Any, metric_name: str, source: str = "FMP") -> None:
            evidence.append(
                Evidence(
                    claim=claim,
                    value=value if isinstance(value, (int, float)) else None,
                    source=source,
                    filing_type=None,
                    period=str(valuation_metrics.get("period", "")),
                    metric_name=metric_name,
                    formula=valuation_metrics.get(f"{metric_name}_formula"),
                )
            )

        for key, val in valuation_metrics.items():
            if isinstance(val, (int, float)) and not key.endswith("_formula"):
                _add_ev(f"{key}: {val}", val, key)

        if current_price is not None:
            evidence.append(
                Evidence(
                    claim=f"current_price: {current_price}",
                    value=current_price,
                    source="YAHOO",
                    filing_type=None,
                    period=None,
                    metric_name="current_price",
                    formula=None,
                )
            )

        missing_data: list[str] = []
        if not valuation_metrics:
            missing_data.append("valuation_metrics")
            quality_notes = list(quality_notes) + [
                "No pre-calculated valuation metrics provided."
            ]
        if not comparable_companies:
            missing_data.append("comparable_companies")
        if dcf_input.get("status") == "assumptions_required":
            missing_data.append("dcf_assumptions")

        total = len(evidence)
        populated = sum(1 for e in evidence if e.value is not None)
        confidence = (populated / total) if total > 0 else 0.0

        valuation_json = json.dumps(valuation_metrics, indent=2, default=str)
        comps_json = json.dumps(comparable_companies, indent=2, default=str)
        dcf_json = json.dumps(dcf_input, indent=2, default=str)
        quality_str = "\n".join(quality_notes) if quality_notes else "None reported."
        price_str = str(current_price) if current_price is not None else "unavailable"

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            current_price=price_str,
            valuation_json=valuation_json,
            comps_json=comps_json,
            dcf_json=dcf_json,
            quality_notes=quality_str,
        )

        response_text, tokens_used = await self._run_analysis(_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_structured_output(response_text)

        # Enforce DCF rule: if assumptions were not provided, overwrite whatever
        # the model may have put in dcf_analysis with the canonical object
        if dcf_input.get("status") == "assumptions_required":
            if isinstance(parsed, dict):
                parsed["dcf_analysis"] = _DCF_ASSUMPTIONS_REQUIRED

        return AgentOutput(
            agent_name="ValuationAnalystAgent",
            ticker=ticker,
            analysis=parsed,
            evidence=evidence,
            confidence=round(confidence, 3),
            data_quality_warnings=list(quality_notes),
            missing_data=missing_data,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_used=MODEL,
            tokens_used=tokens_used,
        )
