'use client'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getCompany,
  getFinancials,
  getRatios,
  getFilings,
  getGovernance,
  getReport,
  listReports,
  getCompanyReports,
  getJobStatus,
  triggerAnalysis,
  getWatchlist,
  addToWatchlist,
  removeFromWatchlist,
} from '@/lib/api'
import type { DCFAssumptions } from '@/lib/types'

export function useCompany(ticker: string) {
  return useQuery({
    queryKey: ['company', ticker],
    queryFn: () => getCompany(ticker),
    enabled: !!ticker,
  })
}

export function useFinancials(ticker: string) {
  return useQuery({
    queryKey: ['financials', ticker],
    queryFn: () => getFinancials(ticker),
    enabled: !!ticker,
  })
}

export function useRatios(ticker: string) {
  return useQuery({
    queryKey: ['ratios', ticker],
    queryFn: () => getRatios(ticker),
    enabled: !!ticker,
  })
}

export function useFilings(ticker: string) {
  return useQuery({
    queryKey: ['filings', ticker],
    queryFn: () => getFilings(ticker),
    enabled: !!ticker,
  })
}

export function useGovernance(ticker: string) {
  return useQuery({
    queryKey: ['governance', ticker],
    queryFn: () => getGovernance(ticker),
    enabled: !!ticker,
  })
}

export function useReport(reportId: string) {
  return useQuery({
    queryKey: ['report', reportId],
    queryFn: () => getReport(reportId),
    enabled: !!reportId,
  })
}

export function useListReports() {
  return useQuery({
    queryKey: ['reports'],
    queryFn: listReports,
  })
}

export function useCompanyReports(ticker: string) {
  return useQuery({
    queryKey: ['company-reports', ticker],
    queryFn: () => getCompanyReports(ticker),
    enabled: !!ticker,
  })
}

export function useJobPolling(jobId: string | null) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'failed') return false
      return 2000
    },
  })
}

export function useTriggerAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      ticker,
      dcfAssumptions,
    }: {
      ticker: string
      dcfAssumptions?: DCFAssumptions
    }) => triggerAnalysis(ticker, dcfAssumptions),
    onSuccess: (_, { ticker }) => {
      qc.invalidateQueries({ queryKey: ['company-reports', ticker] })
      qc.invalidateQueries({ queryKey: ['reports'] })
    },
  })
}

export function useWatchlist() {
  return useQuery({
    queryKey: ['watchlist'],
    queryFn: getWatchlist,
  })
}

export function useAddToWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ticker: string) => addToWatchlist(ticker),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (ticker: string) => removeFromWatchlist(ticker),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['watchlist'] }),
  })
}
