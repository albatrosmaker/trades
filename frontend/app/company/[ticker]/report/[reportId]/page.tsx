import { ReportViewer } from './ReportViewer'

export function generateStaticParams() {
  return [{ ticker: 'AAPL', reportId: 'demo-report' }]
}

export default function ReportPage() {
  return <ReportViewer />
}
