// Demo data for GitHub Pages static deployment — realistic Apple Inc (AAPL) FY2024 data

export const DEMO_COMPANY = {
  id: 'demo-aapl',
  ticker: 'AAPL',
  name: 'Apple Inc.',
  sector: 'Technology',
  industry: 'Consumer Electronics',
  exchange: 'NASDAQ',
  market_cap: 3200000000000,
  description:
    'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company offers iPhone, Mac, iPad, and Wearables product lines. It also provides AppleCare support and cloud services, and operates platforms that allow customers to discover and download applications and digital content.',
  cik: '0000320193',
  country: 'US',
  is_active: true,
}

export const DEMO_RATIOS = [
  { id: '1', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'gross_margin', value: 46.2, formula: '(Revenue - COGS) / Revenue = ($391.0B - $210.4B) / $391.0B', inputs: { revenue: 391035000000, cogs: 210352000000 }, confidence: 0.98, source: 'SEC_EDGAR', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '2', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'operating_margin', value: 31.5, formula: 'Operating Income / Revenue = $123.2B / $391.0B', inputs: { operating_income: 123216000000, revenue: 391035000000 }, confidence: 0.98, source: 'SEC_EDGAR', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '3', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'net_profit_margin', value: 26.4, formula: 'Net Income / Revenue = $93.7B / $391.0B', inputs: { net_income: 93736000000, revenue: 391035000000 }, confidence: 0.98, source: 'SEC_EDGAR', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '4', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'revenue_growth_yoy', value: 2.1, formula: '(Rev_2024 - Rev_2023) / Rev_2023 = ($391.0B - $383.3B) / $383.3B', inputs: { revenue_2024: 391035000000, revenue_2023: 383285000000 }, confidence: 0.97, source: 'SEC_EDGAR', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '5', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'return_on_equity', value: 164.2, formula: 'Net Income / Avg Shareholders Equity = $93.7B / $57.1B', inputs: { net_income: 93736000000, avg_equity: 57096500000 }, confidence: 0.95, source: 'SEC_EDGAR', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '6', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'return_on_invested_capital', value: 54.8, formula: 'NOPAT / Invested Capital = $102.6B / $187.2B', inputs: { nopat: 102569000000, invested_capital: 187200000000 }, confidence: 0.93, source: 'CALCULATED', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '7', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'free_cash_flow', value: 108807000000, formula: 'Operating CF - CapEx = $118.3B - $9.4B', inputs: { operating_cf: 118254000000, capex: 9447000000 }, confidence: 0.98, source: 'SEC_EDGAR', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '8', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'debt_to_ebitda', value: 0.9, formula: 'Net Debt / EBITDA = $67.8B / $134.7B', inputs: { net_debt: 67815000000, ebitda: 134661000000 }, confidence: 0.94, source: 'CALCULATED', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '9', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'current_ratio', value: 0.87, formula: 'Current Assets / Current Liabilities = $143.6B / $176.4B', inputs: { current_assets: 143566000000, current_liabilities: 176392000000 }, confidence: 0.98, source: 'SEC_EDGAR', calculated_at: '2024-11-01T00:00:00Z' },
  { id: '10', company_id: 'demo-aapl', period: '2024-FY', ratio_name: 'ebitda', value: 134661000000, formula: 'Operating Income + D&A = $123.2B + $11.4B', inputs: { operating_income: 123216000000, da: 11445000000 }, confidence: 0.97, source: 'CALCULATED', calculated_at: '2024-11-01T00:00:00Z' },
]

export const DEMO_FILINGS = [
  { id: 'f1', company_id: 'demo-aapl', form_type: '10-K', filed_at: '2024-11-01T00:00:00Z', period_of_report: 'FY2024', accession_number: '0000320193-24-000123', filing_url: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-K', document_url: null, is_processed: true, created_at: '2024-11-01T00:00:00Z' },
  { id: 'f2', company_id: 'demo-aapl', form_type: '10-Q', filed_at: '2024-08-02T00:00:00Z', period_of_report: 'Q3 FY2024', accession_number: '0000320193-24-000098', filing_url: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=10-Q', document_url: null, is_processed: true, created_at: '2024-08-02T00:00:00Z' },
  { id: 'f3', company_id: 'demo-aapl', form_type: '8-K', filed_at: '2024-10-31T00:00:00Z', period_of_report: 'Q4 FY2024 Earnings', accession_number: '0000320193-24-000121', filing_url: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=8-K', document_url: null, is_processed: true, created_at: '2024-10-31T00:00:00Z' },
  { id: 'f4', company_id: 'demo-aapl', form_type: 'DEF 14A', filed_at: '2024-01-12T00:00:00Z', period_of_report: 'Annual Meeting 2024', accession_number: '0000320193-24-000008', filing_url: 'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000320193&type=DEF+14A', document_url: null, is_processed: true, created_at: '2024-01-12T00:00:00Z' },
]

export const DEMO_GOVERNANCE = {
  id: 'g1', company_id: 'demo-aapl', period: '2024',
  board_size: 9, independent_directors: 8, ceo_chairman_combined: false,
  insider_ownership_pct: 0.4, institutional_ownership_pct: 60.1,
  executive_comp_total: 63200000, has_poison_pill: false,
  has_dual_class: false, staggered_board: false,
}

export const DEMO_EVIDENCE = [
  { claim: 'Revenue grew 2.1% year-over-year to $391.0B in FY2024', value: 391035000000, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Total Net Sales', formula: '($391.0B - $383.3B) / $383.3B = +2.1%' },
  { claim: 'Gross margin expanded to 46.2% from 44.1% in the prior year', value: 46.2, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Gross Margin %', formula: '($391.0B - $210.4B) / $391.0B = 46.2%' },
  { claim: 'Free cash flow of $108.8B demonstrates exceptional cash generation', value: 108807000000, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Free Cash Flow', formula: 'Operating CF $118.3B - CapEx $9.4B = $108.8B' },
  { claim: 'Services segment revenue reached $96.2B, up 12.7% YoY', value: 96169000000, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Services Revenue', formula: '($96.2B - $85.2B) / $85.2B = +12.7%' },
  { claim: 'Board is 89% independent (8 of 9 directors)', value: 88.9, source: 'SEC_EDGAR' as const, filing_type: 'DEF 14A', period: 'FY2024', metric_name: 'Board Independence %', formula: '8 independent / 9 total = 88.9%' },
  { claim: 'Net debt of $67.8B represents 0.9x EBITDA — conservative leverage', value: 0.9, source: 'CALCULATED' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Net Debt / EBITDA', formula: '$67.8B net debt / $134.7B EBITDA = 0.9x' },
  { claim: 'ROIC of 54.8% far exceeds cost of capital, signaling strong value creation', value: 54.8, source: 'CALCULATED' as const, filing_type: null, period: 'FY2024', metric_name: 'Return on Invested Capital', formula: 'NOPAT $102.6B / Invested Capital $187.2B = 54.8%' },
]

export const DEMO_REPORT = {
  id: 'demo-report',
  company_id: 'demo-aapl',
  ticker: 'AAPL',
  report_type: 'full',
  status: 'completed' as const,
  financial_analysis: {
    agent_name: 'Financial Statement Analyst',
    ticker: 'AAPL',
    analysis: {
      revenue_analysis: { trend: 'decelerating', cagr_3y: 5.2, commentary: 'Revenue grew 2.1% YoY to $391.0B in FY2024, decelerating from prior years as iPhone saturation weighs on growth. Services segment (24.6% of revenue) grew 12.7%, offsetting hardware weakness.' },
      profitability_analysis: { gross_margin_trend: 'expanding', operating_leverage: 'positive', commentary: 'Gross margin expanded 210bps to 46.2% driven by favorable Services mix shift and supply chain efficiencies. Operating leverage remains exceptional at 31.5% operating margin.' },
      cash_flow_quality: { fcf_conversion: 1.16, commentary: 'FCF conversion of 116% of net income signals high earnings quality with minimal accruals. $108.8B FCF funds the $110.2B capital return program.' },
      balance_sheet_health: { leverage_assessment: 'conservative', liquidity_assessment: 'adequate', commentary: 'Net debt/EBITDA of 0.9x is conservative. Current ratio below 1.0x is structural due to deferred revenue and is not a liquidity concern.' },
      financial_strength_score: 88,
      growth_score: 62,
      profitability_score: 96,
      key_strengths: ['Industry-leading 46.2% gross margins (SEC 10-K FY2024)', 'Exceptional FCF generation of $108.8B (SEC 10-K FY2024)', 'Services revenue growing 12.7% YoY providing recurring income', 'ROIC of 54.8% far exceeds cost of capital'],
      key_concerns: ['iPhone revenue flat YoY at $201.2B — 51% revenue concentration', 'Greater China revenue declined 8.0% YoY to $66.9B', 'Hardware segment growth of -1.7% shows saturation'],
      analyst_summary: 'Apple demonstrates best-in-class financial metrics with 46.2% gross margins and $108.8B in free cash flow. The Services pivot is progressing well (+12.7% YoY) though hardware concentration and China exposure remain key watch items. Overall financial quality is exceptional.',
    },
    evidence: DEMO_EVIDENCE,
    confidence: 0.94,
    data_quality_warnings: [],
    missing_data: [],
    generated_at: '2024-11-15T10:23:00Z',
    model_used: 'claude-sonnet-4-6',
    tokens_used: 4821,
  },
  governance_analysis: {
    agent_name: 'Governance Analyst',
    ticker: 'AAPL',
    analysis: {
      board_assessment: { independence_ratio: 0.889, size_assessment: 'optimal', ceo_chairman_separation: true, commentary: '8 of 9 directors are independent. CEO/Chairman roles are separated (Tim Cook CEO, Arthur Levinson Chairman).' },
      compensation_assessment: { pay_for_performance: 'strong', excessive_pay_flags: [], commentary: '$63.2M total CEO compensation is tied 90%+ to performance metrics including revenue growth and relative TSR vs S&P 500.' },
      shareholder_rights: { dual_class_structure: false, poison_pill: false, staggered_board: false, shareholder_friendly_score: 88 },
      insider_ownership: { percentage: 0.4, alignment_assessment: 'low', commentary: '0.4% insider ownership is low but typical for mega-cap companies. Institutional ownership of 60.1% provides strong oversight.' },
      governance_score: 82,
      governance_grade: 'B',
      red_flags: [],
      governance_risk_assessment: 'Low',
      analyst_summary: 'Apple demonstrates strong governance: independent board, separated CEO/Chairman, no dual-class structure, no poison pill. Compensation is well-aligned with performance.',
    },
    evidence: DEMO_EVIDENCE.slice(3),
    confidence: 0.88,
    data_quality_warnings: [],
    missing_data: [],
    generated_at: '2024-11-15T10:24:00Z',
    model_used: 'claude-sonnet-4-6',
    tokens_used: 3102,
  },
  valuation_analysis: {
    agent_name: 'Valuation Analyst',
    ticker: 'AAPL',
    analysis: {
      trading_multiples: { pe_ratio: 34.1, ev_ebitda: 26.8, ev_revenue: 8.4, p_fcf: 29.4, vs_peers: { pe_premium_discount_pct: 18.2, ev_ebitda_premium_discount_pct: 22.4 } },
      comps_implied_value: { low: 168, midpoint: 198, high: 241, methodology: 'Median peer EV/EBITDA of 21.9x applied to FY2024 EBITDA; P/E of 28.8x applied to FY2024 EPS of $6.08' },
      dcf_analysis: { status: 'assumptions_required', message: 'DCF requires explicit user-provided WACC and terminal growth rate. AI does not generate these assumptions.' },
      margin_of_safety: null,
      valuation_summary: 'expensive',
      current_price: 207.43,
      analyst_summary: 'AAPL trades at 18-22% premium to peers on P/E and EV/EBITDA. At $207 vs. comps-implied midpoint of $198, the stock appears modestly overvalued on fundamentals.',
    },
    evidence: DEMO_EVIDENCE.slice(0, 3),
    confidence: 0.82,
    data_quality_warnings: ['DCF not computed — user-provided WACC required'],
    missing_data: ['dcf_wacc', 'dcf_terminal_growth_rate'],
    generated_at: '2024-11-15T10:25:00Z',
    model_used: 'claude-sonnet-4-6',
    tokens_used: 2891,
  },
  risk_analysis: {
    agent_name: 'Risk Analyst',
    ticker: 'AAPL',
    analysis: {
      risk_categories: {
        financial_risk: { severity: 'Low', factors: ['Conservative 0.9x Net Debt/EBITDA', 'Strong FCF covers all obligations'] },
        operational_risk: { severity: 'Moderate', factors: ['Heavy reliance on Foxconn for manufacturing', 'Supply chain concentration in Asia'] },
        regulatory_risk: { severity: 'High', factors: ['EU Digital Markets Act: App Store forced to open', 'DOJ antitrust case regarding iPhone monopoly', 'EU €13B tax case ruling (Irish state aid)'] },
        competitive_risk: { severity: 'Moderate', factors: ['Android at 72% global smartphone share', 'Huawei re-entry into premium segment in China'] },
        macro_risk: { severity: 'Moderate', factors: ['China revenue 17.1% of total, down 8% YoY', 'USD strength pressure on international revenue'] },
        management_risk: { severity: 'Low', factors: ['Tim Cook succession not yet disclosed'] },
      },
      key_risk_factors: [
        'Regulatory scrutiny of App Store in US and EU could reduce high-margin Services revenue',
        'China revenue declined 8% — geopolitical tensions and Huawei competition intensifying',
        'DOJ antitrust investigation into iPhone monopoly practices',
        'Apple Intelligence adoption critical for next upgrade cycle',
        'Manufacturing concentration: 90%+ production in China/Taiwan',
      ],
      financial_risk_signals: { debt_concern: false, liquidity_concern: false, margin_compression: false },
      bear_case: 'DOJ forces structural App Store changes (est. -$15-20B EBIT impact), China revenue declines 15% annually as Huawei gains share, Apple Intelligence disappoints. Combined, operating margins compress to 27-28% and the stock de-rates to peer multiples (~28x P/E), implying $155-165.',
      worst_case_scenario: 'Forced App Store restructuring (-$18B EBIT) + China market share loss (-15% revenue) + consumer slowdown (-5%) could reduce FY2026E EPS to $4.80 vs. consensus $7.40. At trough 22x P/E: ~$105 (-49%).',
      risk_score: 38,
      risk_rating: 'Moderate',
      analyst_summary: 'Apple faces meaningful regulatory risk and China headwinds, offset by financial strength and ecosystem lock-in. Overall risk is Moderate — the balance sheet absorbs adverse scenarios but regulatory outcomes could impair the Services segment.',
    },
    evidence: DEMO_EVIDENCE,
    confidence: 0.86,
    data_quality_warnings: [],
    missing_data: [],
    generated_at: '2024-11-15T10:26:00Z',
    model_used: 'claude-sonnet-4-6',
    tokens_used: 5234,
  },
  investment_committee: {
    agent_name: 'Investment Committee',
    ticker: 'AAPL',
    analysis: {
      investment_thesis: "Apple is the highest-quality franchise in global technology with a growing Services business providing durable recurring revenue. At 34x P/E the stock prices in perfection, warranting a Hold. Existing holders benefit from $110B/year capital return and the unmatched ecosystem moat, but near-term risk/reward is balanced given regulatory overhangs and China headwinds.",
      bull_case: {
        scenario: 'Apple Intelligence drives the largest iPhone upgrade cycle in a decade, with AI features pushing ASP to $870+ from $825. Services accelerates to 15%+ growth. Regulatory risk settles via out-of-court agreements.',
        key_drivers: ['Apple Intelligence triggers 15%+ upgrade cycle in FY2025-2026', 'Services revenue reaches $115B by FY2026 (+20% CAGR)', 'Margin expansion to 48%+ as Services mix grows', '$115B buyback + dividend in FY2025'],
        price_target_upside_pct: 28,
      },
      bear_case: {
        scenario: 'DOJ forces App Store structural changes, China revenue declines accelerate as Huawei re-establishes premium position, and Apple Intelligence adoption disappoints — delaying upgrade cycle 12-18 months.',
        key_risks: ['DOJ removes 25-30% of Services gross profit', 'China declines accelerate to -15% YoY', 'AI features fail to drive upgrade cycle'],
        downside_scenario_pct: -26,
      },
      recommendation: 'Hold',
      conviction: 'Moderate',
      confidence_score: 79,
      what_would_change_view: [
        'Upgrade to Buy: DOJ settlement preserves App Store economics + Apple Intelligence drives 15%+ iPhone growth + China stabilizes',
        'Downgrade to Sell: App Store restructuring cuts Services margins below 60% OR China declines exceed 20%',
      ],
      key_metrics_to_watch: ['iPhone unit volumes (quarterly)', 'Services gross margin %', 'China revenue growth', 'Apple Intelligence adoption', 'DOJ case developments'],
      time_horizon: 'Medium-term (1-3yr)',
      suitable_investor: 'Quality-focused long-term investors seeking capital preservation with moderate growth. Not suitable for value investors (premium valuation) or pure growth investors (decelerating revenue).',
      executive_summary: "Apple Inc. (AAPL) is rated HOLD at $207.43. The company shows exceptional financial quality — 46.2% gross margins, $108.8B FCF, 54.8% ROIC — supported by the world's most valuable consumer technology ecosystem. However at 34x P/E (18% premium to peers), the stock fully prices this quality. Near-term catalysts (Apple Intelligence, iPhone 17) are balanced against meaningful risks (DOJ antitrust, China -8% YoY, EU App Store pressure). Bull case $265 (+28%) if AI upgrade materializes; bear case $153 (-26%) if regulatory and China headwinds compound.",
    },
    evidence: DEMO_EVIDENCE,
    confidence: 0.87,
    data_quality_warnings: [],
    missing_data: ['dcf_assumptions'],
    generated_at: '2024-11-15T10:27:00Z',
    model_used: 'claude-sonnet-4-6',
    tokens_used: 6102,
  },
  pdf_path: null,
  error_message: null,
  created_at: '2024-11-15T10:23:00Z',
  completed_at: '2024-11-15T10:27:00Z',
}

export const DEMO_COMPETITORS = [
  { ticker: 'AAPL', name: 'Apple Inc.', revenue_growth: 2.1, gross_margin: 46.2, net_margin: 26.4, roe: 164.2, roic: 54.8, debt_ebitda: 0.9, pe_ratio: 34.1, ev_ebitda: 26.8, governance_score: 82 },
  { ticker: 'MSFT', name: 'Microsoft', revenue_growth: 16.0, gross_margin: 70.1, net_margin: 36.4, roe: 38.2, roic: 28.4, debt_ebitda: 0.6, pe_ratio: 36.2, ev_ebitda: 29.1, governance_score: 88 },
  { ticker: 'GOOGL', name: 'Alphabet', revenue_growth: 8.7, gross_margin: 56.9, net_margin: 23.8, roe: 23.4, roic: 22.1, debt_ebitda: null, pe_ratio: 23.4, ev_ebitda: 19.8, governance_score: 72 },
  { ticker: 'META', name: 'Meta Platforms', revenue_growth: 22.1, gross_margin: 81.5, net_margin: 33.9, roe: 34.7, roic: 29.8, debt_ebitda: null, pe_ratio: 27.8, ev_ebitda: 22.4, governance_score: 61 },
  { ticker: 'AMZN', name: 'Amazon', revenue_growth: 11.0, gross_margin: 47.6, net_margin: 9.4, roe: 21.2, roic: 14.8, debt_ebitda: 1.2, pe_ratio: 44.1, ev_ebitda: 18.7, governance_score: 74 },
]

export const DEMO_CHART_DATA = [
  { period: 'FY2020', revenue: 274515000000, gross_margin: 38.2, operating_margin: 24.1, net_margin: 20.9 },
  { period: 'FY2021', revenue: 365817000000, gross_margin: 41.8, operating_margin: 29.8, net_margin: 25.9 },
  { period: 'FY2022', revenue: 394328000000, gross_margin: 43.3, operating_margin: 30.3, net_margin: 25.3 },
  { period: 'FY2023', revenue: 383285000000, gross_margin: 44.1, operating_margin: 29.8, net_margin: 25.3 },
  { period: 'FY2024', revenue: 391035000000, gross_margin: 46.2, operating_margin: 31.5, net_margin: 26.4 },
]

export const DEMO_WATCHLIST = [
  { id: 'w1', company: DEMO_COMPANY, added_at: '2024-11-01T00:00:00Z', notes: null },
  { id: 'w2', company: { ...DEMO_COMPANY, id: 'msft', ticker: 'MSFT', name: 'Microsoft Corp.', market_cap: 3100000000000 }, added_at: '2024-11-02T00:00:00Z', notes: null },
  { id: 'w3', company: { ...DEMO_COMPANY, id: 'nvda', ticker: 'NVDA', name: 'NVIDIA Corp.', market_cap: 2800000000000 }, added_at: '2024-11-03T00:00:00Z', notes: null },
]
