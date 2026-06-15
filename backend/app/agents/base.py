"""
base.py — Shared infrastructure for all AI research agents.

Every agent:
  1. Receives a pre-computed data packet (never raw market data)
  2. Calls the Anthropic API via _run_analysis()
  3. Returns a fully-structured AgentOutput with evidence citations
  4. States "insufficient data" rather than guessing when evidence is missing
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Shared data structures
# ---------------------------------------------------------------------------


@dataclass
class Evidence:
    """A single piece of evidence supporting an analytical claim."""

    claim: str
    value: str | float | None
    source: str  # "SEC_EDGAR" / "FMP" / "YAHOO"
    filing_type: str | None  # "10-K", "10-Q", etc.
    period: str | None
    metric_name: str | None
    formula: str | None  # calculation formula used


@dataclass
class AgentOutput:
    """Standardised output for every research agent."""

    agent_name: str
    ticker: str
    analysis: dict  # structured output specific to each agent
    evidence: list[Evidence]
    confidence: float  # 0–1
    data_quality_warnings: list[str]
    missing_data: list[str]
    generated_at: str  # ISO timestamp
    model_used: str
    tokens_used: int


# ---------------------------------------------------------------------------
# Base agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_BASE = """You are a {role} at a tier-1 investment bank.

CRITICAL RULES:
1. Every numerical claim must reference a specific metric from the provided data packet.
2. Never estimate, interpolate, or assume any financial figure.
3. If data is missing, state "insufficient data" for that point.
4. All conclusions must be supported by evidence from the data packet.
5. You are analyzing REAL company data — accuracy is paramount.
6. Output must be valid JSON matching the specified schema exactly.
"""


class BaseAgent(ABC):
    """
    Abstract base class for all AI research agents.

    Subclasses must implement `analyze(data_bundle)`.
    """

    def __init__(self) -> None:
        self._client = AsyncAnthropic()

    # ------------------------------------------------------------------
    # Core API call
    # ------------------------------------------------------------------

    async def _run_analysis(self, system_prompt: str, user_prompt: str) -> tuple[str, int]:
        """
        Call the Anthropic API and return (response_text, tokens_used).

        Raises:
            RuntimeError: if the API call fails after retries.
        """
        try:
            message = await self._client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            response_text = message.content[0].text
            tokens_used = message.usage.input_tokens + message.usage.output_tokens
            return response_text, tokens_used
        except Exception as exc:
            logger.error("Anthropic API call failed in %s: %s", self.__class__.__name__, exc)
            raise RuntimeError(f"Anthropic API call failed: {exc}") from exc

    # ------------------------------------------------------------------
    # JSON parsing
    # ------------------------------------------------------------------

    def _parse_structured_output(self, response: str) -> dict:
        """
        Extract and parse a JSON object from the LLM response.

        Handles both bare JSON and JSON wrapped in markdown code blocks.
        Returns an empty dict on parse failure (caller should treat as error).
        """
        # Strip markdown code fences if present
        cleaned = response.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to find a JSON object anywhere in the response
            obj_match = re.search(r"\{[\s\S]*\}", cleaned)
            if obj_match:
                try:
                    return json.loads(obj_match.group(0))
                except json.JSONDecodeError:
                    pass

        logger.warning(
            "%s: Failed to parse JSON from LLM response. Raw: %.200s",
            self.__class__.__name__,
            response,
        )
        return {}

    # ------------------------------------------------------------------
    # Evidence extraction
    # ------------------------------------------------------------------

    def _build_evidence_from_data(self, data_bundle: Any) -> list[Evidence]:
        """
        Extract Evidence objects from a calculation results bundle.

        Accepts either:
          - a list of CalculationResult dicts/objects
          - a dict containing such a list under various keys
        Returns an empty list when nothing useful can be extracted.
        """
        evidence: list[Evidence] = []

        # Normalise to a flat list of result-like objects
        items: list[Any] = []
        if isinstance(data_bundle, list):
            items = data_bundle
        elif isinstance(data_bundle, dict):
            for key in ("calculation_results", "results", "metrics", "ratios"):
                if isinstance(data_bundle.get(key), list):
                    items = data_bundle[key]
                    break
            if not items:
                # Fallback: treat dict values themselves as evidence
                for key, val in data_bundle.items():
                    if isinstance(val, (int, float, str)) and val is not None:
                        evidence.append(
                            Evidence(
                                claim=key,
                                value=val if isinstance(val, (int, float)) else str(val),
                                source=str(data_bundle.get("source", "UNKNOWN")).upper(),
                                filing_type=data_bundle.get("filing_type"),
                                period=str(data_bundle.get("period", "")),
                                metric_name=key,
                                formula=None,
                            )
                        )
                return evidence

        for item in items:
            if isinstance(item, dict):
                metric_name = item.get("metric_name", "")
                value = item.get("value")
                source = str(item.get("source", "UNKNOWN")).upper()
                evidence.append(
                    Evidence(
                        claim=f"{metric_name}: {value}",
                        value=value,
                        source=source,
                        filing_type=item.get("filing_type"),
                        period=str(item.get("period", item.get("fiscal_year", ""))),
                        metric_name=metric_name,
                        formula=item.get("formula"),
                    )
                )
            else:
                # Assume CalculationResult-like dataclass/object
                try:
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

        return evidence

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    async def analyze(self, data_bundle: Any) -> AgentOutput:
        """
        Run analysis on the provided data bundle.

        Args:
            data_bundle: Pre-computed data specific to this agent.

        Returns:
            AgentOutput with structured analysis and evidence citations.
        """
