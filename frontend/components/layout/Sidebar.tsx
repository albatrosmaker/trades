'use client'
import { useState } from 'react'
import Link from 'next/link'
import { Plus, X, TrendingUp } from 'lucide-react'
import { useWatchlist, useAddToWatchlist, useRemoveFromWatchlist } from '@/hooks/useAnalysis'

export function Sidebar() {
  const [addInput, setAddInput] = useState('')
  const { data: watchlist = [] } = useWatchlist()
  const addMutation = useAddToWatchlist()
  const removeMutation = useRemoveFromWatchlist()

  function handleAdd(e: React.FormEvent) {
    e.preventDefault()
    const ticker = addInput.trim().toUpperCase()
    if (ticker) {
      addMutation.mutate(ticker)
      setAddInput('')
    }
  }

  return (
    <aside className="w-56 shrink-0 bg-[#0a0e1a] border-r border-[#1e2d4a] flex flex-col h-full">
      <div className="p-3 border-b border-[#1e2d4a]">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-medium flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          Watchlist
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        {watchlist.length === 0 ? (
          <p className="text-xs text-gray-600 p-3">No tickers tracked yet.</p>
        ) : (
          watchlist.map(item => (
            <div
              key={item.id}
              className="flex items-center justify-between px-3 py-2 hover:bg-[#0f1629] group transition-colors border-b border-[#1e2d4a]/40"
            >
              <Link
                href={`/company/${item.company.ticker}`}
                className="flex-1 min-w-0"
              >
                <div className="text-sm font-mono font-bold text-white">
                  {item.company.ticker}
                </div>
                <div className="text-[10px] text-gray-500 truncate">
                  {item.company.name}
                </div>
              </Link>
              <button
                onClick={() => removeMutation.mutate(item.company.ticker)}
                className="opacity-0 group-hover:opacity-100 p-1 text-gray-600 hover:text-red-400 transition-all"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleAdd} className="p-3 border-t border-[#1e2d4a]">
        <div className="flex gap-2">
          <input
            value={addInput}
            onChange={e => setAddInput(e.target.value)}
            placeholder="Add ticker..."
            className="flex-1 bg-[#0f1629] border border-[#1e2d4a] rounded px-2 py-1 text-xs font-mono text-white placeholder-gray-700 focus:outline-none focus:border-blue-500/60 uppercase"
          />
          <button
            type="submit"
            disabled={addMutation.isPending}
            className="p-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors disabled:opacity-50"
          >
            <Plus className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>
    </aside>
  )
}
