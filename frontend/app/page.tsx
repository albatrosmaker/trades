import Link from 'next/link'
import { Search, Shield, BarChart2, FileSearch, Cpu, ArrowRight } from 'lucide-react'
import { DEMO_REPORT } from '@/lib/demo-data'
import { RecommendationBadge } from '@/components/ui/RecommendationBadge'
import type { Recommendation } from '@/lib/types'

const FEATURES = [
  { icon: Shield, title: 'SEC-First Data', desc: 'Primary source is always SEC EDGAR. Every claim cites the exact filing, section, and page.' },
  { icon: Cpu, title: 'Multi-Agent AI', desc: '5 specialized agents analyze financials, governance, valuation, risk, and investment thesis in parallel.' },
  { icon: FileSearch, title: 'Evidence Trail', desc: 'Every metric shows its source, formula, and raw inputs. AI analyzes — AI never invents.' },
  { icon: BarChart2, title: 'PDF Reports', desc: 'Export institutional-quality research reports with full citations and evidence appendix.' },
]

export default function Home() {
  const rec = DEMO_REPORT.investment_committee.analysis.recommendation as Recommendation

  return (
    <div className="min-h-screen bg-[#0a0e1a] bg-grid">
      <nav className="h-14 border-b border-[#1e2d4a] flex items-center px-8">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-blue-400" />
          <span className="font-semibold text-white tracking-tight">EquityLens</span>
          <span className="text-[10px] bg-blue-900/50 text-blue-300 border border-blue-700 px-1.5 py-0.5 rounded font-mono">AI</span>
        </div>
        <div className="ml-auto flex gap-4 items-center">
          <Link href="/dashboard/" className="text-sm text-gray-400 hover:text-white transition-colors">Dashboard</Link>
          <span className="text-xs bg-yellow-900/40 text-yellow-400 border border-yellow-800 px-2 py-1 rounded font-mono">Demo Mode</span>
        </div>
      </nav>

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

        <div className="flex gap-3 max-w-xl mx-auto">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <div className="w-full bg-[#0f1629] border border-[#1e2d4a] rounded-xl pl-12 pr-4 py-4 text-gray-600 font-mono text-sm cursor-not-allowed">
              Demo: AAPL loaded below
            </div>
          </div>
          <Link
            href="/company/AAPL/"
            className="px-6 py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors flex items-center gap-2 whitespace-nowrap"
          >
            View Demo <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

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

        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Demo Research Report</h2>
          <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-xl overflow-hidden">
            <Link
              href="/company/AAPL/report/demo-report/"
              className="flex items-center justify-between px-5 py-4 hover:bg-[#1e2d4a]/30 transition-colors"
            >
              <div className="flex items-center gap-4">
                <span className="font-mono font-bold text-white w-16">AAPL</span>
                <RecommendationBadge recommendation={rec} size="sm" />
                <span className="text-xs font-mono px-2 py-0.5 rounded text-emerald-400 bg-emerald-900/20">completed</span>
                <span className="text-xs text-gray-500">Apple Inc. · FY2024 Full Analysis</span>
              </div>
              <span className="text-xs text-blue-400">View Report →</span>
            </Link>
          </div>
        </div>

        <div className="mt-8 bg-yellow-900/10 border border-yellow-900/40 rounded-xl p-5">
          <p className="text-xs text-yellow-400 font-medium mb-1">Demo Mode</p>
          <p className="text-xs text-gray-400">
            This is a static demo showing realistic Apple Inc. FY2024 data from SEC EDGAR.
            For live analysis of any company, deploy with an Anthropic API key — see the{' '}
            <a href="https://github.com/albatrosmaker/trades" className="text-blue-400 hover:underline" target="_blank" rel="noopener noreferrer">
              GitHub repo
            </a>.
          </p>
        </div>
      </section>

      <footer className="border-t border-[#1e2d4a] py-6 text-center text-xs text-gray-600">
        <p>EquityLens — For informational purposes only. Not investment advice.</p>
        <p className="mt-1">Data sourced from SEC EDGAR (primary), Financial Modeling Prep, Yahoo Finance.</p>
      </footer>
    </div>
  )
}
