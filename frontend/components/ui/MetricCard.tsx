'use client'
import { cn } from '@/lib/utils'
import { getChangeColor, formatCurrency, formatPercent, formatMultiple } from '@/lib/formatters'
import { SourceBadge } from './SourceBadge'
import type { DataSource } from '@/lib/types'

function renderValue(
  value: number | string | null | undefined,
  format: 'currency' | 'percent' | 'multiple' | 'number'
): string {
  if (value === null || value === undefined) return 'N/A'
  if (typeof value === 'string') return value
  switch (format) {
    case 'currency':
      return formatCurrency(value)
    case 'percent':
      return formatPercent(value)
    case 'multiple':
      return formatMultiple(value)
    default:
      return value.toLocaleString()
  }
}

interface MetricCardProps {
  label: string
  value: number | string | null | undefined
  change?: number | null
  changeLabel?: string
  source: DataSource | string
  confidence?: number
  format?: 'currency' | 'percent' | 'multiple' | 'number'
  onClick?: () => void
  className?: string
}

export function MetricCard({
  label,
  value,
  change,
  changeLabel,
  source,
  confidence = 1,
  format = 'number',
  onClick,
  className,
}: MetricCardProps) {
  const confidenceDots = Math.round(confidence * 5)

  return (
    <div
      className={cn(
        'bg-[#0f1629] border border-[#1e2d4a] rounded-lg p-4 transition-colors',
        onClick && 'cursor-pointer hover:border-blue-500/50',
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
        <SourceBadge source={source} />
      </div>
      <div className="font-mono text-xl font-semibold text-white mt-1">
        {renderValue(value, format)}
      </div>
      <div className="flex items-center justify-between mt-2">
        {change !== null && change !== undefined ? (
          <span className={cn('text-xs font-mono', getChangeColor(change))}>
            {change >= 0 ? '▲' : '▼'} {Math.abs(change).toFixed(1)}%
            {changeLabel && <span className="text-gray-500 ml-1">{changeLabel}</span>}
          </span>
        ) : (
          <span />
        )}
        <div className="flex gap-0.5">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className={cn(
                'w-1.5 h-1.5 rounded-full',
                i < confidenceDots ? 'bg-blue-400' : 'bg-gray-700'
              )}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
