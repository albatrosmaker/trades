'use client'
import { useState } from 'react'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatPercent, formatMultiple } from '@/lib/formatters'

interface CompanyMetrics {
  ticker: string
  name?: string
  revenue_growth?: number | null
  gross_margin?: number | null
  net_margin?: number | null
  roe?: number | null
  roic?: number | null
  debt_ebitda?: number | null
  pe_ratio?: number | null
  ev_ebitda?: number | null
  governance_score?: number | null
}

interface CompetitorTableProps {
  companies: CompanyMetrics[]
  highlightTicker?: string
}

type SortKey = keyof Omit<CompanyMetrics, 'ticker' | 'name'>
type SortDir = 'asc' | 'desc'

const COLUMNS: { key: SortKey; label: string; format: (v: number | null) => string; higherBetter: boolean }[] = [
  { key: 'revenue_growth', label: 'Rev Growth', format: (v) => formatPercent(v), higherBetter: true },
  { key: 'gross_margin', label: 'Gross Margin', format: (v) => formatPercent(v), higherBetter: true },
  { key: 'net_margin', label: 'Net Margin', format: (v) => formatPercent(v), higherBetter: true },
  { key: 'roe', label: 'ROE', format: (v) => formatPercent(v), higherBetter: true },
  { key: 'roic', label: 'ROIC', format: (v) => formatPercent(v), higherBetter: true },
  { key: 'debt_ebitda', label: 'Debt/EBITDA', format: (v) => formatMultiple(v), higherBetter: false },
  { key: 'pe_ratio', label: 'P/E', format: (v) => formatMultiple(v), higherBetter: false },
  { key: 'ev_ebitda', label: 'EV/EBITDA', format: (v) => formatMultiple(v), higherBetter: false },
  { key: 'governance_score', label: 'Gov Score', format: (v) => v !== null ? v!.toFixed(0) : 'N/A', higherBetter: true },
]

function getRankBadge(rank: number) {
  if (rank === 1) return <span className="text-yellow-400 font-bold text-xs">#1</span>
  if (rank === 2) return <span className="text-gray-300 text-xs">#2</span>
  if (rank === 3) return <span className="text-orange-400 text-xs">#3</span>
  return null
}

function getCellBg(rank: number, total: number) {
  const pct = rank / total
  if (pct <= 0.25) return 'bg-emerald-900/30'
  if (pct >= 0.75) return 'bg-red-900/20'
  return ''
}

export function CompetitorTable({ companies, highlightTicker }: CompetitorTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('revenue_growth')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }

  const sorted = [...companies].sort((a, b) => {
    const av = a[sortKey] ?? -Infinity
    const bv = b[sortKey] ?? -Infinity
    return sortDir === 'desc' ? (bv as number) - (av as number) : (av as number) - (bv as number)
  })

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-[#1e2d4a]">
            <th className="text-left py-2 px-3 text-gray-400 font-medium">Ticker</th>
            {COLUMNS.map(col => (
              <th
                key={col.key}
                className="text-right py-2 px-3 text-gray-400 font-medium cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort(col.key)}
              >
                <div className="flex items-center justify-end gap-1">
                  {col.label}
                  {sortKey === col.key && (
                    sortDir === 'desc'
                      ? <ChevronDown className="w-3 h-3 text-blue-400" />
                      : <ChevronUp className="w-3 h-3 text-blue-400" />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((co, rowIdx) => (
            <tr
              key={co.ticker}
              className={cn(
                'border-b border-[#1e2d4a]/50 transition-colors',
                co.ticker === highlightTicker
                  ? 'bg-blue-900/20 border-blue-800/50'
                  : 'hover:bg-[#1e2d4a]/30'
              )}
            >
              <td className="py-2 px-3">
                <div className="flex items-center gap-2">
                  <span className={cn('font-bold', co.ticker === highlightTicker ? 'text-blue-300' : 'text-white')}>
                    {co.ticker}
                  </span>
                  {sortKey && getRankBadge(rowIdx + 1)}
                </div>
                {co.name && <div className="text-gray-500 text-[10px]">{co.name}</div>}
              </td>
              {COLUMNS.map((col, colIdx) => {
                const val = co[col.key]
                const rank = sorted.findIndex(c => c.ticker === co.ticker) + 1
                return (
                  <td
                    key={col.key}
                    className={cn(
                      'text-right py-2 px-3',
                      val !== null && val !== undefined
                        ? getCellBg(rank, companies.length)
                        : '',
                      sortKey === col.key ? 'text-white' : 'text-gray-300'
                    )}
                  >
                    {val !== null && val !== undefined ? col.format(val as number) : <span className="text-gray-600">—</span>}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
