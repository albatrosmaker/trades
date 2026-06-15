"""
agents — AI research agent package for the AI Equity Research Platform.

Five specialist agents collaborate to produce institutional-quality research:

  Agent 1 — FinancialAnalystAgent   : financial statement analysis
  Agent 2 — GovernanceAnalystAgent  : corporate governance (proxy statements)
  Agent 3 — ValuationAnalystAgent   : trading multiples and DCF (if assumptions provided)
  Agent 4 — RiskAnalystAgent        : SEC 10-K risk factor extraction and categorization
  Agent 5 — InvestmentCommitteeAgent: final synthesis and investment recommendation

ResearchOrchestrator orchestrates the full pipeline, running agents 1–4 in
parallel and feeding their outputs to agent 5.

Core principle: agents ANALYZE data — they NEVER invent data. Every claim
must be supported by evidence from the provided data packet.
"""

from .agent1_financial import FinancialAnalystAgent
from .agent2_governance import GovernanceAnalystAgent
from .agent3_valuation import ValuationAnalystAgent
from .agent4_risk import RiskAnalystAgent
from .agent5_investment_committee import InvestmentCommitteeAgent
from .base import AgentOutput, BaseAgent, Evidence
from .orchestrator import FullResearchResult, ResearchOrchestrator

__all__ = [
    # Base types
    "BaseAgent",
    "AgentOutput",
    "Evidence",
    # Specialist agents
    "FinancialAnalystAgent",
    "GovernanceAnalystAgent",
    "ValuationAnalystAgent",
    "RiskAnalystAgent",
    "InvestmentCommitteeAgent",
    # Orchestrator
    "ResearchOrchestrator",
    "FullResearchResult",
]
