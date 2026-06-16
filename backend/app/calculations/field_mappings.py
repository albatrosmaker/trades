"""
field_mappings.py — Translation layer between external data provider field names
and the internal standardized field names used by the calculation engine.

Supports:
  - SEC EDGAR XBRL tags (us-gaap namespace)
  - Financial Modeling Prep (FMP) JSON field names

The internal field names are the canonical names used throughout
the calculation engine. All data must be normalized through these
mappings before any calculation is performed.
"""

# ---------------------------------------------------------------------------
# EDGAR XBRL → Internal
# Multiple XBRL tags can map to the same internal field because companies
# use different (but semantically equivalent) concepts.
# ---------------------------------------------------------------------------

EDGAR_TO_INTERNAL: dict[str, str] = {
    # ── Revenue ──────────────────────────────────────────────────────────────
    "us-gaap/Revenues": "revenue",
    "us-gaap/RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "us-gaap/RevenueFromContractWithCustomerIncludingAssessedTax": "revenue",
    "us-gaap/SalesRevenueNet": "revenue",
    "us-gaap/SalesRevenueGoodsNet": "revenue",
    "us-gaap/SalesRevenueServicesNet": "revenue",
    "us-gaap/NetRevenues": "revenue",
    "us-gaap/RevenueNet": "revenue",
    "us-gaap/TotalRevenues": "revenue",

    # ── Cost of Goods Sold / Cost of Revenue ─────────────────────────────────
    "us-gaap/CostOfGoodsSold": "cost_of_revenue",
    "us-gaap/CostOfRevenue": "cost_of_revenue",
    "us-gaap/CostOfGoodsAndServicesSold": "cost_of_revenue",
    "us-gaap/CostOfServices": "cost_of_revenue",
    "us-gaap/CostOfGoodsSoldExcludingDepreciationDepletionAndAmortization": "cost_of_revenue",

    # ── Gross Profit ─────────────────────────────────────────────────────────
    "us-gaap/GrossProfit": "gross_profit",

    # ── Operating Income ─────────────────────────────────────────────────────
    "us-gaap/OperatingIncomeLoss": "operating_income",
    "us-gaap/IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "income_before_tax",
    "us-gaap/OperatingExpenses": "operating_expenses",

    # ── EBIT / EBITDA components ──────────────────────────────────────────────
    "us-gaap/DepreciationDepletionAndAmortization": "depreciation_and_amortization",
    "us-gaap/Depreciation": "depreciation",
    "us-gaap/AmortizationOfIntangibleAssets": "amortization",
    "us-gaap/DepreciationAndAmortization": "depreciation_and_amortization",
    "us-gaap/DepreciationAmortizationAndAccretionNet": "depreciation_and_amortization",

    # ── Net Income ────────────────────────────────────────────────────────────
    "us-gaap/NetIncomeLoss": "net_income",
    "us-gaap/NetIncomeLossAvailableToCommonStockholdersBasic": "net_income",
    "us-gaap/ProfitLoss": "net_income",
    "us-gaap/NetIncome": "net_income",
    "us-gaap/ComprehensiveIncomeNetOfTax": "comprehensive_income",

    # ── Interest ─────────────────────────────────────────────────────────────
    "us-gaap/InterestExpense": "interest_expense",
    "us-gaap/InterestAndDebtExpense": "interest_expense",
    "us-gaap/InterestExpenseDebt": "interest_expense",
    "us-gaap/InterestAndOtherExpenses": "interest_expense",
    "us-gaap/InterestIncome": "interest_income",
    "us-gaap/NonoperatingIncomeExpense": "non_operating_income",

    # ── Taxes ─────────────────────────────────────────────────────────────────
    "us-gaap/IncomeTaxExpenseBenefit": "income_tax_expense",
    "us-gaap/EffectiveIncomeTaxRateContinuingOperations": "effective_tax_rate",

    # ── EPS ───────────────────────────────────────────────────────────────────
    "us-gaap/EarningsPerShareBasic": "eps_basic",
    "us-gaap/EarningsPerShareDiluted": "eps_diluted",
    "us-gaap/WeightedAverageNumberOfSharesOutstandingBasic": "shares_basic",
    "us-gaap/WeightedAverageNumberOfDilutedSharesOutstanding": "shares_diluted",

    # ── R&D / SG&A ────────────────────────────────────────────────────────────
    "us-gaap/ResearchAndDevelopmentExpense": "research_and_development",
    "us-gaap/SellingGeneralAndAdministrativeExpense": "selling_general_administrative",
    "us-gaap/GeneralAndAdministrativeExpense": "general_and_administrative",
    "us-gaap/SellingAndMarketingExpense": "selling_and_marketing",

    # ── Balance Sheet: Assets ─────────────────────────────────────────────────
    "us-gaap/Assets": "total_assets",
    "us-gaap/AssetsCurrent": "current_assets",
    "us-gaap/AssetsNoncurrent": "non_current_assets",
    "us-gaap/CashAndCashEquivalentsAtCarryingValue": "cash_and_equivalents",
    "us-gaap/CashAndCashEquivalentsPeriodIncreaseDecrease": "change_in_cash",
    "us-gaap/CashCashEquivalentsAndShortTermInvestments": "cash_and_short_term_investments",
    "us-gaap/ShortTermInvestments": "short_term_investments",
    "us-gaap/MarketableSecuritiesCurrent": "short_term_investments",
    "us-gaap/AccountsReceivableNetCurrent": "accounts_receivable",
    "us-gaap/ReceivablesNetCurrent": "accounts_receivable",
    "us-gaap/InventoryNet": "inventory",
    "us-gaap/PrepaidExpenseAndOtherAssetsCurrent": "prepaid_and_other_current_assets",
    "us-gaap/OtherAssetsCurrent": "other_current_assets",
    "us-gaap/PropertyPlantAndEquipmentNet": "property_plant_equipment_net",
    "us-gaap/PropertyPlantAndEquipmentGross": "property_plant_equipment_gross",
    "us-gaap/Goodwill": "goodwill",
    "us-gaap/IntangibleAssetsNetExcludingGoodwill": "intangible_assets",
    "us-gaap/LongTermInvestments": "long_term_investments",
    "us-gaap/OtherAssetsNoncurrent": "other_non_current_assets",

    # ── Balance Sheet: Liabilities ────────────────────────────────────────────
    "us-gaap/Liabilities": "total_liabilities",
    "us-gaap/LiabilitiesCurrent": "current_liabilities",
    "us-gaap/LiabilitiesNoncurrent": "non_current_liabilities",
    "us-gaap/AccountsPayableCurrent": "accounts_payable",
    "us-gaap/AccruedLiabilitiesCurrent": "accrued_liabilities",
    "us-gaap/DeferredRevenueCurrent": "deferred_revenue_current",
    "us-gaap/ShortTermBorrowings": "short_term_debt",
    "us-gaap/LongTermDebt": "long_term_debt",
    "us-gaap/LongTermDebtCurrent": "current_portion_long_term_debt",
    "us-gaap/LongTermDebtNoncurrent": "long_term_debt",
    "us-gaap/LongTermDebtAndCapitalLeaseObligations": "long_term_debt",
    "us-gaap/DebtCurrent": "short_term_debt",
    "us-gaap/OtherLiabilitiesCurrent": "other_current_liabilities",
    "us-gaap/OtherLiabilitiesNoncurrent": "other_non_current_liabilities",
    "us-gaap/DeferredTaxLiabilitiesNoncurrent": "deferred_tax_liabilities",
    "us-gaap/OperatingLeaseLiability": "operating_lease_liability",
    "us-gaap/OperatingLeaseLiabilityCurrent": "operating_lease_current",
    "us-gaap/OperatingLeaseLiabilityNoncurrent": "operating_lease_non_current",
    "us-gaap/FinanceLeaseLiability": "finance_lease_liability",

    # ── Balance Sheet: Equity ─────────────────────────────────────────────────
    "us-gaap/StockholdersEquity": "shareholders_equity",
    "us-gaap/StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "total_equity",
    "us-gaap/RetainedEarningsAccumulatedDeficit": "retained_earnings",
    "us-gaap/CommonStockValue": "common_stock",
    "us-gaap/AdditionalPaidInCapital": "additional_paid_in_capital",
    "us-gaap/TreasuryStockValue": "treasury_stock",
    "us-gaap/AccumulatedOtherComprehensiveIncomeLossNetOfTax": "accumulated_other_comprehensive_income",
    "us-gaap/MinorityInterest": "non_controlling_interest",
    "us-gaap/CommonStockSharesOutstanding": "shares_outstanding",

    # ── Cash Flow Statement ───────────────────────────────────────────────────
    "us-gaap/NetCashProvidedByUsedInOperatingActivities": "operating_cash_flow",
    "us-gaap/NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": "operating_cash_flow",
    "us-gaap/NetCashProvidedByUsedInInvestingActivities": "investing_cash_flow",
    "us-gaap/NetCashProvidedByUsedInFinancingActivities": "financing_cash_flow",
    "us-gaap/PaymentsToAcquirePropertyPlantAndEquipment": "capital_expenditures",
    "us-gaap/PaymentsForProceedsFromBusinessesAndInterestInAffiliates": "acquisitions",
    "us-gaap/PaymentsToAcquireBusinessesNetOfCashAcquired": "acquisitions",
    "us-gaap/PaymentsOfDividendsCommonStock": "dividends_paid",
    "us-gaap/PaymentsOfDividends": "dividends_paid",
    "us-gaap/ProceedsFromIssuanceOfCommonStock": "proceeds_from_stock_issuance",
    "us-gaap/RepaymentsOfLongTermDebt": "debt_repayment",
    "us-gaap/ProceedsFromIssuanceOfLongTermDebt": "debt_issuance",
    "us-gaap/PaymentsForRepurchaseOfCommonStock": "share_repurchases",
    "us-gaap/DepreciationDepletionAndAmortizationProductionAndManufacturing": "depreciation_and_amortization",
    "us-gaap/ShareBasedCompensation": "stock_based_compensation",
    "us-gaap/AmortizationOfDeferredSalesCommissions": "amortization",
    "us-gaap/IncreaseDecreaseInAccountsReceivable": "change_in_accounts_receivable",
    "us-gaap/IncreaseDecreaseInInventories": "change_in_inventory",
    "us-gaap/IncreaseDecreaseInAccountsPayable": "change_in_accounts_payable",
}

# ---------------------------------------------------------------------------
# FMP (Financial Modeling Prep) → Internal
# FMP uses camelCase JSON keys for most endpoints.
# ---------------------------------------------------------------------------

FMP_TO_INTERNAL: dict[str, str] = {
    # ── Income Statement ──────────────────────────────────────────────────────
    "revenue": "revenue",
    "costOfRevenue": "cost_of_revenue",
    "costAndExpenses": "total_costs_and_expenses",
    "grossProfit": "gross_profit",
    "grossProfitRatio": "gross_margin",
    "researchAndDevelopmentExpenses": "research_and_development",
    "generalAndAdministrativeExpenses": "general_and_administrative",
    "sellingAndMarketingExpenses": "selling_and_marketing",
    "sellingGeneralAndAdministrativeExpenses": "selling_general_administrative",
    "otherExpenses": "other_operating_expenses",
    "operatingExpenses": "operating_expenses",
    "operatingIncome": "operating_income",
    "operatingIncomeRatio": "operating_margin",
    "totalOtherIncomeExpensesNet": "non_operating_income",
    "incomeBeforeTax": "income_before_tax",
    "incomeBeforeTaxRatio": "pre_tax_margin",
    "incomeTaxExpense": "income_tax_expense",
    "netIncome": "net_income",
    "netIncomeRatio": "net_profit_margin",
    "eps": "eps_basic",
    "epsdiluted": "eps_diluted",
    "weightedAverageShsOut": "shares_basic",
    "weightedAverageShsOutDil": "shares_diluted",
    "ebitda": "ebitda",
    "ebitdaratio": "ebitda_margin",
    "depreciationAndAmortization": "depreciation_and_amortization",
    "interestExpense": "interest_expense",
    "interestIncome": "interest_income",

    # ── Balance Sheet ─────────────────────────────────────────────────────────
    "cashAndCashEquivalents": "cash_and_equivalents",
    "shortTermInvestments": "short_term_investments",
    "cashAndShortTermInvestments": "cash_and_short_term_investments",
    "netReceivables": "accounts_receivable",
    "inventory": "inventory",
    "otherCurrentAssets": "other_current_assets",
    "totalCurrentAssets": "current_assets",
    "propertyPlantEquipmentNet": "property_plant_equipment_net",
    "goodwill": "goodwill",
    "intangibleAssets": "intangible_assets",
    "goodwillAndIntangibleAssets": "goodwill_and_intangibles",
    "longTermInvestments": "long_term_investments",
    "taxAssets": "deferred_tax_assets",
    "otherNonCurrentAssets": "other_non_current_assets",
    "totalNonCurrentAssets": "non_current_assets",
    "otherAssets": "other_assets",
    "totalAssets": "total_assets",
    "accountPayables": "accounts_payable",
    "shortTermDebt": "short_term_debt",
    "taxPayables": "taxes_payable",
    "deferredRevenue": "deferred_revenue_current",
    "otherCurrentLiabilities": "other_current_liabilities",
    "totalCurrentLiabilities": "current_liabilities",
    "longTermDebt": "long_term_debt",
    "deferredRevenueNonCurrent": "deferred_revenue_non_current",
    "deferredTaxLiabilitiesNonCurrent": "deferred_tax_liabilities",
    "otherNonCurrentLiabilities": "other_non_current_liabilities",
    "totalNonCurrentLiabilities": "non_current_liabilities",
    "otherLiabilities": "other_liabilities",
    "capitalLeaseObligations": "capital_lease_obligations",
    "totalLiabilities": "total_liabilities",
    "preferredStock": "preferred_stock",
    "commonStock": "common_stock",
    "retainedEarnings": "retained_earnings",
    "accumulatedOtherComprehensiveIncomeLoss": "accumulated_other_comprehensive_income",
    "othertotalStockholdersEquity": "other_equity",
    "totalStockholdersEquity": "shareholders_equity",
    "totalEquity": "total_equity",
    "minorityInterest": "non_controlling_interest",
    "totalLiabilitiesAndStockholdersEquity": "total_liabilities_and_equity",
    "totalInvestments": "total_investments",
    "totalDebt": "total_debt",
    "netDebt": "net_debt",

    # ── Cash Flow Statement ───────────────────────────────────────────────────
    "netIncome": "net_income",  # repeated in cash flow context
    "depreciationAndAmortization": "depreciation_and_amortization",
    "deferredIncomeTax": "deferred_income_tax",
    "stockBasedCompensation": "stock_based_compensation",
    "changeInWorkingCapital": "change_in_working_capital",
    "accountsReceivables": "change_in_accounts_receivable",
    "inventoryChange": "change_in_inventory",
    "accountsPayables": "change_in_accounts_payable",
    "otherWorkingCapital": "other_working_capital",
    "otherNonCashItems": "other_non_cash_items",
    "netCashProvidedByOperatingActivities": "operating_cash_flow",
    "investmentsInPropertyPlantAndEquipment": "capital_expenditures",
    "acquisitionsNet": "acquisitions",
    "purchasesOfInvestments": "purchases_of_investments",
    "salesMaturitiesOfInvestments": "sales_of_investments",
    "otherInvestingActivites": "other_investing_activities",
    "netCashUsedForInvestingActivites": "investing_cash_flow",
    "debtRepayment": "debt_repayment",
    "commonStockIssued": "proceeds_from_stock_issuance",
    "commonStockRepurchased": "share_repurchases",
    "dividendsPaid": "dividends_paid",
    "otherFinancingActivites": "other_financing_activities",
    "netCashUsedProvidedByFinancingActivities": "financing_cash_flow",
    "effectOfForexChangesOnCash": "forex_effect_on_cash",
    "netChangeInCash": "change_in_cash",
    "cashAtEndOfPeriod": "cash_end_of_period",
    "cashAtBeginningOfPeriod": "cash_beginning_of_period",
    "operatingCashFlow": "operating_cash_flow",
    "capitalExpenditure": "capital_expenditures",
    "freeCashFlow": "free_cash_flow",

    # ── Metadata ──────────────────────────────────────────────────────────────
    "symbol": "ticker",
    "date": "period_end_date",
    "reportedCurrency": "currency",
    "cik": "cik",
    "fillingDate": "filing_date",
    "acceptedDate": "accepted_date",
    "calendarYear": "fiscal_year",
    "period": "fiscal_period",
}

# ---------------------------------------------------------------------------
# Internal → Display Label
# Human-readable labels for UI / report rendering.
# ---------------------------------------------------------------------------

INTERNAL_TO_DISPLAY: dict[str, str] = {
    # Income Statement
    "revenue": "Revenue",
    "cost_of_revenue": "Cost of Revenue",
    "gross_profit": "Gross Profit",
    "gross_margin": "Gross Margin",
    "operating_expenses": "Operating Expenses",
    "research_and_development": "R&D Expense",
    "selling_general_administrative": "SG&A Expense",
    "operating_income": "Operating Income (EBIT)",
    "operating_margin": "Operating Margin",
    "ebitda": "EBITDA",
    "ebitda_margin": "EBITDA Margin",
    "depreciation_and_amortization": "D&A",
    "interest_expense": "Interest Expense",
    "income_before_tax": "Income Before Tax",
    "income_tax_expense": "Income Tax Expense",
    "net_income": "Net Income",
    "net_profit_margin": "Net Profit Margin",
    "eps_basic": "EPS (Basic)",
    "eps_diluted": "EPS (Diluted)",
    "shares_basic": "Shares Outstanding (Basic)",
    "shares_diluted": "Shares Outstanding (Diluted)",
    # Balance Sheet
    "cash_and_equivalents": "Cash & Equivalents",
    "short_term_investments": "Short-term Investments",
    "accounts_receivable": "Accounts Receivable",
    "inventory": "Inventory",
    "current_assets": "Total Current Assets",
    "property_plant_equipment_net": "PP&E (Net)",
    "goodwill": "Goodwill",
    "intangible_assets": "Intangible Assets",
    "total_assets": "Total Assets",
    "accounts_payable": "Accounts Payable",
    "short_term_debt": "Short-term Debt",
    "current_liabilities": "Total Current Liabilities",
    "long_term_debt": "Long-term Debt",
    "total_liabilities": "Total Liabilities",
    "shareholders_equity": "Shareholders' Equity",
    "total_equity": "Total Equity",
    "retained_earnings": "Retained Earnings",
    "total_debt": "Total Debt",
    "net_debt": "Net Debt",
    # Cash Flow
    "operating_cash_flow": "Operating Cash Flow",
    "capital_expenditures": "Capital Expenditures",
    "free_cash_flow": "Free Cash Flow",
    "investing_cash_flow": "Investing Cash Flow",
    "financing_cash_flow": "Financing Cash Flow",
    "stock_based_compensation": "Stock-based Compensation",
    "dividends_paid": "Dividends Paid",
    "share_repurchases": "Share Repurchases",
    # Computed Ratios
    "current_ratio": "Current Ratio",
    "quick_ratio": "Quick Ratio",
    "cash_ratio": "Cash Ratio",
    "debt_to_equity": "Debt-to-Equity",
    "debt_to_ebitda": "Net Debt / EBITDA",
    "interest_coverage": "Interest Coverage Ratio",
    "return_on_assets": "Return on Assets (ROA)",
    "return_on_equity": "Return on Equity (ROE)",
    "return_on_invested_capital": "Return on Invested Capital (ROIC)",
    "days_sales_outstanding": "Days Sales Outstanding (DSO)",
    "days_inventory_outstanding": "Days Inventory Outstanding (DIO)",
    "days_payable_outstanding": "Days Payable Outstanding (DPO)",
    "cash_conversion_cycle": "Cash Conversion Cycle (CCC)",
    "fcf_margin": "FCF Margin",
    "fcf_conversion": "FCF Conversion Rate",
    "capex_intensity": "CapEx Intensity",
    "revenue_growth_yoy": "Revenue Growth (YoY)",
    "net_income_growth_yoy": "Net Income Growth (YoY)",
    "ebitda_growth_yoy": "EBITDA Growth (YoY)",
    "fcf_growth_yoy": "FCF Growth (YoY)",
}

# ---------------------------------------------------------------------------
# Utility functions for normalization
# ---------------------------------------------------------------------------

def normalize_edgar_data(raw: dict) -> dict:
    """
    Translate an EDGAR XBRL fact dict to internal field names.

    EDGAR facts arrive keyed by concept name (with or without the namespace
    prefix). Both "us-gaap/Revenues" and "Revenues" are handled.

    Returns a new dict with internal field names. Unknown fields are passed
    through unchanged so callers can inspect them.
    """
    result: dict = {}
    for key, value in raw.items():
        # Normalise key: strip namespace prefix variants
        normalised_key = key
        if "/" not in key:
            normalised_key = f"us-gaap/{key}"

        internal = EDGAR_TO_INTERNAL.get(normalised_key) or EDGAR_TO_INTERNAL.get(key)
        if internal:
            # Prefer the first non-None value encountered if multiple XBRL
            # tags map to the same internal field.
            if internal not in result or result[internal] is None:
                result[internal] = value
        else:
            result[key] = value  # pass through unknown fields

    return result


def normalize_fmp_data(raw: dict) -> dict:
    """
    Translate an FMP JSON response dict to internal field names.

    FMP sometimes includes duplicate keys in different statement types
    (e.g., "netIncome" appears in both income statement and cash flow).
    Both are valid; the income statement value takes precedence when both
    are present and non-None.
    """
    result: dict = {}
    for key, value in raw.items():
        internal = FMP_TO_INTERNAL.get(key, key)
        if internal not in result or result[internal] is None:
            result[internal] = value
    return result


def get_display_label(internal_field: str) -> str:
    """Return a human-readable label for an internal field name."""
    return INTERNAL_TO_DISPLAY.get(internal_field, internal_field.replace("_", " ").title())


def build_reverse_mapping(mapping: dict[str, str]) -> dict[str, list[str]]:
    """
    Build a reverse mapping: internal_field → [list of source field names].

    Useful for documentation and debugging — shows all source fields that
    roll up to a given internal field.
    """
    reverse: dict[str, list[str]] = {}
    for source, internal in mapping.items():
        reverse.setdefault(internal, []).append(source)
    return reverse


# Pre-built reverse mappings for inspection
INTERNAL_TO_EDGAR: dict[str, list[str]] = build_reverse_mapping(EDGAR_TO_INTERNAL)
INTERNAL_TO_FMP: dict[str, list[str]] = build_reverse_mapping(FMP_TO_INTERNAL)
