import Link from 'next/link'
import { FileText, TrendingUp, Clock, Cpu } from 'lucide-react'
import { DEMO_REPORT, DEMO_WATCHLIST } from '@/lib/demo-data'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import type { Recommendation } from '@/lib/types'

export default function Dashboard() {
  const rec = DEMO_REPORT.investment_committee.analysis.recommendation as Recommendation
  const conf = DEMO_REPORT.investment_committee.confidence

  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="h-14 bg-[#0a0e1a] border-b border-[#1e2d4a] flex items-center px-6 gap-6 sticky top-0 z-40">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <Cpu className="w-5 h-5 text-blue-400" />
          <span className="font-semibold text-white tracking-tight">EquityLens</span>
          <span className="text-[10px] bg-blue-900/50 text-blue-300 border border-blue-700 px-1.5 py-0.5 rounded font-mono">AI</span>
        </Link>
        <div className="flex-1" />
        <span className="text-xs bg-yellow-900/40 text-yellow-400 border border-yellow-800 px-2 py-1 rounded font-mono">Demo Mode</span>
      </nav>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-56 shrink-0 bg-[#0a0e1a] border-r border-[#1e2d4a] flex flex-col">
          <div className="p-3 border-b border-[#1e2d4a]">
            <p className="text-xs text-gray-500 uppercase tracking-wider font-medium flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Watchlist
            </p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {DEMO_WATCHLIST.map(item => (
              <Link
                key={item.id}
                href={`/company/${item.company.ticker}/`}
                className="flex items-center justify-between px-3 py-2 hover:bg-[#0f1629] transition-colors border-b border-[#1e2d4a]/40"
              >
                <div>
                  <div className="text-sm font-mono font-bold text-white">{item.company.ticker}</div>
                  <div className="text-[10px] text-gray-500 truncate">{item.company.name}</div>
                </div>
              </Link>
            ))}
          </div>
        </aside>

        {/* Main */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h1 className="text-xl font-semibold text-white">Research Dashboard</h1>
                <p className="text-sm text-gray-500 mt-0.5">AI-powered equity research · Demo mode</p>
              </div>
              <div className="px-4 py-2 bg-[#0f1629] border border-[#1e2d4a] text-gray-500 rounded-lg text-sm cursor-not-allowed">
                + New Analysis (requires API key)
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-6">
              {[
                { icon: FileText, label: 'Total Reports', value: 1 },
                { icon: TrendingUp, label: 'Completed', value: 1 },
                { icon: Clock, label: 'Running', value: 0 },
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

            <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-[#1e2d4a]">
                <h2 className="text-sm font-medium text-white">Research Reports</h2>
              </div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#1e2d4a]">
                    {['Ticker', 'Recommendation', 'Confidence', 'Status', 'Date', ''].map(h => (
                      <th key={h} className="px-5 py-2.5 text-left text-xs text-gray-500 font-medium">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-[#1e2d4a]/50 hover:bg-[#1e2d4a]/20 transition-colors">
                    <td className="px-5 py-3">
                      <Link href="/company/AAPL/" className="font-mono font-bold text-white hover:text-blue-300 transition-colors">AAPL</Link>
                    </td>
                    <td className="px-5 py-3">
                      <RecommendationBadge recommendation={rec} size="sm" />
                    </td>
                    <td className="px-5 py-3 font-mono text-sm text-gray-300">{(conf * 100).toFixed(0)}%</td>
                    <td className="px-5 py-3">
                      <span className="text-xs font-mono px-2 py-0.5 rounded text-emerald-400 bg-emerald-900/20">completed</span>
                    </td>
                    <td className="px-5 py-3 text-xs text-gray-500 font-mono">Nov 15, 2024</td>
                    <td className="px-5 py-3">
                      <Link href="/company/AAPL/report/demo-report/" className="text-xs text-blue-400 hover:text-blue-300 transition-colors">View →</Link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
