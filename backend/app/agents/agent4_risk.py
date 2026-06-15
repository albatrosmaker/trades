"""
agent4_risk.py — Risk Analyst agent.

Analyzes risk factors from SEC 10-K filings, cross-references them with
financial metrics, and produces a structured risk assessment. News headlines
are included as supplementary context only and are never the primary basis
for any risk conclusion.

Input:
  - SEC 10-K risk factors text (from latest_10k)
  - Pre-calculated financial ratios
  - News headlines (low-trust, supplementary only)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from .base import SYSTEM_PROMPT_BASE, AgentOutput, BaseAgent, Evidence, MODEL

logger = logging.getLogger(__name__)

_ROLE = "Senior Risk Analyst specializing in equity investment risk assessment"

_SYSTEM_PROMPT = SYSTEM_PROMPT_BASE.format(role=_ROLE) + """
You will receive:
  1. Risk factors text extracted from a SEC 10-K filing (PRIMARY SOURCE)
  2. Pre-calculated financial ratios that may signal financial risk (SECONDARY)
  3. Recent news headlines (LOW TRUST — supplementary context only, never
     the basis for a risk conclusion)

Your task:
  - Extract and categorize the ACTUAL risk factors stated in the 10-K filing.
  - Cross-reference financial risks with the financial ratio data provided.
  - Produce a bear case that is grounded in the actual 10-K risk factors.
  - Do NOT invent risk factors that are not in the data provided.

OUTPUT SCHEMA:
{
  "risk_categories": {
    "financial_risk": {
      "severity": "<Low|Moderate|High|Critical>",
      "factors": ["<specific factor from 10-K or financial data>"],
      "evidence": ["<metric_name: value or 10-K quote>"]
    },
    "operational_risk": {
      "severity": "<Low|Moderate|High|Critical>",
      "factors": [],
      "evidence": []
    },
    "regulatory_risk": {
      "severity": "<Low|Moderate|High|Critical>",
      "factors": [],
      "evidence": []
    },
    "competitive_risk": {
      "severity": "<Low|Moderate|High|Critical>",
      "factors": [],
      "evidence": []
    },
    "macro_risk": {
      "severity": "<Low|Moderate|High|Critical>",
      "factors": [],
      "evidence": []
    },
    "management_risk": {
      "severity": "<Low|Moderate|High|Critical>",
      "factors": [],
      "evidence": []
    }
  },
  "key_risk_factors": [
    "<top 5 risks extracted verbatim or closely paraphrased from SEC 10-K filing>"
  ],
  "financial_risk_signals": {
    "debt_concern": <true|false>,
    "liquidity_concern": <true|false>,
    "margin_compression": <true|false>
  },
  "bear_case": "<paragraph describing worst realistic scenario based on actual 10-K risk factors>",
  "worst_case_scenario": "<specific downside scenario with supporting logic from data>",
  "risk_score": <0-100>,
  "risk_rating": "<Low|Moderate|High|Very High>",
  "analyst_summary": "<string>"
}

News headlines: you may note sentiment patterns from news as supplementary
colour, but every risk_category factor and evidence item must trace back to
the 10-K filing or financial metrics. Label any news-derived observation
explicitly as "[NEWS — low trust]".
"""

_USER_PROMPT_TEMPLATE = """
TICKER: {ticker}
COMPANY: {company_name}

--- SEC 10-K RISK FACTORS (PRIMARY SOURCE) ---
{risk_factors_text}

--- FINANCIAL RISK SIGNALS (CALCULATED METRICS) ---
{financial_metrics_json}

--- RECENT NEWS HEADLINES (LOW TRUST — supplementary only) ---
{news_headlines}

DATA QUALITY NOTES:
{quality_notes}

Analyze the risk data above and return your assessment as valid JSON matching
the schema in your system prompt.

IMPORTANT:
- key_risk_factors must be drawn from the 10-K text above, not invented.
- If 10-K risk factors text is empty or unavailable, state "insufficient data"
  in the bear_case and worst_case_scenario fields.
- financial_risk_signals must be cross-referenced with the metric values shown.
"""


class RiskAnalystAgent(BaseAgent):
    """
    Agent 4 — Risk Analysis.

    Extracts and categorizes risk factors from SEC 10-K filings, cross-
    references with financial metrics, and produces a structured risk report.
    """

    async def analyze(self, data_bundle: Any) -> AgentOutput:
        """
        Analyze risk factors from SEC filing and financial data.

        Args:
            data_bundle: dict with keys:
                - "ticker": str
                - "company_name": str (optional)
                - "risk_factors_text": str  — extracted from 10-K Item 1A
                - "financial_metrics": list of CalculationResult dicts
                - "recent_news": list of news dicts (low-trust)
                - "quality_notes": list[str] (optional)

        Returns:
            AgentOutput with risk assessment.
        """
        ticker = "UNKNOWN"
        company_name = ""
        risk_factors_text = ""
        financial_metrics: list = []
        recent_news: list = []
        quality_notes: list[str] = []

        if isinstance(data_bundle, dict):
            ticker = data_bundle.get("ticker", "UNKNOWN")
            company_name = data_bundle.get("company_name", ticker)
            risk_factors_text = data_bundle.get("risk_factors_text", "")
            financial_metrics = data_bundle.get(
                "financial_metrics",
                data_bundle.get("calculation_results", []),
            )
            recent_news = data_bundle.get("recent_news", [])
            quality_notes = data_bundle.get("quality_notes", [])

        # Build evidence
        evidence: list[Evidence] = []

        # Evidence from 10-K filing
        if risk_factors_text:
            evidence.append(
                Evidence(
                    claim="10-K risk factors text available",
                    value=len(risk_factors_text),
                    source="SEC_EDGAR",
                    filing_type="10-K",
                    period=None,
                    metric_name="risk_factors_char_count",
                    formula=None,
                )
            )

        # Evidence from financial metrics
        for item in financial_metrics:
            if isinstance(item, dict):
                metric_name = item.get("metric_name", "")
                value = item.get("value")
                if value is not None:
                    evidence.append(
                        Evidence(
                            claim=f"{metric_name}: {value}",
                            value=value if isinstance(value, (int, float)) else None,
                            source=str(item.get("source", "UNKNOWN")).upper(),
                            filing_type=item.get("filing_type"),
                            period=str(
                                item.get("period", item.get("fiscal_year", ""))
                            ),
                            metric_name=metric_name,
                            formula=item.get("formula"),
                        )
                    )
            else:
                try:
                    if getattr(item, "value", None) is not None:
                        evidence.append(
                            Evidence(
                                claim=f"{item.metric_name}: {item.value}",
                                value=item.value,
                                source=str(getattr(item, "source", "UNKNOWN")).upper(),
                                filing_type=getattr(item, "filing_type", None),
                                period=str(
                                    getattr(item, "period", getattr(item, "fiscal_year", ""))
                                ),
                                metric_name=item.metric_name,
                                formula=getattr(item, "formula", None),
                            )
                        )
                except AttributeError:
                    pass

        missing_data: list[str] = []
        if not risk_factors_text:
            missing_data.append("risk_factors_text")
            quality_notes = list(quality_notes) + [
                "No 10-K risk factors text provided — risk categorization will be limited."
            ]
        if not financial_metrics:
            missing_data.append("financial_metrics")

        total = len(evidence)
        populated = sum(1 for e in evidence if e.value is not None)
        confidence = (populated / total) if total > 0 else 0.0

        # Truncate risk factors text if very long (keep first 8000 chars)
        rf_text = risk_factors_text[:8000] if risk_factors_text else "NOT PROVIDED"
        if len(risk_factors_text) > 8000:
            rf_text += "\n[... truncated ...]"

        financial_metrics_json = json.dumps(
            [m if isinstance(m, dict) else vars(m) for m in financial_metrics],
            indent=2,
            default=str,
        )

        # Summarise news (title + source only, to keep prompts concise)
        news_summary = "\n".join(
            f"- {item.get('title', item.get('headline', str(item)))}"
            f" [{item.get('source', item.get('publisher', 'unknown'))}]"
            for item in recent_news[:15]
        ) or "No recent news available."

        quality_str = "\n".join(quality_notes) if quality_notes else "None reported."

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            risk_factors_text=rf_text,
            financial_metrics_json=financial_metrics_json,
            news_headlines=news_summary,
            quality_notes=quality_str,
        )

        response_text, tokens_used = await self._run_analysis(_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_structured_output(response_text)

        return AgentOutput(
            agent_name="RiskAnalystAgent",
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
