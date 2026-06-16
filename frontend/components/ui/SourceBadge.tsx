'use client'
import { cn } from '@/lib/utils'
import type { DataSource } from '@/lib/types'

const SOURCE_CONFIG: Record<string, { label: string; className: string }> = {
  SEC_EDGAR: {
    label: 'SEC',
    className: 'bg-blue-900/50 text-blue-300 border-blue-700',
  },
  FMP: {
    label: 'FMP',
    className: 'bg-purple-900/50 text-purple-300 border-purple-700',
  },
  YAHOO: {
    label: 'YF',
    className: 'bg-orange-900/50 text-orange-300 border-orange-700',
  },
  CALCULATED: {
    label: 'CALC',
    className: 'bg-teal-900/50 text-teal-300 border-teal-700',
  },
}

interface SourceBadgeProps {
  source: DataSource | string
  className?: string
}

export function SourceBadge({ source, className }: SourceBadgeProps) {
  const config = SOURCE_CONFIG[source] ?? {
    label: source,
    className: 'bg-gray-800 text-gray-400 border-gray-700',
  }
  return (
    <span
      className={cn(
        'inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-medium border',
        config.className,
        className
      )}
    >
      {config.label}
    </span>
  )
}
