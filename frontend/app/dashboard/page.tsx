'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { PlayCircle, FileText, Clock, TrendingUp } from 'lucide-react'
import { Navbar } from '@/components/layout/Navbar'
import { Sidebar } from '@/components/layout/Sidebar'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import { useListReports, useTriggerAnalysis, useJobPolling } from '@/hooks/useAnalysis'
import { formatDate } from '@/lib/formatters'
import type { Recommendation } from '@/lib/types'

function AnalyzeModal({ onClose }: { onClose: () => void }) {
  const router = useRouter()
  const [ticker, setTicker] = useState('')
  const [showDCF, setShowDCF] = useState(false)
  const [wacc, setWacc] = useState('10')
  const [tgr, setTgr] = useState('3')
  const [years, setYears] = useState('5')
  const [jobId, setJobId] = useState<string | null>(null)

  const triggerMutation = useTriggerAnalysis()
  const jobQuery = useJobPolling(jobId)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const t = ticker.trim().toUpperCase()
    if (!t) return
    const dcf = showDCF ? { wacc: parseFloat(wacc) / 100, terminal_growth_rate: parseFloat(tgr) / 100, projection_years: parseInt(years) } : undefined
    const result = await triggerMutation.mutateAsync({ ticker: t, dcfAssumptions: dcf })
    setJobId(result.job_id)
  }

  if (jobQuery.data?.status === 'completed') {
    const reportId = jobQuery.data.result?.report_id as string | undefined
    if (reportId) router.push(`/company/${ticker.toUpperCase()}/report/${reportId}`)
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl w-full max-w-md p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Run New Analysis</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 uppercase tracking-wider">Ticker Symbol</label>
            <input
              value={ticker}
              onChange={e => setTicker(e.target.value.toUpperCase())}
              placeholder="e.g. AAPL"
              className="mt-1 w-full bg-[#0a0e1a] border border-[#1e2d4a] rounded-lg px-3 py-2.5 text-white font-mono focus:outline-none focus:border-blue-500/60 uppercase"
            />
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" checked={showDCF} onChange={e => setShowDCF(e.target.checked)} className="accent-blue-500" />
            <span className="text-sm text-gray-300">Include DCF Analysis (requires assumptions)</span>
          </label>

          {showDCF && (
            <div className="grid grid-cols-3 gap-3 bg-[#0a0e1a] border border-[#1e2d4a] rounded-lg p-3">
              <div>
                <label className="text-xs text-gray-500">WACC (%)</label>
                <input value={wacc} onChange={e => setWacc(e.target.value)} type="number" step="0.1" className="mt-1 w-full bg-transparent border-b border-[#1e2d4a] pb-1 text-white font-mono text-sm focus:outline-none focus:border-blue-400" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Terminal Growth (%)</label>
                <input value={tgr} onChange={e => setTgr(e.target.value)} type="number" step="0.1" className="mt-1 w-full bg-transparent border-b border-[#1e2d4a] pb-1 text-white font-mono text-sm focus:outline-none focus:border-blue-400" />
              </div>
              <div>
                <label className="text-xs text-gray-500">Years</label>
                <input value={years} onChange={e => setYears(e.target.value)} type="number" min="3" max="10" className="mt-1 w-full bg-transparent border-b border-[#1e2d4a] pb-1 text-white font-mono text-sm focus:outline-none focus:border-blue-400" />
              </div>
              <p className="col-span-3 text-xs text-yellow-600/80 mt-1">
                DCF assumptions are your inputs — AI never invents them.
              </p>
            </div>
          )}

          {jobId && (
            <div className="flex items-center gap-2 text-sm text-blue-300">
              <div className="w-3 h-3 border border-blue-400 border-t-transparent rounded-full animate-spin" />
              {jobQuery.data?.status === 'running' ? 'Agents analyzing...' : 'Queued...'}
            </div>
          )}

          <div className="flex gap-3">
            <button type="button" onClick={onClose} className="flex-1 py-2.5 border border-[#1e2d4a] text-gray-400 rounded-lg text-sm hover:border-gray-500 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={triggerMutation.isPending || !!jobId} className="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-60 flex items-center justify-center gap-2">
              <PlayCircle className="w-4 h-4" />
              Analyze
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [showModal, setShowModal] = useState(false)
  const { data: reports = [], isLoading } = useListReports()

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-xl font-semibold text-white">Research Dashboard</h1>
                <p className="text-sm text-gray-500 mt-0.5">AI-powered equity research with primary-source data</p>
              </div>
              <button onClick={() => setShowModal(true)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors">
                <PlayCircle className="w-4 h-4" />
                New Analysis
              </button>
            </div>

            {/* Stats strip */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              {[
                { icon: FileText, label: 'Total Reports', value: reports.length },
                { icon: TrendingUp, label: 'Completed', value: reports.filter(r => r.status === 'completed').length },
                { icon: Clock, label: 'Running', value: reports.filter(r => r.status === 'running').length },
              ].map(stat => (
                <div key={stat.label} className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-4 flex items-center gap-4">
                  <stat.icon className="w-8 h-8 text-blue-400/50" />
                  <div>
                    <p className="text-2xl font-bold font-mono text-white">{stat.value}</p>
                    <p className="text-xs text-gray-500">{stat.label}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Reports table */}
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-[#1e2d4a]">
                <h2 className="text-sm font-medium text-white">Research Reports</h2>
              </div>
              {isLoading ? (
                <div className="flex items-center justify-center py-12 text-gray-500 text-sm">Loading...</div>
              ) : reports.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                  <FileText className="w-12 h-12 mb-3 opacity-20" />
                  <p className="text-sm">No reports yet. Run your first analysis.</p>
                </div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#1e2d4a]">
                      {['Ticker', 'Recommendation', 'Confidence', 'Status', 'Date', ''].map(h => (
                        <th key={h} className="px-5 py-2.5 text-left text-xs text-gray-500 font-medium">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {reports.map(report => {
                      const ic = report.investment_committee?.analysis
                      const rec = ic?.recommendation as Recommendation | undefined
                      const conf = report.investment_committee?.confidence
                      return (
                        <tr key={report.id} className="border-b border-[#1e2d4a]/50 hover:bg-[#1e2d4a]/20 transition-colors">
                          <td className="px-5 py-3">
                            <a href={`/company/${report.ticker}`} className="font-mono font-bold text-white hover:text-blue-300 transition-colors">
                              {report.ticker}
                            </a>
                          </td>
                          <td className="px-5 py-3">
                            {rec ? <RecommendationBadge recommendation={rec} size="sm" /> : <span className="text-gray-600 text-xs">—</span>}
                          </td>
                          <td className="px-5 py-3 font-mono text-sm text-gray-300">
                            {conf !== undefined ? `${(conf * 100).toFixed(0)}%` : '—'}
                          </td>
                          <td className="px-5 py-3">
                            <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                              report.status === 'completed' ? 'text-emerald-400 bg-emerald-900/20' :
                              report.status === 'failed' ? 'text-red-400 bg-red-900/20' :
                              report.status === 'running' ? 'text-yellow-400 bg-yellow-900/20 animate-pulse' :
                              'text-gray-400 bg-gray-900/20'
                            }`}>
                              {report.status}
                            </span>
                          </td>
                          <td className="px-5 py-3 text-xs text-gray-500 font-mono">{formatDate(report.created_at)}</td>
                          <td className="px-5 py-3">
                            {report.status === 'completed' && (
                              <a href={`/company/${report.ticker}/report/${report.id}`} className="text-xs text-blue-400 hover:text-blue-300 transition-colors">
                                View →
                              </a>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </main>
      </div>
      {showModal && <AnalyzeModal onClose={() => setShowModal(false)} />}
    </div>
  )
}
