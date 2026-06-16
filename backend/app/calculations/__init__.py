"""
calculations — Financial calculation engine for the AI Equity Research Platform.

Public API surface:

    from app.calculations import (
        FinancialRatioCalculator,
        CalculationResult,
        ValuationCalculator,
        DCFAssumptions,
        DCFResult,
        CompanyMetrics,
        CompsResult,
        ScoringEngine,
        ScoreResult,
        normalize_edgar_data,
        normalize_fmp_data,
        get_display_label,
        EDGAR_TO_INTERNAL,
        FMP_TO_INTERNAL,
    )

The calculation engine is the ONLY place where financial numbers are produced.
The LLM layer must call these functions and cite their outputs; it must never
invent or hallucinate financial figures.
"""

from .financial_ratios import CalculationResult, FinancialRatioCalculator
from .field_mappings import (
    EDGAR_TO_INTERNAL,
    FMP_TO_INTERNAL,
    INTERNAL_TO_DISPLAY,
    INTERNAL_TO_EDGAR,
    INTERNAL_TO_FMP,
    get_display_label,
    normalize_edgar_data,
    normalize_fmp_data,
)
from .scoring import ScoreResult, ScoringEngine
from .valuation import (
    CompanyMetrics,
    CompsResult,
    DCFAssumptions,
    DCFResult,
    DCFYearProjection,
    ImpliedValueResult,
    MarginOfSafetyResult,
    ValuationCalculator,
)

__all__ = [
    # financial_ratios
    "CalculationResult",
    "FinancialRatioCalculator",
    # field_mappings
    "EDGAR_TO_INTERNAL",
    "FMP_TO_INTERNAL",
    "INTERNAL_TO_DISPLAY",
    "INTERNAL_TO_EDGAR",
    "INTERNAL_TO_FMP",
    "get_display_label",
    "normalize_edgar_data",
    "normalize_fmp_data",
    # valuation
    "CompanyMetrics",
    "CompsResult",
    "DCFAssumptions",
    "DCFResult",
    "DCFYearProjection",
    "ImpliedValueResult",
    "MarginOfSafetyResult",
    "ValuationCalculator",
    # scoring
    "ScoreResult",
    "ScoringEngine",
]
