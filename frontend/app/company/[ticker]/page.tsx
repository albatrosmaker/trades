'use client'
import { useState } from 'react'
import { useParams } from 'next/navigation'
import { BookMarked, PlayCircle, ExternalLink } from 'lucide-react'
import { Navbar } from '@/components/layout/Navbar'
import { MetricCard } from '@/components/ui/MetricCard'
import { ScoreGauge } from '@/components/ui/ScoreGauge'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import { SourceBadge } from '@/components/ui/SourceBadge'
import { SECFilingViewer } from '@/components/ui/SECFilingViewer'
import { EvidencePanel } from '@/components/ui/EvidencePanel'
import { AgentStatusCard } from '@/components/ui/AgentStatusCard'
import { CompetitorTable } from '@/components/ui/CompetitorTable'
import {
  useCompany, useRatios, useFilings, useGovernance,
  useCompanyReports, useTriggerAnalysis, useJobPolling,
} from '@/hooks/useAnalysis'
import { formatCurrency } from '@/lib/formatters'
import type { Evidence, Recommendation } from '@/lib/types'

const TABS = ['Overview', 'Financials', 'Governance', 'Valuation', 'Risks', 'Report'] as const
type Tab = typeof TABS[number]

export default function CompanyPage() {
  const { ticker } = useParams<{ ticker: string }>()
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)

  const { data: company, isLoading } = useCompany(ticker)
  const { data: ratios = [] } = useRatios(ticker)
  const { data: filings = [] } = useFilings(ticker)
  const { data: governance } = useGovernance(ticker)
  const { data: reports = [] } = useCompanyReports(ticker)
  const triggerMutation = useTriggerAnalysis()
  const jobQuery = useJobPolling(jobId)

  const latestReport = reports.find(r => r.status === 'completed')

  function getRatio(name: string) {
    return ratios.find(r => r.ratio_name === name)
  }

  async function handleAnalyze() {
    const result = await triggerMutation.mutateAsync({ ticker })
    setJobId(result.job_id)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
            <p className="text-gray-400 text-sm font-mono">Loading {ticker}...</p>
          </div>
        </div>
      </div>
    )
  }

  const ic = latestReport?.investment_committee
  const recommendation = ic?.analysis?.recommendation as Recommendation | undefined

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="flex-1 overflow-y-auto">
        {/* Company header */}
        <div className="border-b border-[#1e2d4a] bg-[#0a0e1a] px-6 py-5">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-2xl font-bold text-white font-mono">{ticker}</h1>
                  {recommendation && <RecommendationBadge recommendation={recommendation} />}
                </div>
                <p className="text-gray-400 text-sm">{company?.name ?? '—'}</p>
                <div className="flex items-center gap-2 mt-2">
                  {company?.sector && (
                    <span className="text-xs bg-[#1e2d4a] text-gray-400 px-2 py-0.5 rounded">{company.sector}</span>
                  )}
                  {company?.industry && (
                    <span className="text-xs bg-[#1e2d4a] text-gray-400 px-2 py-0.5 rounded">{company.industry}</span>
                  )}
                  {company?.exchange && (
                    <span className="text-xs text-gray-500 font-mono">{company.exchange}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-3">
                {company?.market_cap && (
                  <div className="text-right">
                    <p className="text-xs text-gray-500">Market Cap</p>
                    <p className="text-lg font-mono font-bold text-white">{formatCurrency(company.market_cap)}</p>
                  </div>
                )}
                <button
                  onClick={handleAnalyze}
                  disabled={triggerMutation.isPending || jobQuery.data?.status === 'running'}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-60"
                >
                  <PlayCircle className="w-4 h-4" />
                  {jobQuery.data?.status === 'running' ? 'Analyzing...' : 'Run Analysis'}
                </button>
                <button className="p-2 border border-[#1e2d4a] text-gray-400 hover:text-white rounded-lg transition-colors">
                  <BookMarked className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 mt-5">
              {TABS.map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-[#1e2d4a]'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tab content */}
        <div className="max-w-6xl mx-auto px-6 py-6">

          {/* Overview */}
          {activeTab === 'Overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Revenue', key: 'revenue', format: 'currency' as const },
                  { label: 'Gross Margin', key: 'gross_margin', format: 'percent' as const },
                  { label: 'Net Margin', key: 'net_profit_margin', format: 'percent' as const },
                  { label: 'FCF', key: 'free_cash_flow', format: 'currency' as const },
                  { label: 'ROE', key: 'return_on_equity', format: 'percent' as const },
                  { label: 'ROIC', key: 'return_on_invested_capital', format: 'percent' as const },
                  { label: 'Debt/EBITDA', key: 'debt_to_ebitda', format: 'multiple' as const },
                  { label: 'Rev Growth YoY', key: 'revenue_growth_yoy', format: 'percent' as const },
                ].map(({ label, key, format }) => {
                  const ratio = getRatio(key)
                  return (
                    <MetricCard
                      key={key}
                      label={label}
                      value={ratio?.value}
                      source={ratio?.source ?? 'CALCULATED'}
                      confidence={ratio?.confidence ?? 0}
                      format={format}
                      onClick={ratio ? () => setSelectedEvidence({
                        claim: `${label}: ${ratio.value}`,
                        value: ratio.value,
                        source: ratio.source as Evidence['source'],
                        filing_type: null,
                        period: ratio.period,
                        metric_name: label,
                        formula: ratio.formula,
                      }) : undefined}
                    />
                  )
                })}
              </div>

              {company?.description && (
                <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
                  <h3 className="text-sm font-medium text-gray-400 mb-2">Company Description</h3>
                  <p className="text-sm text-gray-300 leading-relaxed">{company.description}</p>
                </div>
              )}

              {latestReport?.investment_committee && (
                <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
                  <h3 className="text-sm font-medium text-gray-400 mb-3">Investment Thesis</h3>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {latestReport.investment_committee.analysis?.investment_thesis as string ?? 'Run analysis to generate investment thesis.'}
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Governance */}
          {activeTab === 'Governance' && (
            <div className="space-y-6">
              {governance ? (
                <div className="grid grid-cols-2 gap-6">
                  <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5 space-y-4">
                    <h3 className="text-sm font-medium text-white">Board Composition</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {[
                        { label: 'Board Size', value: governance.board_size },
                        { label: 'Independent Directors', value: governance.independent_directors },
                        { label: 'CEO/Chair Combined', value: governance.ceo_chairman_combined !== null ? (governance.ceo_chairman_combined ? 'Yes' : 'No') : null },
                        { label: 'Staggered Board', value: governance.staggered_board !== null ? (governance.staggered_board ? 'Yes' : 'No') : null },
                      ].map(row => (
                        <div key={row.label}>
                          <p className="text-xs text-gray-500">{row.label}</p>
                          <p className="text-white font-mono">{row.value ?? '—'}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5 space-y-4">
                    <h3 className="text-sm font-medium text-white">Ownership & Rights</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {[
                        { label: 'Insider Ownership', value: governance.insider_ownership_pct !== null ? `${governance.insider_ownership_pct?.toFixed(1)}%` : null },
                        { label: 'Institutional Ownership', value: governance.institutional_ownership_pct !== null ? `${governance.institutional_ownership_pct?.toFixed(1)}%` : null },
                        { label: 'Dual Class Structure', value: governance.has_dual_class !== null ? (governance.has_dual_class ? 'Yes' : 'No') : null },
                        { label: 'Poison Pill', value: governance.has_poison_pill !== null ? (governance.has_poison_pill ? 'Yes' : 'No') : null },
                      ].map(row => (
                        <div key={row.label}>
                          <p className="text-xs text-gray-500">{row.label}</p>
                          <p className="text-white font-mono">{row.value ?? '—'}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-8 text-center text-gray-500">
                  <p className="text-sm">Governance data requires running an analysis first.</p>
                </div>
              )}
              {latestReport?.governance_analysis && (
                <AgentStatusCard
                  agentName="Governance Analyst"
                  status="completed"
                  output={latestReport.governance_analysis}
                />
              )}
            </div>
          )}

          {/* Risks */}
          {activeTab === 'Risks' && (
            <div className="space-y-4">
              {latestReport?.risk_analysis ? (
                <>
                  <AgentStatusCard agentName="Risk Analyst" status="completed" output={latestReport.risk_analysis} />
                  {latestReport.risk_analysis.analysis?.bear_case && (
                    <div className="bg-red-900/10 border border-red-900/50 rounded-xl p-5">
                      <h3 className="text-sm font-medium text-red-400 mb-2">Bear Case</h3>
                      <p className="text-sm text-gray-300 leading-relaxed">
                        {latestReport.risk_analysis.analysis.bear_case as string}
                      </p>
                    </div>
                  )}
                </>
              ) : (
                <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-8 text-center text-gray-500">
                  <p className="text-sm">Risk analysis requires running an analysis first.</p>
                </div>
              )}
            </div>
          )}

          {/* SEC Filings */}
          {activeTab === 'Financials' && (
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-400">SEC Filings</h3>
              {filings.length === 0 ? (
                <p className="text-sm text-gray-500">No filings loaded. Run an analysis to ingest SEC data.</p>
              ) : (
                filings.slice(0, 10).map(filing => (
                  <SECFilingViewer key={filing.id} filing={filing} />
                ))
              )}
            </div>
          )}

          {/* Report */}
          {activeTab === 'Report' && (
            <div className="space-y-4">
              {reports.length === 0 ? (
                <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-8 text-center text-gray-500">
                  <p className="text-sm">No reports yet. Click &ldquo;Run Analysis&rdquo; to generate one.</p>
                </div>
              ) : (
                reports.map(report => (
                  <div key={report.id} className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-4 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-white">{report.ticker} Research Report</p>
                      <p className="text-xs text-gray-500 font-mono mt-0.5">{report.created_at}</p>
                    </div>
                    {report.status === 'completed' && (
                      <a href={`/company/${ticker}/report/${report.id}`} className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1">
                        View Report <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === 'Valuation' && (
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-8 text-center text-gray-500">
              <p className="text-sm">Valuation analysis available after running full analysis.</p>
              <p className="text-xs mt-2">DCF requires your own WACC and terminal growth rate assumptions.</p>
            </div>
          )}
        </div>
      </div>

      <EvidencePanel evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)} />
    </div>
  )
}
