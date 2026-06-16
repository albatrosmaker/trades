'use client'
import { useState } from 'react'
import Link from 'next/link'
import { ExternalLink } from 'lucide-react'
import { MetricCard } from '@/components/ui/MetricCard'
import { ScoreGauge } from '@/components/ui/ScoreGauge'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import { SECFilingViewer } from '@/components/ui/SECFilingViewer'
import { EvidencePanel } from '@/components/ui/EvidencePanel'
import { AgentStatusCard } from '@/components/ui/AgentStatusCard'
import { CompetitorTable } from '@/components/ui/CompetitorTable'
import { FinancialChart } from '@/components/ui/FinancialChart'
import { SourceBadge } from '@/components/ui/SourceBadge'
import { formatCurrency } from '@/lib/formatters'
import {
  DEMO_COMPANY, DEMO_RATIOS, DEMO_FILINGS, DEMO_GOVERNANCE,
  DEMO_REPORT, DEMO_COMPETITORS, DEMO_CHART_DATA,
} from '@/lib/demo-data'
import type { Evidence, Recommendation } from '@/lib/types'

const TABS = ['Overview', 'Financials', 'Governance', 'Valuation', 'Risks', 'Report'] as const
type Tab = typeof TABS[number]

export function CompanyDashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null)

  const ic = DEMO_REPORT.investment_committee
  const recommendation = ic.analysis.recommendation as Recommendation

  function getRatio(name: string) {
    return DEMO_RATIOS.find(r => r.ratio_name === name)
  }

  const finScore = DEMO_REPORT.financial_analysis.analysis.financial_strength_score as number
  const govScore = DEMO_REPORT.governance_analysis.analysis.governance_score as number
  const riskScore = DEMO_REPORT.risk_analysis.analysis.risk_score as number

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <div className="border-b border-[#1e2d4a] bg-[#0a0e1a] px-6 py-5">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-3 mb-1">
                <Link href="/" className="text-xs text-gray-500 hover:text-gray-300 transition-colors">← Home</Link>
                <span className="text-gray-700">|</span>
                <h1 className="text-2xl font-bold text-white font-mono">AAPL</h1>
                <RecommendationBadge recommendation={recommendation} />
              </div>
              <p className="text-gray-400 text-sm">{DEMO_COMPANY.name}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs bg-[#1e2d4a] text-gray-400 px-2 py-0.5 rounded">{DEMO_COMPANY.sector}</span>
                <span className="text-xs bg-[#1e2d4a] text-gray-400 px-2 py-0.5 rounded">{DEMO_COMPANY.industry}</span>
                <span className="text-xs text-gray-500 font-mono">{DEMO_COMPANY.exchange}</span>
                <SourceBadge source="SEC_EDGAR" />
              </div>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-500">Market Cap</p>
              <p className="text-2xl font-mono font-bold text-white">{formatCurrency(DEMO_COMPANY.market_cap)}</p>
              <p className="text-xs text-gray-500 mt-1 font-mono">$207.43 per share</p>
            </div>
          </div>

          <div className="flex gap-1 mt-5">
            {TABS.map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  activeTab === tab ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-[#1e2d4a]'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto px-6 py-6 w-full">

        {activeTab === 'Overview' && (
          <div className="space-y-6">
            {/* Score gauges */}
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
              <h3 className="text-sm font-medium text-gray-400 mb-4">AI Analysis Scores</h3>
              <div className="flex items-center justify-around">
                <ScoreGauge score={finScore} label="Financial Strength" size={110} />
                <ScoreGauge score={DEMO_REPORT.financial_analysis.analysis.growth_score as number} label="Growth" size={110} />
                <ScoreGauge score={DEMO_REPORT.financial_analysis.analysis.profitability_score as number} label="Profitability" size={110} />
                <ScoreGauge score={govScore} label="Governance" size={110} />
                <ScoreGauge score={100 - riskScore} label="Safety" size={110} />
              </div>
            </div>

            {/* Key metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Revenue (FY2024)', key: 'free_cash_flow', displayValue: '$391.0B', source: 'SEC_EDGAR', conf: 0.98, ev: { claim: 'Total Revenue FY2024', value: 391035000000, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Net Sales', formula: 'Per Income Statement, SEC 10-K p.32' } },
                { label: 'Gross Margin', key: 'gross_margin', displayValue: '46.2%', source: 'SEC_EDGAR', conf: 0.98, ev: { claim: 'Gross margin 46.2%', value: 46.2, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Gross Margin %', formula: '($391.0B - $210.4B) / $391.0B = 46.2%' } },
                { label: 'Net Margin', key: 'net_profit_margin', displayValue: '26.4%', source: 'SEC_EDGAR', conf: 0.98, ev: { claim: 'Net profit margin 26.4%', value: 26.4, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Net Profit Margin', formula: '$93.7B / $391.0B = 26.4%' } },
                { label: 'Free Cash Flow', key: 'fcf', displayValue: '$108.8B', source: 'SEC_EDGAR', conf: 0.98, ev: { claim: 'FCF of $108.8B', value: 108807000000, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Free Cash Flow', formula: 'Op CF $118.3B - CapEx $9.4B = $108.8B' } },
                { label: 'ROE', key: 'roe', displayValue: '164.2%', source: 'SEC_EDGAR', conf: 0.95, ev: { claim: 'ROE 164.2%', value: 164.2, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Return on Equity', formula: '$93.7B / $57.1B avg equity = 164.2%' } },
                { label: 'ROIC', key: 'roic', displayValue: '54.8%', source: 'CALCULATED', conf: 0.93, ev: { claim: 'ROIC 54.8%', value: 54.8, source: 'CALCULATED' as const, filing_type: null, period: 'FY2024', metric_name: 'Return on Invested Capital', formula: 'NOPAT $102.6B / Invested Capital $187.2B = 54.8%' } },
                { label: 'Debt / EBITDA', key: 'debt_ebitda', displayValue: '0.9x', source: 'CALCULATED', conf: 0.94, ev: { claim: 'Net Debt/EBITDA 0.9x', value: 0.9, source: 'CALCULATED' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Net Debt / EBITDA', formula: '$67.8B / $134.7B = 0.9x' } },
                { label: 'Rev Growth YoY', key: 'rev_growth', displayValue: '+2.1%', source: 'SEC_EDGAR', conf: 0.97, ev: { claim: 'Revenue growth +2.1%', value: 2.1, source: 'SEC_EDGAR' as const, filing_type: '10-K', period: 'FY2024', metric_name: 'Revenue Growth YoY', formula: '($391.0B - $383.3B) / $383.3B = +2.1%' } },
              ].map(m => (
                <div
                  key={m.label}
                  onClick={() => setSelectedEvidence(m.ev)}
                  className="bg-[#0f1629] border border-[#1e2d4a] rounded-lg p-4 cursor-pointer hover:border-blue-500/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-400 uppercase tracking-wider">{m.label}</span>
                    <SourceBadge source={m.source} />
                  </div>
                  <div className="font-mono text-xl font-semibold text-white mt-1">{m.displayValue}</div>
                  <div className="flex justify-end mt-2 gap-0.5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <div key={i} className={`w-1.5 h-1.5 rounded-full ${i < Math.round(m.conf * 5) ? 'bg-blue-400' : 'bg-gray-700'}`} />
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Investment thesis */}
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
              <h3 className="text-sm font-medium text-gray-400 mb-3">Investment Thesis</h3>
              <p className="text-sm text-gray-300 leading-relaxed">{ic.analysis.investment_thesis}</p>
            </div>

            {/* Competitor table */}
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
              <h3 className="text-sm font-medium text-gray-400 mb-4">Peer Comparison</h3>
              <CompetitorTable companies={DEMO_COMPETITORS} highlightTicker="AAPL" />
            </div>
          </div>
        )}

        {activeTab === 'Financials' && (
          <div className="space-y-6">
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
              <FinancialChart
                data={DEMO_CHART_DATA}
                bars={[{ key: 'revenue', label: 'Revenue', color: '#3B82F6' }]}
                lines={[
                  { key: 'gross_margin', label: 'Gross Margin %', color: '#10B981' },
                  { key: 'net_margin', label: 'Net Margin %', color: '#F59E0B' },
                ]}
                title="Revenue & Margin Trend (FY2020–2024)"
                xKey="period"
                height={300}
              />
            </div>

            <h3 className="text-sm font-medium text-gray-400">SEC Filings</h3>
            {DEMO_FILINGS.map(f => (
              <SECFilingViewer key={f.id} filing={f} />
            ))}
          </div>
        )}

        {activeTab === 'Governance' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-medium text-white">Board Composition</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {[
                    { label: 'Board Size', value: `${DEMO_GOVERNANCE.board_size} directors` },
                    { label: 'Independent', value: `${DEMO_GOVERNANCE.independent_directors} / ${DEMO_GOVERNANCE.board_size} (89%)` },
                    { label: 'CEO/Chair Split', value: DEMO_GOVERNANCE.ceo_chairman_combined ? 'Combined' : 'Separated ✓' },
                    { label: 'Staggered Board', value: DEMO_GOVERNANCE.staggered_board ? 'Yes' : 'No ✓' },
                  ].map(row => (
                    <div key={row.label}>
                      <p className="text-xs text-gray-500">{row.label}</p>
                      <p className="text-white font-mono">{row.value}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5 space-y-4">
                <h3 className="text-sm font-medium text-white">Ownership & Rights</h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {[
                    { label: 'Insider Ownership', value: `${DEMO_GOVERNANCE.insider_ownership_pct}%` },
                    { label: 'Institutional', value: `${DEMO_GOVERNANCE.institutional_ownership_pct}%` },
                    { label: 'Dual Class', value: DEMO_GOVERNANCE.has_dual_class ? 'Yes' : 'No ✓' },
                    { label: 'Poison Pill', value: DEMO_GOVERNANCE.has_poison_pill ? 'Yes' : 'No ✓' },
                  ].map(row => (
                    <div key={row.label}>
                      <p className="text-xs text-gray-500">{row.label}</p>
                      <p className="text-white font-mono">{row.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-6 bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
              <ScoreGauge score={govScore} label="Governance Score" size={120} />
              <div>
                <p className="text-sm text-gray-300 leading-relaxed">{DEMO_REPORT.governance_analysis.analysis.analyst_summary as string}</p>
              </div>
            </div>
            <AgentStatusCard agentName="Governance Analyst" status="completed" output={DEMO_REPORT.governance_analysis as never} />
          </div>
        )}

        {activeTab === 'Valuation' && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
                <h3 className="text-sm font-medium text-white mb-4">Trading Multiples</h3>
                <div className="space-y-3">
                  {[
                    { label: 'P/E Ratio', value: '34.1x', vs: '+18% vs peers' },
                    { label: 'EV/EBITDA', value: '26.8x', vs: '+22% vs peers' },
                    { label: 'EV/Revenue', value: '8.4x', vs: null },
                    { label: 'P/FCF', value: '29.4x', vs: null },
                  ].map(m => (
                    <div key={m.label} className="flex items-center justify-between py-2 border-b border-[#1e2d4a]/50">
                      <span className="text-sm text-gray-400">{m.label}</span>
                      <div className="text-right">
                        <span className="font-mono text-white text-sm">{m.value}</span>
                        {m.vs && <span className="ml-2 text-xs text-orange-400">{m.vs}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
                <h3 className="text-sm font-medium text-white mb-4">Comps-Implied Value</h3>
                <div className="space-y-3">
                  {[
                    { label: 'Bear (low)', value: '$168', color: 'text-red-400' },
                    { label: 'Base (mid)', value: '$198', color: 'text-yellow-400' },
                    { label: 'Bull (high)', value: '$241', color: 'text-emerald-400' },
                    { label: 'Current Price', value: '$207.43', color: 'text-white' },
                  ].map(m => (
                    <div key={m.label} className="flex items-center justify-between py-2 border-b border-[#1e2d4a]/50">
                      <span className="text-sm text-gray-400">{m.label}</span>
                      <span className={`font-mono font-semibold ${m.color}`}>{m.value}</span>
                    </div>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-3">Based on median peer EV/EBITDA 21.9x and P/E 28.8x</p>
              </div>
            </div>

            <div className="bg-yellow-900/10 border border-yellow-900/40 rounded-xl p-5">
              <p className="text-sm text-yellow-400 font-medium mb-1">DCF Analysis — Assumptions Required</p>
              <p className="text-sm text-gray-400">The DCF model requires you to provide WACC and terminal growth rate. AI never generates these assumptions — they reflect your own view of risk and long-term growth. Deploy the full platform to input your own DCF assumptions.</p>
            </div>

            <AgentStatusCard agentName="Valuation Analyst" status="completed" output={DEMO_REPORT.valuation_analysis as never} />
          </div>
        )}

        {activeTab === 'Risks' && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(DEMO_REPORT.risk_analysis.analysis.risk_categories as Record<string, { severity: string; factors: string[] }>).map(([cat, data]) => (
                <div key={cat} className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-white capitalize">{cat.replace('_', ' ')}</h4>
                    <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                      data.severity === 'High' ? 'text-red-400 bg-red-900/20' :
                      data.severity === 'Moderate' ? 'text-yellow-400 bg-yellow-900/20' :
                      'text-emerald-400 bg-emerald-900/20'
                    }`}>{data.severity}</span>
                  </div>
                  <ul className="space-y-1">
                    {data.factors.map((f: string, i: number) => (
                      <li key={i} className="text-xs text-gray-400">{f}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <div className="bg-red-900/10 border border-red-900/50 rounded-xl p-5">
              <h3 className="text-sm font-medium text-red-400 mb-2">Bear Case Scenario</h3>
              <p className="text-sm text-gray-300 leading-relaxed">{DEMO_REPORT.risk_analysis.analysis.bear_case as string}</p>
            </div>

            <AgentStatusCard agentName="Risk Analyst" status="completed" output={DEMO_REPORT.risk_analysis as never} />
          </div>
        )}

        {activeTab === 'Report' && (
          <div className="space-y-4">
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-white">AAPL Full Research Report — FY2024</p>
                <p className="text-xs text-gray-500 font-mono mt-0.5">Nov 15, 2024 · 5 agents · 22,150 tokens</p>
              </div>
              <Link
                href="/company/AAPL/report/demo-report/"
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
              >
                View Full Report <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          </div>
        )}
      </div>

      <EvidencePanel evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)} />
    </div>
  )
}
