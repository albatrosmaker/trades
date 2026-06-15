'use client'
import { useState } from 'react'
import { useParams } from 'next/navigation'
import { Download, ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import { Navbar } from '@/components/layout/Navbar'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import { SourceBadge } from '@/components/ui/SourceBadge'
import { EvidencePanel } from '@/components/ui/EvidencePanel'
import { AgentStatusCard } from '@/components/ui/AgentStatusCard'
import { formatDate } from '@/lib/formatters'
import { useReport } from '@/hooks/useAnalysis'
import type { Evidence, Recommendation } from '@/lib/types'

export default function ReportPage() {
  const { ticker, reportId } = useParams<{ ticker: string; reportId: string }>()
  const { data: report, isLoading } = useReport(reportId)
  const [evidence, setEvidence] = useState<Evidence | null>(null)

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="min-h-screen flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-gray-500">
          Report not found.
        </div>
      </div>
    )
  }

  const ic = report.investment_committee
  const recommendation = ic?.analysis?.recommendation as Recommendation | undefined
  const allEvidence = [
    ...(report.financial_analysis?.evidence ?? []),
    ...(report.governance_analysis?.evidence ?? []),
    ...(report.valuation_analysis?.evidence ?? []),
    ...(report.risk_analysis?.evidence ?? []),
    ...(report.investment_committee?.evidence ?? []),
  ]

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="flex-1 flex">
        {/* Main report */}
        <div className="flex-1 overflow-y-auto pr-0 md:pr-96">
          <div className="max-w-3xl mx-auto px-6 py-8">
            {/* Back + actions */}
            <div className="flex items-center justify-between mb-8 no-print">
              <Link
                href={`/company/${ticker}`}
                className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-4 h-4" /> Back to {ticker}
              </Link>
              <div className="flex gap-2">
                <a
                  href={`/api/v1/reports/${reportId}/pdf`}
                  download
                  className="flex items-center gap-2 px-4 py-2 bg-[#0f1629] border border-[#1e2d4a] text-gray-300 hover:text-white rounded-lg text-sm transition-colors"
                >
                  <Download className="w-4 h-4" /> Export PDF
                </a>
              </div>
            </div>

            {/* Report header */}
            <div className="border-b border-[#1e2d4a] pb-8 mb-8">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">Equity Research Report</span>
                <SourceBadge source="SEC_EDGAR" />
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">{report.ticker}</h1>
              <p className="text-gray-400 text-sm font-mono">{formatDate(report.created_at)}</p>
              {recommendation && (
                <div className="mt-4">
                  <RecommendationBadge recommendation={recommendation} size="lg" />
                </div>
              )}
            </div>

            {/* Executive Summary */}
            {ic?.analysis?.executive_summary && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">
                  Executive Summary
                </h2>
                <p className="text-gray-300 leading-relaxed">
                  {ic.analysis.executive_summary as string}
                </p>
              </section>
            )}

            {/* Investment Thesis */}
            {ic?.analysis?.investment_thesis && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">
                  Investment Thesis
                </h2>
                <p className="text-gray-300 leading-relaxed">
                  {ic.analysis.investment_thesis as string}
                </p>
              </section>
            )}

            {/* Bull Case */}
            {ic?.analysis?.bull_case && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-emerald-400 mb-3 pb-2 border-b border-[#1e2d4a]">
                  Bull Case
                </h2>
                <div className="bg-emerald-900/10 border border-emerald-900/40 rounded-xl p-5">
                  <p className="text-gray-300 leading-relaxed mb-3">
                    {(ic.analysis.bull_case as Record<string, unknown>)?.scenario as string}
                  </p>
                  {Array.isArray((ic.analysis.bull_case as Record<string, unknown>)?.key_drivers) && (
                    <ul className="space-y-1">
                      {((ic.analysis.bull_case as Record<string, unknown>).key_drivers as string[]).map((d, i) => (
                        <li key={i} className="text-sm text-emerald-300 flex items-start gap-2">
                          <span className="text-emerald-500 mt-0.5">▲</span> {d}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </section>
            )}

            {/* Bear Case */}
            {ic?.analysis?.bear_case && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-red-400 mb-3 pb-2 border-b border-[#1e2d4a]">
                  Bear Case
                </h2>
                <div className="bg-red-900/10 border border-red-900/40 rounded-xl p-5">
                  <p className="text-gray-300 leading-relaxed mb-3">
                    {(ic.analysis.bear_case as Record<string, unknown>)?.scenario as string}
                  </p>
                  {Array.isArray((ic.analysis.bear_case as Record<string, unknown>)?.key_risks) && (
                    <ul className="space-y-1">
                      {((ic.analysis.bear_case as Record<string, unknown>).key_risks as string[]).map((r, i) => (
                        <li key={i} className="text-sm text-red-300 flex items-start gap-2">
                          <span className="text-red-500 mt-0.5">▼</span> {r}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </section>
            )}

            {/* Agent outputs */}
            <section className="mb-8">
              <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">
                Agent Analysis Detail
              </h2>
              <div className="space-y-3">
                {[
                  { name: 'Financial Analyst', output: report.financial_analysis },
                  { name: 'Governance Analyst', output: report.governance_analysis },
                  { name: 'Valuation Analyst', output: report.valuation_analysis },
                  { name: 'Risk Analyst', output: report.risk_analysis },
                  { name: 'Investment Committee', output: report.investment_committee },
                ].map(({ name, output }) => (
                  output && (
                    <AgentStatusCard
                      key={name}
                      agentName={name}
                      status="completed"
                      output={output}
                    />
                  )
                ))}
              </div>
            </section>

            {/* Evidence Appendix */}
            {allEvidence.length > 0 && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-white mb-3 pb-2 border-b border-[#1e2d4a]">
                  Evidence Appendix ({allEvidence.length} citations)
                </h2>
                <div className="space-y-2">
                  {allEvidence.map((ev, i) => (
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
                        <p className="text-[10px] text-gray-500 mt-1 font-mono">{ev.metric_name}</p>
                      )}
                    </button>
                  ))}
                </div>
              </section>
            )}

            <div className="border-t border-[#1e2d4a] pt-6 text-xs text-gray-600">
              <p>This report is for informational purposes only and does not constitute investment advice.</p>
              <p className="mt-1">Data sourced from SEC EDGAR (primary), FMP, and Yahoo Finance. AI-generated analysis — all metrics calculated from real data.</p>
            </div>
          </div>
        </div>

        {/* Evidence sidebar */}
        <div className="hidden md:block w-96 border-l border-[#1e2d4a] fixed right-0 top-14 h-[calc(100vh-3.5rem)] overflow-y-auto bg-[#0a0e1a]">
          {evidence ? (
            <EvidencePanel evidence={evidence} onClose={() => setEvidence(null)} />
          ) : (
            <div className="p-6 text-center text-gray-600 mt-12">
              <p className="text-sm">Click any evidence item in the appendix to inspect its source.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
