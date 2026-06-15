'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Shield, BarChart2, FileSearch, Cpu, ArrowRight } from 'lucide-react'
import { useListReports } from '@/hooks/useAnalysis'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import { formatDate } from '@/lib/formatters'
import type { Recommendation } from '@/lib/types'

const FEATURES = [
  {
    icon: Shield,
    title: 'SEC-First Data',
    desc: 'Primary source is always SEC EDGAR. Every claim cites the exact filing, section, and page.',
  },
  {
    icon: Cpu,
    title: 'Multi-Agent AI',
    desc: '5 specialized agents analyze financials, governance, valuation, risk, and investment thesis independently.',
  },
  {
    icon: FileSearch,
    title: 'Evidence Trail',
    desc: 'Every metric shows its source, formula, and raw inputs. AI analysis — no AI invention.',
  },
  {
    icon: BarChart2,
    title: 'PDF Reports',
    desc: 'Export institutional-quality research reports with full citations and evidence appendix.',
  },
]

export default function Home() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const { data: reports = [] } = useListReports()

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    const ticker = query.trim().toUpperCase()
    if (ticker) router.push(`/company/${ticker}`)
  }

  return (
    <div className="min-h-screen bg-[#0a0e1a] bg-grid">
      {/* Nav */}
      <nav className="h-14 border-b border-[#1e2d4a] flex items-center px-8">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-400" />
          <span className="font-semibold text-white tracking-tight">EquityLens</span>
          <span className="text-[10px] bg-blue-900/50 text-blue-300 border border-blue-700 px-1.5 py-0.5 rounded font-mono">
            AI
          </span>
        </div>
        <div className="ml-auto flex gap-4">
          <a href="/dashboard" className="text-sm text-gray-400 hover:text-white transition-colors">
            Dashboard
          </a>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-8 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-blue-900/30 border border-blue-800/50 rounded-full px-4 py-1.5 text-xs text-blue-300 font-mono mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          Primary-source SEC data · No AI-invented metrics
        </div>

        <h1 className="text-4xl md:text-5xl font-bold text-white leading-tight mb-6">
          Institutional-Grade{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
            Equity Research
          </span>
          <br />Powered by AI
        </h1>

        <p className="text-lg text-gray-400 max-w-2xl mx-auto mb-12">
          Every conclusion backed by primary-source data from SEC filings. Multi-agent analysis
          with full evidence trails — built for serious investors.
        </p>

        <form onSubmit={handleSearch} className="flex gap-3 max-w-xl mx-auto">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Enter ticker symbol (e.g. AAPL, MSFT, NVDA)"
              className="w-full bg-[#0f1629] border border-[#1e2d4a] rounded-xl pl-12 pr-4 py-4 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/70 font-mono text-sm"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors flex items-center gap-2"
          >
            Analyze <ArrowRight className="w-4 h-4" />
          </button>
        </form>
      </section>

      {/* Features */}
      <section className="max-w-4xl mx-auto px-8 pb-20">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
          {FEATURES.map(f => (
            <div key={f.title} className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl p-5">
              <f.icon className="w-6 h-6 text-blue-400 mb-3" />
              <h3 className="text-sm font-semibold text-white mb-1.5">{f.title}</h3>
              <p className="text-xs text-gray-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>

        {/* Recent Reports */}
        {reports.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-white mb-4">Recent Research Reports</h2>
            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl overflow-hidden">
              {reports.slice(0, 8).map((report, i) => {
                const rec = report.investment_committee?.analysis?.recommendation as Recommendation | undefined
                return (
                  <a
                    key={report.id}
                    href={`/company/${report.ticker}/report/${report.id}`}
                    className="flex items-center justify-between px-5 py-3.5 hover:bg-[#1e2d4a]/30 transition-colors border-b border-[#1e2d4a]/50 last:border-0"
                  >
                    <div className="flex items-center gap-4">
                      <span className="font-mono font-bold text-white w-16">{report.ticker}</span>
                      {rec && <RecommendationBadge recommendation={rec} size="sm" />}
                      <span className={`text-xs font-mono px-2 py-0.5 rounded ${
                        report.status === 'completed'
                          ? 'text-emerald-400 bg-emerald-900/20'
                          : report.status === 'failed'
                          ? 'text-red-400 bg-red-900/20'
                          : 'text-yellow-400 bg-yellow-900/20'
                      }`}>
                        {report.status}
                      </span>
                    </div>
                    <span className="text-xs text-gray-500 font-mono">{formatDate(report.created_at)}</span>
                  </a>
                )
              })}
            </div>
          </div>
        )}
      </section>

      <footer className="border-t border-[#1e2d4a] py-6 text-center text-xs text-gray-600">
        <p>EquityLens — For informational purposes only. Not investment advice.</p>
        <p className="mt-1">
          Data sourced from SEC EDGAR (primary), Financial Modeling Prep, Yahoo Finance.
          AI analysis only; all metrics calculated from real data.
        </p>
      </footer>
    </div>
  )
}
