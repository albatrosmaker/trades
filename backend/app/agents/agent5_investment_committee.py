"""
agent5_investment_committee.py — Investment Committee Chair agent.

Synthesizes outputs from all four specialist agents (Financial, Governance,
Valuation, Risk) into a final investment recommendation. Every conclusion
must be traceable to specific evidence from the prior agents. The committee
must also articulate what specific events or metrics would change the view.

Input: AgentOutput instances from agents 1–4 plus current price and ticker.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from .base import SYSTEM_PROMPT_BASE, AgentOutput, BaseAgent, Evidence, MODEL

logger = logging.getLogger(__name__)

_ROLE = "Chief Investment Officer and Investment Committee Chair"

_SYSTEM_PROMPT = SYSTEM_PROMPT_BASE.format(role=_ROLE) + """
You are reviewing the outputs of four specialist analysts (Financial,
Governance, Valuation, Risk) and synthesizing them into a final investment
recommendation.

CRITICAL RULE: Your recommendation must cite specific findings from the
analyst reports. Do NOT introduce new data or assumptions beyond what is
provided in those reports. Explain clearly what would change your view.

OUTPUT SCHEMA:
{
  "investment_thesis": "<3-5 sentence core thesis citing specific analyst findings>",
  "bull_case": {
    "scenario": "<description grounded in financial and valuation data>",
    "key_drivers": ["<driver 1 from financial analysis>", "<driver 2>", "<driver 3>"],
    "price_target_upside_pct": <number or null>
  },
  "bear_case": {
    "scenario": "<description grounded in risk analysis>",
    "key_risks": ["<risk 1 from risk agent>", "<risk 2>", "<risk 3>"],
    "downside_scenario_pct": <number or null>
  },
  "recommendation": "<Strong Buy|Buy|Hold|Sell|Strong Sell>",
  "conviction": "<High|Moderate|Low>",
  "confidence_score": <0-100>,
  "what_would_change_view": [
    "<specific catalyst, price level, or financial milestone>"
  ],
  "key_metrics_to_watch": ["<metric 1>", "<metric 2>"],
  "time_horizon": "<Short-term (<1yr)|Medium-term (1-3yr)|Long-term (3yr+)>",
  "suitable_investor": "<description of investor profile this is appropriate for>",
  "executive_summary": "<professional paragraph summarizing the full analysis>"
}

Grounding rules:
- bull_case.key_drivers must reference findings from the financial or valuation report.
- bear_case.key_risks must reference findings from the risk report.
- price_target_upside_pct: derive from valuation agent's comps_implied_value midpoint
  vs current_price if available; otherwise set to null.
- downside_scenario_pct: derive from the risk agent's worst_case_scenario if it
  contains a percentage estimate; otherwise set to null.
- confidence_score: weight the four agent confidence scores and data quality.
- If any agent reported missing data, lower conviction accordingly.
"""

_USER_PROMPT_TEMPLATE = """
TICKER: {ticker}
COMPANY: {company_name}
CURRENT PRICE: {current_price}

=== FINANCIAL ANALYSIS (Agent 1) ===
Confidence: {financial_confidence}
Data Warnings: {financial_warnings}
Analysis:
{financial_analysis}

=== GOVERNANCE ANALYSIS (Agent 2) ===
Confidence: {governance_confidence}
Data Warnings: {governance_warnings}
Analysis:
{governance_analysis}

=== VALUATION ANALYSIS (Agent 3) ===
Confidence: {valuation_confidence}
Data Warnings: {valuation_warnings}
Analysis:
{valuation_analysis}

=== RISK ANALYSIS (Agent 4) ===
Confidence: {risk_confidence}
Data Warnings: {risk_warnings}
Analysis:
{risk_analysis}

Review the four analyst reports above. Every claim in your recommendation
must trace back to a specific finding in one of these reports. Return your
investment committee decision as valid JSON matching the schema in your
system prompt.
"""


class InvestmentCommitteeAgent(BaseAgent):
    """
    Agent 5 — Investment Committee Synthesis.

    Synthesizes outputs from all four specialist agents into a final
    investment recommendation with evidence-backed bull/bear cases.
    """

    async def analyze(self, data_bundle: Any) -> AgentOutput:
        """
        Synthesize all agent outputs into a final recommendation.

        Args:
            data_bundle: dict with keys:
                - "ticker": str
                - "company_name": str (optional)
                - "current_price": float | None
                - "financial_output": AgentOutput from FinancialAnalystAgent
                - "governance_output": AgentOutput from GovernanceAnalystAgent
                - "valuation_output": AgentOutput from ValuationAnalystAgent
                - "risk_output": AgentOutput from RiskAnalystAgent

        Returns:
            AgentOutput with the investment committee recommendation.
        """
        ticker = "UNKNOWN"
        company_name = ""
        current_price: float | None = None
        financial_output: AgentOutput | None = None
        governance_output: AgentOutput | None = None
        valuation_output: AgentOutput | None = None
        risk_output: AgentOutput | None = None

        if isinstance(data_bundle, dict):
            ticker = data_bundle.get("ticker", "UNKNOWN")
            company_name = data_bundle.get("company_name", ticker)
            current_price = data_bundle.get("current_price")
            financial_output = data_bundle.get("financial_output")
            governance_output = data_bundle.get("governance_output")
            valuation_output = data_bundle.get("valuation_output")
            risk_output = data_bundle.get("risk_output")

        def _get_confidence(output: AgentOutput | None) -> float:
            return output.confidence if output else 0.0

        def _get_analysis_json(output: AgentOutput | None) -> str:
            if output is None:
                return json.dumps({"status": "not_available"})
            return json.dumps(output.analysis, indent=2, default=str)

        def _get_warnings(output: AgentOutput | None) -> str:
            if output is None:
                return "Agent output not available."
            warnings = output.data_quality_warnings + output.missing_data
            return "; ".join(warnings) if warnings else "None."

        # Aggregate evidence from all agents
        evidence: list[Evidence] = []
        for agent_output in [financial_output, governance_output, valuation_output, risk_output]:
            if agent_output:
                evidence.extend(agent_output.evidence)

        # Add current price as evidence
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
        for name, output in [
            ("financial_output", financial_output),
            ("governance_output", governance_output),
            ("valuation_output", valuation_output),
            ("risk_output", risk_output),
        ]:
            if output is None:
                missing_data.append(name)

        # Weighted average confidence across all four agents
        confidences = [
            _get_confidence(financial_output),
            _get_confidence(governance_output),
            _get_confidence(valuation_output),
            _get_confidence(risk_output),
        ]
        available = [c for c in confidences if c > 0]
        avg_confidence = sum(available) / len(available) if available else 0.0
        # Penalise for missing agents
        penalty = len(missing_data) * 0.1
        confidence = max(0.0, avg_confidence - penalty)

        all_warnings: list[str] = []
        for agent_output in [financial_output, governance_output, valuation_output, risk_output]:
            if agent_output:
                all_warnings.extend(agent_output.data_quality_warnings)

        price_str = str(current_price) if current_price is not None else "unavailable"

        user_prompt = _USER_PROMPT_TEMPLATE.format(
            ticker=ticker,
            company_name=company_name,
            current_price=price_str,
            financial_confidence=_get_confidence(financial_output),
            financial_warnings=_get_warnings(financial_output),
            financial_analysis=_get_analysis_json(financial_output),
            governance_confidence=_get_confidence(governance_output),
            governance_warnings=_get_warnings(governance_output),
            governance_analysis=_get_analysis_json(governance_output),
            valuation_confidence=_get_confidence(valuation_output),
            valuation_warnings=_get_warnings(valuation_output),
            valuation_analysis=_get_analysis_json(valuation_output),
            risk_confidence=_get_confidence(risk_output),
            risk_warnings=_get_warnings(risk_output),
            risk_analysis=_get_analysis_json(risk_output),
        )

        response_text, tokens_used = await self._run_analysis(_SYSTEM_PROMPT, user_prompt)
        parsed = self._parse_structured_output(response_text)

        return AgentOutput(
            agent_name="InvestmentCommitteeAgent",
            ticker=ticker,
            analysis=parsed,
            evidence=evidence,
            confidence=round(confidence, 3),
            data_quality_warnings=all_warnings,
            missing_data=missing_data,
            generated_at=datetime.now(timezone.utc).isoformat(),
            model_used=MODEL,
            tokens_used=tokens_used,
        )
