import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

const METRICS_DATA = [
  { date: 'Jul 4',  crash_rate: 0.8,  p95_latency: 210, support_tickets: 34,  retention_d1: 61.5 },
  { date: 'Jul 5',  crash_rate: 0.9,  p95_latency: 215, support_tickets: 31,  retention_d1: 62.1 },
  { date: 'Jul 6',  crash_rate: 0.7,  p95_latency: 208, support_tickets: 28,  retention_d1: 61.8 },
  { date: 'Jul 7',  crash_rate: 1.4,  p95_latency: 248, support_tickets: 62,  retention_d1: 63.5 },
  { date: 'Jul 8',  crash_rate: 1.6,  p95_latency: 264, support_tickets: 78,  retention_d1: 60.9 },
  { date: 'Jul 9',  crash_rate: 2.1,  p95_latency: 295, support_tickets: 94,  retention_d1: 59.8 },
  { date: 'Jul 10', crash_rate: 2.9,  p95_latency: 381, support_tickets: 148, retention_d1: 55.2 },
  { date: 'Jul 11', crash_rate: 3.1,  p95_latency: 412, support_tickets: 163, retention_d1: 53.8 },
  { date: 'Jul 12', crash_rate: 2.6,  p95_latency: 368, support_tickets: 141, retention_d1: 55.1 },
  { date: 'Jul 13', crash_rate: 2.4,  p95_latency: 352, support_tickets: 128, retention_d1: 56.0 },
]

const CHARTS = [
  { key: 'crash_rate',       label: 'Crash Rate (/1000)',  color: '#ff3b3b', threshold: 2.0,  unit: '' },
  { key: 'p95_latency',      label: 'p95 Latency (ms)',    color: '#f5a623', threshold: 300,  unit: 'ms' },
  { key: 'support_tickets',  label: 'Support Tickets',     color: '#9f7aea', threshold: 120,  unit: '' },
  { key: 'retention_d1',     label: 'D1 Retention (%)',    color: '#00d97e', threshold: 58.0, unit: '%' },
]

const CustomTooltip = ({ active, payload, label, unit }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="card-2 px-3 py-2 text-xs font-mono">
      <p className="text-gray-400 mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.value}{unit}</p>
      ))}
    </div>
  )
}

export default function MetricsChart() {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-5">
        <span className="text-sm font-medium text-white">KPI Dashboard — 10-Day Window</span>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
          <span className="text-xs text-gray-500">Launch Day Jul 7</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {CHARTS.map(({ key, label, color, threshold, unit }) => (
          <div key={key}>
            <p className="text-xs text-gray-500 font-mono mb-2">{label}</p>
            <ResponsiveContainer width="100%" height={100}>
              <LineChart data={METRICS_DATA} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                <XAxis
                  dataKey="date"
                  tick={{ fill: '#4a5568', fontSize: 9, fontFamily: 'JetBrains Mono' }}
                  axisLine={false}
                  tickLine={false}
                  interval={2}
                />
                <YAxis hide />
                <Tooltip content={<CustomTooltip unit={unit} />} />
                <ReferenceLine
                  y={threshold}
                  stroke={color}
                  strokeDasharray="3 3"
                  strokeOpacity={0.4}
                />
                <ReferenceLine
                  x="Jul 7"
                  stroke="#ff3b3b"
                  strokeDasharray="4 4"
                  strokeOpacity={0.3}
                />
                <Line
                  type="monotone"
                  dataKey={key}
                  stroke={color}
                  strokeWidth={1.5}
                  dot={{ r: 2, fill: color, strokeWidth: 0 }}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-white/5">
        <div className="flex items-center gap-1.5">
          <span className="text-red-500" style={{ fontSize: 10 }}>- - -</span>
          <span className="text-xs text-gray-600">threshold</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-red-400" style={{ fontSize: 10 }}>│</span>
          <span className="text-xs text-gray-600">launch day</span>
        </div>
      </div>
    </div>
  )
}