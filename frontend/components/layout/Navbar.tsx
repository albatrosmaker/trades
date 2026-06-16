'use client'
import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, Bell, BookMarked, Cpu } from 'lucide-react'
import { searchCompanies } from '@/lib/api'
import type { Company } from '@/lib/types'

export function Navbar() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Company[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const timeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return }
    setLoading(true)
    if (timeout.current) clearTimeout(timeout.current)
    timeout.current = setTimeout(async () => {
      try {
        const res = await searchCompanies(query)
        setResults(res.slice(0, 8))
        setOpen(true)
      } catch {
        setResults([])
      } finally {
        setLoading(false)
      }
    }, 300)
  }, [query])

  function selectCompany(ticker: string) {
    setQuery('')
    setOpen(false)
    router.push(`/company/${ticker}`)
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const q = query.trim().toUpperCase()
    if (q) selectCompany(q)
  }

  return (
    <nav className="h-14 bg-[#0a0e1a] border-b border-[#1e2d4a] flex items-center px-6 gap-6 sticky top-0 z-40">
      <a href="/" className="flex items-center gap-2 shrink-0">
        <Cpu className="w-5 h-5 text-blue-400" />
        <span className="font-semibold text-white tracking-tight">EquityLens</span>
        <span className="text-[10px] bg-blue-900/50 text-blue-300 border border-blue-700 px-1.5 py-0.5 rounded font-mono">
          AI
        </span>
      </a>

      <form onSubmit={handleSubmit} className="flex-1 max-w-xl relative">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onBlur={() => setTimeout(() => setOpen(false), 150)}
            placeholder="Search ticker or company name..."
            className="w-full bg-[#0f1629] border border-[#1e2d4a] rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-blue-500/60 font-mono"
          />
          {loading && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 w-3 h-3 border border-blue-400 border-t-transparent rounded-full animate-spin" />
          )}
        </div>

        {open && results.length > 0 && (
          <div className="absolute top-full mt-1 w-full bg-[#0f1629] border border-[#1e2d4a] rounded-lg shadow-xl overflow-hidden z-50">
            {results.map(co => (
              <button
                key={co.ticker}
                onMouseDown={() => selectCompany(co.ticker)}
                className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-[#1e2d4a] transition-colors text-left"
              >
                <div>
                  <span className="text-sm font-mono font-bold text-white">{co.ticker}</span>
                  <span className="text-xs text-gray-400 ml-3">{co.name}</span>
                </div>
                {co.sector && (
                  <span className="text-[10px] text-gray-500">{co.sector}</span>
                )}
              </button>
            ))}
          </div>
        )}
      </form>

      <div className="flex items-center gap-3 ml-auto">
        <a href="/dashboard" className="text-sm text-gray-400 hover:text-white transition-colors">
          Dashboard
        </a>
        <button className="p-2 text-gray-400 hover:text-white transition-colors">
          <BookMarked className="w-4 h-4" />
        </button>
      </div>
    </nav>
  )
}
