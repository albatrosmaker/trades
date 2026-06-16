'use client'
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface BarConfig {
  key: string
  label: string
  color: string
}

interface LineConfig {
  key: string
  label: string
  color: string
}

interface FinancialChartProps {
  data: Record<string, unknown>[]
  bars?: BarConfig[]
  lines?: LineConfig[]
  height?: number
  title?: string
  formatValue?: (value: number) => string
  xKey?: string
}

const defaultFormat = (v: number) => {
  if (Math.abs(v) >= 1e9) return `$${(v / 1e9).toFixed(1)}B`
  if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`
  return `$${v.toLocaleString()}`
}

export function FinancialChart({
  data,
  bars = [],
  lines = [],
  height = 260,
  title,
  formatValue = defaultFormat,
  xKey = 'period',
}: FinancialChartProps) {
  return (
    <div className="w-full">
      {title && (
        <p className="text-sm text-gray-400 mb-3 font-medium">{title}</p>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fill: '#6B7280', fontSize: 11, fontFamily: 'monospace' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={formatValue}
            tick={{ fill: '#6B7280', fontSize: 11, fontFamily: 'monospace' }}
            axisLine={false}
            tickLine={false}
            width={72}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f1629',
              border: '1px solid #1e2d4a',
              borderRadius: 6,
              fontSize: 12,
              fontFamily: 'monospace',
            }}
            labelStyle={{ color: '#9CA3AF' }}
            formatter={(value: number, name: string) => [formatValue(value), name]}
          />
          <Legend
            wrapperStyle={{ fontSize: 11, fontFamily: 'monospace', color: '#6B7280' }}
          />
          {bars.map((b) => (
            <Bar key={b.key} dataKey={b.key} name={b.label} fill={b.color} radius={[2, 2, 0, 0]} />
          ))}
          {lines.map((l) => (
            <Line
              key={l.key}
              type="monotone"
              dataKey={l.key}
              name={l.label}
              stroke={l.color}
              strokeWidth={2}
              dot={{ fill: l.color, r: 3 }}
            />
          ))}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  )
}
