import { CompanyDashboard } from './CompanyDashboard'

export function generateStaticParams() {
  return [{ ticker: 'AAPL' }]
}

export default function CompanyPage() {
  return <CompanyDashboard />
}
