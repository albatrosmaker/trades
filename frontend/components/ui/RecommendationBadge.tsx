'use client'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Recommendation } from '@/lib/types'

const CONFIG: Record<
  Recommendation,
  { bg: string; text: string; border: string; Icon: React.ElementType }
> = {
  'Strong Buy': {
    bg: 'bg-emerald-900/40',
    text: 'text-emerald-300',
    border: 'border-emerald-600',
    Icon: TrendingUp,
  },
  Buy: {
    bg: 'bg-emerald-900/20',
    text: 'text-emerald-400',
    border: 'border-emerald-700',
    Icon: TrendingUp,
  },
  Hold: {
    bg: 'bg-yellow-900/20',
    text: 'text-yellow-400',
    border: 'border-yellow-700',
    Icon: Minus,
  },
  Sell: {
    bg: 'bg-orange-900/20',
    text: 'text-orange-400',
    border: 'border-orange-700',
    Icon: TrendingDown,
  },
  'Strong Sell': {
    bg: 'bg-red-900/30',
    text: 'text-red-400',
    border: 'border-red-700',
    Icon: TrendingDown,
  },
}

interface RecommendationBadgeProps {
  recommendation: Recommendation
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function RecommendationBadge({
  recommendation,
  size = 'md',
  className,
}: RecommendationBadgeProps) {
  const config = CONFIG[recommendation]
  const { Icon } = config

  const sizeClasses = {
    sm: 'text-xs px-2 py-1 gap-1',
    md: 'text-sm px-3 py-1.5 gap-1.5',
    lg: 'text-base px-4 py-2 gap-2 font-semibold',
  }

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border font-mono font-medium',
        config.bg,
        config.text,
        config.border,
        sizeClasses[size],
        className
      )}
    >
      <Icon className={size === 'lg' ? 'w-5 h-5' : 'w-3.5 h-3.5'} />
      {recommendation}
    </span>
  )
}
