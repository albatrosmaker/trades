'use client'
import { useState } from 'react'
import { ChevronDown, ChevronRight, Loader2, CheckCircle2, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentOutput } from '@/lib/types'

interface AgentStatusCardProps {
  agentName: string
  status: 'running' | 'completed' | 'error' | 'pending'
  output?: AgentOutput | null
}

const STATUS_CONFIG = {
  pending: { color: 'text-gray-500', Icon: null, label: 'Pending' },
  running: { color: 'text-yellow-400', Icon: Loader2, label: 'Analyzing...' },
  completed: { color: 'text-emerald-400', Icon: CheckCircle2, label: 'Complete' },
  error: { color: 'text-red-400', Icon: XCircle, label: 'Failed' },
}

export function AgentStatusCard({ agentName, status, output }: AgentStatusCardProps) {
  const [expanded, setExpanded] = useState(false)
  const config = STATUS_CONFIG[status]
  const { Icon } = config

  return (
    <div className="bg-[#0f1629] border border-[#1e2d4a] rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between p-3 hover:bg-[#1e2d4a]/30 transition-colors"
        onClick={() => output && setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className={cn('w-2 h-2 rounded-full', {
            'bg-gray-500': status === 'pending',
            'bg-yellow-400 animate-pulse': status === 'running',
            'bg-emerald-400': status === 'completed',
            'bg-red-400': status === 'error',
          })} />
          <span className="text-sm font-medium text-white">{agentName}</span>
          {output && (
            <span className="text-xs text-gray-500 font-mono">
              {(output.confidence * 100).toFixed(0)}% confidence
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {Icon && (
            <Icon
              className={cn('w-4 h-4', config.color, status === 'running' && 'animate-spin')}
            />
          )}
          <span className={cn('text-xs', config.color)}>{config.label}</span>
          {output && (
            expanded ? <ChevronDown className="w-4 h-4 text-gray-500" /> : <ChevronRight className="w-4 h-4 text-gray-500" />
          )}
        </div>
      </button>

      {expanded && output && (
        <div className="border-t border-[#1e2d4a] p-3 space-y-3">
          {output.data_quality_warnings.length > 0 && (
            <div className="bg-yellow-900/20 border border-yellow-800/50 rounded p-2">
              <p className="text-xs text-yellow-400 font-medium mb-1">Data Warnings</p>
              {output.data_quality_warnings.map((w, i) => (
                <p key={i} className="text-xs text-yellow-300/80">{w}</p>
              ))}
            </div>
          )}

          {output.missing_data.length > 0 && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Missing Data</p>
              <div className="flex flex-wrap gap-1">
                {output.missing_data.map((m, i) => (
                  <span key={i} className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded font-mono">
                    {m}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="text-xs text-gray-500 mb-1">Evidence Items: {output.evidence.length}</p>
            <p className="text-xs text-gray-500">Tokens: {output.tokens_used.toLocaleString()}</p>
          </div>
        </div>
      )}
    </div>
  )
}
