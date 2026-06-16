'use client'
import { useState } from 'react'
import Link from 'next/link'
import { ArrowLeft } from 'lucide-react'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import { SourceBadge } from '@/components/ui/SourceBadge'
import { EvidencePanel } from '@/components/ui/EvidencePanel'
import { AgentStatusCard } from '@/components/ui/AgentStatusCard'
import { ScoreGauge } from '@/components/ui/ScoreGauge'
import { DEMO_REPORT, DEMO_EVIDENCE } from '@/lib/demo-data'
import type { Evidence, Recommendation } from '@/lib/types'

export function ReportViewer() {
  const [evidence, setEvidence] = useState<Evidence | null>(null)
  const ic = DEMO_REPORT.investment_committee
  const recommendation = ic.analysis.recommendation as Recommendation
  const bullCase = ic.analysis.bull_case as { scenario: string; key_drivers: string[]; price_target_upside_pct: number }
  const bearCase = ic.analysis.bear_case as { scenario: string; key_risks: string[]; downside_scenario_pct: number }

  return (
    <div className="min-h-screen flex flex-col bg-[#0a0e1a]">
      {/* Navbar */}
      <nav className="h-14 border-b border-[#1e2d4a] flex items-center px-6 sticky top-0 z-40 bg-[#0a0e1a]">
        <Link href="/" className="flex items-center gap-2">
          <span className="font-semibold text-white">EquityLens</span>
          <span className="text-[10px] bg-blue-900/50 text-blue-300 border border-blue-700 px-1.5 py-0.5 rounded font-mono">AI</span>
        </Link>
        <span className="text-xs bg-yellow-900/40 text-yellow-400 border border-yellow-800 px-2 py-1 rounded font-mono ml-auto">Demo Mode</span>
      </nav>

      <div className="flex flex-1">
        {/* Main report */}
        <div className="flex-1 overflow-y-auto">
          <div className="max-w-3xl mx-auto px-6 py-8">
            <div className="flex items-center justify-between mb-8">
              <Link href="/company/AAPL/" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
                <ArrowLeft className="w-4 h-4" /> Back to AAPL
              </Link>
            </div>

            {/* Report header */}
            <div className="border-b border-[#1e2d4a] pb-8 mb-8">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Equity Research Report</span>
                <SourceBadge source="SEC_EDGAR" />
              </div>
              <h1 className="text-3xl font-bold text-white mb-1">Apple Inc. (AAPL)</h1>
              <p className="text-gray-400 text-sm font-mono">November 15, 2024 · FY2024 Annual Analysis</p>
              <div className="mt-4 flex items-center gap-4">
                <RecommendationBadge recommendation={recommendation} size="lg" />
                <div className="text-sm text-gray-400">
                  Confidence: <span className="text-white font-mono">{(ic.confidence * 100).toFixed(0)}%</span>
                  {' · '}Price target: <span className="text-emerald-400 font-mono">$265</span> bull / <span className="text-red-400 font-mono">$153</span> bear
                </div>
              </div>
            </div>

            {/* Score row */}
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5 mb-8">
              <div className="flex items-center justify-around">
                <ScoreGauge score={88} label="Financial" size={90} />
                <ScoreGauge score={62} label="Growth" size={90} />
                <ScoreGauge score={96} label="Profitability" size={90} />
                <ScoreGauge score={82} label="Governance" size={90} />
                <ScoreGauge score={62} label="Safety" size={90} />
              </div>
            </div>

            {/* Executive Summary */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">Executive Summary</h2>
              <p className="text-gray-300 leading-relaxed">{ic.analysis.executive_summary as string}</p>
            </section>

            {/* Investment Thesis */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">Investment Thesis</h2>
              <p className="text-gray-300 leading-relaxed">{ic.analysis.investment_thesis as string}</p>
            </section>

            {/* Bull Case */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-emerald-400 mb-3 pb-2 border-b border-[#1e2d4a]">
                Bull Case (+{bullCase.price_target_upside_pct}% to $265)
              </h2>
              <div className="bg-emerald-900/10 border border-emerald-900/40 rounded-xl p-5">
                <p className="text-gray-300 leading-relaxed mb-3">{bullCase.scenario}</p>
                <ul className="space-y-1">
                  {bullCase.key_drivers.map((d, i) => (
                    <li key={i} className="text-sm text-emerald-300 flex items-start gap-2">
                      <span className="text-emerald-500 mt-0.5">▲</span> {d}
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            {/* Bear Case */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-red-400 mb-3 pb-2 border-b border-[#1e2d4a]">
                Bear Case ({bearCase.downside_scenario_pct}% to $153)
              </h2>
              <div className="bg-red-900/10 border border-red-900/40 rounded-xl p-5">
                <p className="text-gray-300 leading-relaxed mb-3">{bearCase.scenario}</p>
                <ul className="space-y-1">
                  {bearCase.key_risks.map((r, i) => (
                    <li key={i} className="text-sm text-red-300 flex items-start gap-2">
                      <span className="text-red-500 mt-0.5">▼</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            {/* Key metrics to watch */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">What Would Change Our View</h2>
              {(ic.analysis.what_would_change_view as string[]).map((item, i) => (
                <div key={i} className="bg-[#0f1629] border border-[#1e2d4a] rounded-lg p-3 mb-2 text-sm text-gray-300">{item}</div>
              ))}
            </section>

            {/* Agent Analysis */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">Agent Analysis Detail</h2>
              <div className="space-y-3">
                {[
                  { name: 'Financial Statement Analyst', output: DEMO_REPORT.financial_analysis },
                  { name: 'Governance Analyst', output: DEMO_REPORT.governance_analysis },
                  { name: 'Valuation Analyst', output: DEMO_REPORT.valuation_analysis },
                  { name: 'Risk Analyst', output: DEMO_REPORT.risk_analysis },
                  { name: 'Investment Committee', output: DEMO_REPORT.investment_committee },
                ].map(({ name, output }) => (
                  <AgentStatusCard key={name} agentName={name} status="completed" output={output as never} />
                ))}
              </div>
            </section>

            {/* Evidence Appendix */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">
                Evidence Appendix ({DEMO_EVIDENCE.length} citations)
              </h2>
              <p className="text-xs text-gray-500 mb-3">Click any item to inspect its source, formula, and raw inputs.</p>
              <div className="space-y-2">
                {DEMO_EVIDENCE.map((ev, i) => (
                  <button
                    key={i}
                    onClick={() => setEvidence(ev)}
                    className="w-full text-left bg-[#0f1629] border border-[#1e2d4a] rounded-lg p-3 hover:border-blue-500/40 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-xs text-gray-300 flex-1">{ev.claim}</p>
                      <SourceBadge source={ev.source} />
                    </div>
                    {ev.metric_name && (
                      <p className="text-[10px] text-gray-500 mt-1 font-mono">{ev.metric_name} · {ev.period}</p>
                    )}
                  </button>
                ))}
              </div>
            </section>

            <div className="border-t border-[#1e2d4a] pt-6 text-xs text-gray-600">
              <p>This report is for informational purposes only. Not investment advice.</p>
              <p className="mt-1">All financial metrics calculated from SEC EDGAR primary-source data. AI analysis only — no AI-invented numbers.</p>
            </div>
          </div>
        </div>

        {/* Evidence sidebar */}
        <div className="hidden md:block w-80 border-l border-[#1e2d4a] sticky top-14 h-[calc(100vh-3.5rem)] overflow-hidden">
          {evidence ? (
            <EvidencePanel evidence={evidence} onClose={() => setEvidence(null)} />
          ) : (
            <div className="p-6 text-center text-gray-600 mt-12">
              <p className="text-sm">Click any evidence item in the appendix to inspect its source and formula.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
