'use client'
import { ExternalLink, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'
import { formatDate } from '@/lib/formatters'
import type { SECFiling } from '@/lib/types'

const FORM_COLORS: Record<string, string> = {
  '10-K': 'bg-blue-900/40 text-blue-300 border-blue-700',
  '10-Q': 'bg-purple-900/40 text-purple-300 border-purple-700',
  '8-K': 'bg-yellow-900/40 text-yellow-300 border-yellow-700',
  'DEF 14A': 'bg-green-900/40 text-green-300 border-green-700',
  'SC 13G': 'bg-gray-800 text-gray-400 border-gray-700',
}

interface SECFilingViewerProps {
  filing: SECFiling
  excerpt?: string
  className?: string
}

export function SECFilingViewer({ filing, excerpt, className }: SECFilingViewerProps) {
  const colorClass = FORM_COLORS[filing.form_type] ?? 'bg-gray-800 text-gray-400 border-gray-700'

  return (
    <div
      className={cn(
        'bg-[#0f1629] border border-[#1e2d4a] rounded-lg p-4 space-y-2',
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-gray-400" />
          <span
            className={cn(
              'text-xs font-mono font-medium px-2 py-0.5 rounded border',
              colorClass
            )}
          >
            {filing.form_type}
          </span>
        </div>
        <a
          href={filing.filing_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          View on EDGAR <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      <div className="flex items-center gap-4 text-xs text-gray-400 font-mono">
        <span>Filed: {formatDate(filing.filed_at)}</span>
        {filing.period_of_report && (
          <span>Period: {filing.period_of_report}</span>
        )}
        {filing.is_processed && (
          <span className="text-emerald-400">✓ Processed</span>
        )}
      </div>

      {excerpt && (
        <p className="text-xs text-gray-400 line-clamp-3 border-t border-[#1e2d4a] pt-2 mt-2">
          {excerpt}
        </p>
      )}
    </div>
  )
}
