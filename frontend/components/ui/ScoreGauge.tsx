'use client'
import { getScoreGrade, getScoreBgColor } from '@/lib/formatters'

interface ScoreGaugeProps {
  score: number
  label?: string
  size?: number
}

export function ScoreGauge({ score, label, size = 120 }: ScoreGaugeProps) {
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const clampedScore = Math.max(0, Math.min(100, score))
  const offset = circumference - (clampedScore / 100) * circumference
  const color = getScoreBgColor(clampedScore)
  const grade = getScoreGrade(clampedScore)
  const cx = size / 2
  const cy = size / 2

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="#1e2d4a"
          strokeWidth={8}
        />
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={8}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div
        className="flex flex-col items-center"
        style={{ marginTop: -(size * 0.75) }}
      >
        <span
          className="font-mono font-bold"
          style={{ fontSize: size * 0.22, color }}
        >
          {clampedScore.toFixed(0)}
        </span>
        <span className="text-gray-400 text-xs font-mono">{grade}</span>
      </div>
      <div style={{ marginTop: size * 0.35 }} />
      {label && (
        <span className="text-xs text-gray-400 text-center">{label}</span>
      )}
    </div>
  )
}
