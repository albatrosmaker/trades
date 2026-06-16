"""
agent2_governance.py — Corporate Governance Analyst agent.

Analyzes corporate governance data extracted from SEC DEF 14A proxy
statements and produces a structured ESG/governance assessment.

Input: GovernanceData dict from SEC DEF 14A parsing (proxy_data field
       of CompanyDataBundle).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from .base import SYSTEM_PROMPT_BASE, AgentOutput, BaseAgent, Evidence, MODEL

logger = logging.getLogger(__name__)

_ROLE = "Corporate Governance Analyst specializing in ESG and shareholder rights"

_SYSTEM_PROMPT = SYSTEM_PROMPT_BASE.format(role=_ROLE) + """
You will receive corporate governance data extracted from SEC proxy statements
(DEF 14A filings) and other sources. Analyze only the data provided and return
a structured JSON response matching the schema below EXACTLY.

OUTPUT SCHEMA:
{
  "board_assessment": {
    "independence_ratio": <number or null>,
    "size_assessment": "<optimal|too_small|too_large>",
    "ceo_chairman_separation": <true|false|null>,
    "commentary": "<string citing specific data points>"
  },
  "compensation_assessment": {
    "pay_for_performance": "<strong|moderate|weak|unclear>",
    "excessive_pay_flags": ["<concern 1>", "<concern 2>"],
    "commentary": "<string>"
  },
  "shareholder_rights": {
    "dual_class_structure": <true|false|null>,
    "poison_pill": <true|false|null>,
    "staggered_board": <true|false|null>,
    "shareholder_friendly_score": <0-100>
  },
  "insider_ownership": {
    "percentage": <number or null>,
    "alignment_assessment": "<high|moderate|low|concerning>",
    "commentary": "<string>"
  },
  "governance_score": <0-100>,
  "governance_grade": "<A|B|C|D|F>",
  "red_flags": ["<specific governance concern from data>"],
  "governance_risk_assessment": "<Low|Moderate|High|Critical>",
  "analyst_summary": "<string>"
}

When a field is not present in the input data, set it to null and note
"insufficient data" in the relevant commentary field. Do NOT invent figures.
"""

_USER_PROMPT_TEMPLATE = """
TICKER: {ticker}
COMPANY: {company_name}

PROXY STATEMENT / GOVERNANCE DATA:
{governance_json}

INSIDER TRANSACTIONS DATA:
{insider_json}

DATA QUALITY NOTES:
{quality_notes}

Analyze the corporate governance data above and return your assessment as
valid JSON matching the schema in your system prompt. Every claim must be
traceable to a specific field in the data provided. Use "insufficient data"
where information is absent.
"""


class GovernanceAnalystAgent(BaseAgent):
    """
    Agent 2 — Corporate Governance Analysis.

    Analyzes proxy statement data and insider transaction history to
    assess board quality, compensation alignment, and shareholder rights.
    """

    async def analyze(self, data_bundle: Any) -> AgentOutput:
        """
        Analyze governance data from proxy statements.

        Args:
            data_bundle: dict with keys:
                - "ticker": str
                - "company_name": str (optional)
                - "proxy_data": dict from edgar.get_proxy_statement()
                - "insider_transactions": list of transaction dicts
                - "quality_notes": list[str] (optional)

        Returns:
            AgentOutput with governance assessment.
        """
        ticker = "UNKNOWN"
        company_name = ""
        proxy_data: dict = {}
        insider_transactions: list = []
        quality_notes: list[str] = []

        if isinstance(data_bundle, dict):
            ticker = data_bundle.get("ticker", "UNKNOWN")
            company_name = data_bundle.get("company_name", ticker)
            proxy_data = data_bundle.get("proxy_data", {})
            insider_transactions = data_bundle.get("insider_transactions", [])
            quality_notes = data_bundle.get("quality_notes", [])

        # Build evidence from proxy_data fields
        evidence: list[Evidence] = []

        def _add_evidence(claim: str, value: Any, metric_name: str, period: str | None = None) -> None:
            evidence.append(
                Evidence(
                    claim=claim,
                    value=value if isinstance(value, (int, float)) else str(value) if value is not None else None,
                    source="SEC_EDGAR",
                    filing_type="DEF 14A",
                    period=period,
                    metric_name=metric_name,
                    formula=None,
                )
            )

        # Extract key governance fields as evidence
        if proxy_data:
            for key, val in proxy_data.items():
                if isinstance(val, (int, float, str, bool)) and val is not None:
                    _add_evidence(
                        claim=f"{key}: {val}",
                        value=val if isinstance(val, (int, float)) else str(val),
                        metric_name=key,
                        period=str(proxy_data.get("fiscal_year", proxy_data.get("year", ""))),
                    )

        # Summarise insider transactions as evidence
        if insider_transactions:
            insider_count = len(insider_transactions)
            _add_evidence(
                claim=f"insider_transaction_count: {insider_count}",
                value=insider_count,
                metric_name="insider_transaction_count",
            )

        missing_data: list[str] = []
        if not proxy_data:
            missing_data.append("proxy_data")
            quality_notes = list(quality_notes) + [
                "No proxy statement data available — governance assessment limited."
            ]
        if not insider_transactions:
            missing_data.append("insider_transactions")

        total = len(evidence)
        populated = sum(1 for e in evidence if e.value is not None)
        confidence = (populated / total) if total > 0 else 0.0

        governance_json = json.dumps(proxy_data, indent=2, default=str)
        insider_json = json.dumps(insider_transactions[:20], indent=2, default=str)
        quality_str = "\n".join(quality_notes) if quality_notes else "None reported."

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            governance_json=governance_json,
            insider_json=insider_json,
            quality_notes=quality_str,
        )

        response_text, tokens_used = await self._run_analysis(_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_structured_output(response_text)

        return AgentOutput(
            agent_name="GovernanceAnalystAgent",
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
