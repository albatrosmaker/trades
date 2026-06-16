export interface Company {
  id: string
  ticker: string
  name: string
  sector: string | null
  industry: string | null
  exchange: string | null
  market_cap: number | null
  description: string | null
  cik: string | null
  country: string
  is_active: boolean
}

export interface FinancialStatement {
  id: string
  company_id: string
  period: string
  fiscal_year: number
  fiscal_quarter: number | null
  statement_type: 'income' | 'balance' | 'cashflow'
  data: Record<string, number | null>
  source: string
  trust_level: number
  filing_url: string | null
  filed_at: string | null
  created_at: string
}

export interface FinancialRatio {
  id: string
  company_id: string
  period: string
  ratio_name: string
  value: number | null
  formula: string | null
  inputs: Record<string, number | null>
  confidence: number
  source: string
  calculated_at: string
}

export type DataSource = 'SEC_EDGAR' | 'FMP' | 'YAHOO' | 'CALCULATED'

export interface Evidence {
  claim: string
  value: string | number | null
  source: DataSource
  filing_type: string | null
  period: string | null
  metric_name: string | null
  formula: string | null
}

export interface AgentOutput {
  agent_name: string
  ticker: string
  analysis: Record<string, unknown>
  evidence: Evidence[]
  confidence: number
  data_quality_warnings: string[]
  missing_data: string[]
  generated_at: string
  model_used: string
  tokens_used: number
}

export interface ResearchReport {
  id: string
  company_id: string
  ticker: string
  report_type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  financial_analysis: AgentOutput | null
  governance_analysis: AgentOutput | null
  valuation_analysis: AgentOutput | null
  risk_analysis: AgentOutput | null
  investment_committee: AgentOutput | null
  pdf_path: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface AnalysisJob {
  id: string
  ticker: string | null
  job_type: string
  status: 'queued' | 'running' | 'completed' | 'failed'
  result: Record<string, unknown> | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface WatchlistItem {
  id: string
  company: Company
  added_at: string
  notes: string | null
}

export interface SECFiling {
  id: string
  company_id: string
  form_type: string
  filed_at: string
  period_of_report: string | null
  accession_number: string | null
  filing_url: string
  document_url: string | null
  is_processed: boolean
  created_at: string
}

export interface GovernanceData {
  id: string
  company_id: string
  period: string
  board_size: number | null
  independent_directors: number | null
  ceo_chairman_combined: boolean | null
  insider_ownership_pct: number | null
  institutional_ownership_pct: number | null
  executive_comp_total: number | null
  has_poison_pill: boolean | null
  has_dual_class: boolean | null
  staggered_board: boolean | null
}

export type Recommendation = 'Strong Buy' | 'Buy' | 'Hold' | 'Sell' | 'Strong Sell'

export interface DCFAssumptions {
  wacc: number
  terminal_growth_rate: number
  projection_years: number
  revenue_growth_rates?: number[]
  ebitda_margin?: number
  capex_pct_revenue?: number
  tax_rate?: number
}
