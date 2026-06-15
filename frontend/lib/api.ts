import axios from 'axios'
import type {
  Company,
  FinancialStatement,
  FinancialRatio,
  SECFiling,
  GovernanceData,
  ResearchReport,
  AnalysisJob,
  WatchlistItem,
  DCFAssumptions,
} from './types'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
    }
    return Promise.reject(err)
  }
)

export async function searchCompanies(query: string): Promise<Company[]> {
  const { data } = await api.get('/api/v1/companies/search', { params: { q: query } })
  return data
}

export async function getCompany(ticker: string): Promise<Company> {
  const { data } = await api.get(`/api/v1/companies/${ticker}`)
  return data
}

export async function getFinancials(ticker: string): Promise<FinancialStatement[]> {
  const { data } = await api.get(`/api/v1/companies/${ticker}/financials`)
  return data
}

export async function getRatios(ticker: string): Promise<FinancialRatio[]> {
  const { data } = await api.get(`/api/v1/companies/${ticker}/ratios`)
  return data
}

export async function getFilings(ticker: string): Promise<SECFiling[]> {
  const { data } = await api.get(`/api/v1/companies/${ticker}/filings`)
  return data
}

export async function getGovernance(ticker: string): Promise<GovernanceData | null> {
  const { data } = await api.get(`/api/v1/companies/${ticker}/governance`)
  return data
}

export async function getPeers(ticker: string): Promise<Company[]> {
  const { data } = await api.get(`/api/v1/companies/${ticker}/peers`)
  return data
}

export async function triggerAnalysis(
  ticker: string,
  dcfAssumptions?: DCFAssumptions
): Promise<{ job_id: string }> {
  const { data } = await api.post(`/api/v1/companies/${ticker}/analyze`, {
    dcf_assumptions: dcfAssumptions,
  })
  return data
}

export async function getReport(reportId: string): Promise<ResearchReport> {
  const { data } = await api.get(`/api/v1/reports/${reportId}`)
  return data
}

export async function listReports(): Promise<ResearchReport[]> {
  const { data } = await api.get('/api/v1/reports/')
  return data
}

export async function getCompanyReports(ticker: string): Promise<ResearchReport[]> {
  const { data } = await api.get(`/api/v1/companies/${ticker}/reports`)
  return data
}

export async function getJobStatus(jobId: string): Promise<AnalysisJob> {
  const { data } = await api.get(`/api/v1/jobs/${jobId}`)
  return data
}

export async function getWatchlist(): Promise<WatchlistItem[]> {
  const { data } = await api.get('/api/v1/watchlist/')
  return data
}

export async function addToWatchlist(ticker: string): Promise<WatchlistItem> {
  const { data } = await api.post('/api/v1/watchlist/', { ticker })
  return data
}

export async function removeFromWatchlist(ticker: string): Promise<void> {
  await api.delete(`/api/v1/watchlist/${ticker}`)
}

export async function runDCF(ticker: string, assumptions: DCFAssumptions): Promise<unknown> {
  const { data } = await api.post(`/api/v1/valuation/${ticker}/dcf`, assumptions)
  return data
}

export async function getComps(ticker: string): Promise<unknown> {
  const { data } = await api.get(`/api/v1/valuation/${ticker}/comps`)
  return data
}

export async function login(email: string, password: string): Promise<{ access_token: string }> {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const { data } = await api.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export async function register(
  email: string,
  password: string,
  fullName: string
): Promise<{ id: string; email: string }> {
  const { data } = await api.post('/auth/register', {
    email,
    password,
    full_name: fullName,
  })
  return data
}

export default api
