'use client'
import { X, ExternalLink } from 'lucide-react'
import { SourceBadge } from './SourceBadge'
import { cn } from '@/lib/utils'
import type { Evidence } from '@/lib/types'

interface EvidencePanelProps {
  evidence: Evidence | null
  onClose: () => void
}

export function EvidencePanel({ evidence, onClose }: EvidencePanelProps) {
  return (
    <div
      className={cn(
        'fixed right-0 top-0 h-full w-96 bg-[#0f1629] border-l border-[#1e2d4a] z-50',
        'transform transition-transform duration-300 shadow-2xl',
        evidence ? 'translate-x-0' : 'translate-x-full'
      )}
    >
      <div className="flex items-center justify-between p-4 border-b border-[#1e2d4a]">
        <h3 className="font-semibold text-white">Evidence Explorer</h3>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-[#1e2d4a] text-gray-400 hover:text-white transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {evidence && (
        <div className="p-4 overflow-y-auto h-full pb-20 space-y-4">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Metric</p>
            <p className="text-white font-medium">{evidence.metric_name ?? evidence.claim}</p>
          </div>

          <div className="flex items-center gap-2">
            <SourceBadge source={evidence.source} />
            {evidence.filing_type && (
              <span className="text-xs text-gray-400 font-mono">{evidence.filing_type}</span>
            )}
            {evidence.period && (
              <span className="text-xs text-gray-400 font-mono">{evidence.period}</span>
            )}
          </div>

          {evidence.value !== null && evidence.value !== undefined && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Value</p>
              <p className="text-emerald-400 font-mono text-lg">{String(evidence.value)}</p>
            </div>
          )}

          {evidence.formula && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Formula</p>
              <pre className="bg-[#0a0e1a] border border-[#1e2d4a] rounded p-3 text-xs text-blue-300 font-mono whitespace-pre-wrap">
                {evidence.formula}
              </pre>
            </div>
          )}

          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Claim</p>
            <p className="text-gray-300 text-sm">{evidence.claim}</p>
          </div>

          <div className="pt-2 border-t border-[#1e2d4a]">
            <p className="text-xs text-gray-500 mb-2">
              Source: {evidence.source.replace('_', ' ')}
            </p>
            <p className="text-xs text-yellow-600/80">
              Always verify against the original SEC filing at EDGAR.gov
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
