import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell } from 'recharts'
import { checkHealth } from '../services/api'

// ── Mock data (mirrors backend data layer exactly) ─────────────────────────

const METRICS = [
  { date: 'Jul 4',  crash_rate: 0.8,  p95_latency: 210, support_tickets: 34,  retention_d1: 61.5, error_rate: 0.12, dau: 48340, payment_success: 98.7, churn: 12 },
  { date: 'Jul 5',  crash_rate: 0.9,  p95_latency: 215, support_tickets: 31,  retention_d1: 62.1, error_rate: 0.11, dau: 47910, payment_success: 98.9, churn: 10 },
  { date: 'Jul 6',  crash_rate: 0.7,  p95_latency: 208, support_tickets: 28,  retention_d1: 61.8, error_rate: 0.10, dau: 48620, payment_success: 99.1, churn: 9  },
  { date: 'Jul 7',  crash_rate: 1.4,  p95_latency: 248, support_tickets: 62,  retention_d1: 63.5, error_rate: 0.18, dau: 53200, payment_success: 98.5, churn: 11 },
  { date: 'Jul 8',  crash_rate: 1.6,  p95_latency: 264, support_tickets: 78,  retention_d1: 60.9, error_rate: 0.22, dau: 51800, payment_success: 98.1, churn: 14 },
  { date: 'Jul 9',  crash_rate: 2.1,  p95_latency: 295, support_tickets: 94,  retention_d1: 59.8, error_rate: 0.31, dau: 50440, payment_success: 97.6, churn: 17 },
  { date: 'Jul 10', crash_rate: 2.9,  p95_latency: 381, support_tickets: 148, retention_d1: 55.2, error_rate: 0.54, dau: 47100, payment_success: 96.2, churn: 31 },
  { date: 'Jul 11', crash_rate: 3.1,  p95_latency: 412, support_tickets: 163, retention_d1: 53.8, error_rate: 0.61, dau: 45600, payment_success: 95.8, churn: 38 },
  { date: 'Jul 12', crash_rate: 2.6,  p95_latency: 368, support_tickets: 141, retention_d1: 55.1, error_rate: 0.48, dau: 46200, payment_success: 96.4, churn: 33 },
  { date: 'Jul 13', crash_rate: 2.4,  p95_latency: 352, support_tickets: 128, retention_d1: 56.0, error_rate: 0.43, dau: 46800, payment_success: 96.7, churn: 29 },
]

const FEEDBACK_THEMES = [
  { theme: 'Crashes',     count: 5, sentiment: 'negative' },
  { theme: 'Performance', count: 4, sentiment: 'negative' },
  { theme: 'Payment',     count: 3, sentiment: 'negative' },
  { theme: 'Churn Risk',  count: 3, sentiment: 'negative' },
  { theme: 'Data Issues', count: 3, sentiment: 'negative' },
  { theme: 'Positive UX', count: 9, sentiment: 'positive' },
  { theme: 'Neutral',     count: 6, sentiment: 'neutral'  },
]

const KPI_CARDS = [
  { label: 'Crash Rate',       value: '2.4',   unit: '/1k',  baseline: '0.8',  delta: '+200%', status: 'critical' },
  { label: 'p95 Latency',      value: '352',   unit: 'ms',   baseline: '210',  delta: '+68%',  status: 'critical' },
  { label: 'D1 Retention',     value: '56.0',  unit: '%',    baseline: '61.8', delta: '-5.8pp', status: 'warning' },
  { label: 'Payment Success',  value: '96.7',  unit: '%',    baseline: '98.9', delta: '-2.2pp', status: 'warning' },
  { label: 'Support Tickets',  value: '128',   unit: '/day', baseline: '31',   delta: '+313%', status: 'critical' },
  { label: 'DAU',              value: '46.8k', unit: '',     baseline: '48.3k',delta: '-3.1%', status: 'warning' },
]

const STATUS_COLORS = {
  critical: { text: '#ff3b3b', bg: 'rgba(255,59,59,0.1)',  border: 'rgba(255,59,59,0.2)'  },
  warning:  { text: '#f5a623', bg: 'rgba(245,166,35,0.1)', border: 'rgba(245,166,35,0.2)' },
  healthy:  { text: '#00d97e', bg: 'rgba(0,217,126,0.1)',  border: 'rgba(0,217,126,0.2)'  },
}

const SENTIMENT_COLORS = {
  negative: '#ff3b3b',
  positive: '#00d97e',
  neutral:  '#4a5568',
}

// ── Sub-components ──────────────────────────────────────────────────────────

function KpiCard({ label, value, unit, baseline, delta, status }) {
  const c = STATUS_COLORS[status]
  return (
    <div
      className="card p-4 flex flex-col gap-2"
      style={{ borderColor: c.border, background: c.bg }}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">{label}</span>
        <span
          className="text-xs font-mono px-2 py-0.5 rounded"
          style={{ color: c.text, background: `${c.text}15` }}
        >
          {status}
        </span>
      </div>
      <div className="flex items-end gap-2">
        <span className="text-2xl font-display" style={{ color: c.text }}>
          {value}<span className="text-sm ml-0.5 text-gray-500">{unit}</span>
        </span>
      </div>
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>baseline: {baseline}{unit}</span>
        <span style={{ color: c.text }}>{delta}</span>
      </div>
    </div>
  )
}

function MiniChart({ dataKey, color, threshold, unit = '' }) {
  const CustomTip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div className="card-2 px-2 py-1 text-xs font-mono">
        <span style={{ color }}>{payload[0].value}{unit}</span>
        <span className="text-gray-600 ml-2">{label}</span>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={80}>
      <LineChart data={METRICS} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <XAxis dataKey="date" hide />
        <YAxis hide />
        <Tooltip content={<CustomTip />} />
        {threshold && (
          <ReferenceLine y={threshold} stroke={color} strokeDasharray="3 3" strokeOpacity={0.35} />
        )}
        <ReferenceLine x="Jul 7" stroke="#ff3b3b" strokeDasharray="4 4" strokeOpacity={0.25} />
        <Line
          type="monotone" dataKey={dataKey} stroke={color}
          strokeWidth={1.5} dot={{ r: 2, fill: color, strokeWidth: 0 }} activeDot={{ r: 3 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

function ApiStatus({ connected }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="w-2 h-2 rounded-full"
        style={{ background: connected ? '#00d97e' : '#ff3b3b' }}
      />
      <span className="text-xs text-gray-500 font-mono">
        API {connected ? 'online' : 'offline'}
      </span>
    </div>
  )
}

// ── Main Dashboard ──────────────────────────────────────────────────────────

export default function Dashboard() {
  const [apiConnected, setApiConnected] = useState(null)
  const [activeChart, setActiveChart]   = useState('crash_rate')

  useEffect(() => {
    checkHealth()
      .then(() => setApiConnected(true))
      .catch(() => setApiConnected(false))
  }, [])

  const CHART_OPTIONS = [
    { key: 'crash_rate',      label: 'Crash Rate',  color: '#ff3b3b', threshold: 2.0,  unit: '' },
    { key: 'p95_latency',     label: 'p95 Latency', color: '#f5a623', threshold: 300,  unit: 'ms' },
    { key: 'support_tickets', label: 'Tickets',     color: '#9f7aea', threshold: 120,  unit: '' },
    { key: 'retention_d1',    label: 'D1 Retention',color: '#00d97e', threshold: 58,   unit: '%' },
    { key: 'dau',             label: 'DAU',          color: '#63b3ed', threshold: null, unit: '' },
    { key: 'churn',           label: 'Churn',        color: '#fc8181', threshold: 20,   unit: '' },
  ]

  const active = CHART_OPTIONS.find(c => c.key === activeChart)

  return (
    <div className="min-h-screen" style={{ background: 'var(--night)' }}>

      {/* Header */}
      <header className="border-b border-white/5 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold"
            style={{ background: 'var(--kairos-orange)', color: 'white' }}
          >
            K
          </div>
          <span className="font-display text-white text-lg tracking-wide">KairosAI</span>
          <span className="text-xs text-gray-700 font-mono ml-2">DASHBOARD</span>
        </div>
        <div className="flex items-center gap-6">
          {apiConnected !== null && <ApiStatus connected={apiConnected} />}
          <a
            href="/"
            className="text-xs px-4 py-1.5 rounded-lg font-medium transition-all"
            style={{ background: 'rgba(232,85,42,0.15)', color: '#e8552a', border: '1px solid rgba(232,85,42,0.2)' }}
          >
            → War Room
          </a>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-8 py-8 space-y-8">

        {/* Section: Launch context */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-display text-2xl text-white mb-1">SmartDash 2.0 Launch</h1>
            <p className="text-sm text-gray-500">
              PurpleMerit · Launch date Jul 7, 2025 · 10-day monitoring window
            </p>
          </div>
          <div className="card px-4 py-2 text-right">
            <p className="text-xs text-gray-600 font-mono">Current status</p>
            <p className="text-sm font-medium" style={{ color: '#ff3b3b' }}>
              🔴 Rollback recommended
            </p>
          </div>
        </div>

        {/* KPI Cards */}
        <div>
          <p className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-3">KPI Snapshot — Latest vs Baseline</p>
          <div className="grid grid-cols-3 gap-4">
            {KPI_CARDS.map(kpi => <KpiCard key={kpi.label} {...kpi} />)}
          </div>
        </div>

        {/* Main chart */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="text-sm font-medium text-white">10-Day Trend</p>
            <div className="flex gap-2">
              {CHART_OPTIONS.map(opt => (
                <button
                  key={opt.key}
                  onClick={() => setActiveChart(opt.key)}
                  className="text-xs px-3 py-1 rounded-lg font-mono transition-all"
                  style={{
                    background: activeChart === opt.key ? `${opt.color}20` : 'transparent',
                    color:      activeChart === opt.key ? opt.color : '#4a5568',
                    border:     `1px solid ${activeChart === opt.key ? `${opt.color}40` : 'transparent'}`,
                  }}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={METRICS} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
              <XAxis
                dataKey="date"
                tick={{ fill: '#4a5568', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                axisLine={false} tickLine={false}
              />
              <YAxis
                tick={{ fill: '#4a5568', fontSize: 10, fontFamily: 'JetBrains Mono' }}
                axisLine={false} tickLine={false} width={40}
              />
              <Tooltip
                contentStyle={{ background: '#1a1d2e', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, fontSize: 12, fontFamily: 'JetBrains Mono' }}
                labelStyle={{ color: '#718096' }}
                itemStyle={{ color: active?.color }}
              />
              {active?.threshold && (
                <ReferenceLine
                  y={active.threshold} stroke={active?.color}
                  strokeDasharray="4 4" strokeOpacity={0.4}
                  label={{ value: 'threshold', fill: active?.color, fontSize: 10, position: 'insideTopRight' }}
                />
              )}
              <ReferenceLine
                x="Jul 7" stroke="#ff3b3b" strokeDasharray="4 4" strokeOpacity={0.35}
                label={{ value: 'launch', fill: '#ff3b3b', fontSize: 10, position: 'insideTopLeft' }}
              />
              <Line
                type="monotone" dataKey={activeChart}
                stroke={active?.color} strokeWidth={2}
                dot={{ r: 3, fill: active?.color, strokeWidth: 0 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Bottom grid: mini charts + feedback */}
        <div className="grid grid-cols-2 gap-6">

          {/* Mini charts grid */}
          <div className="card p-5">
            <p className="text-sm font-medium text-white mb-4">All KPIs at a glance</p>
            <div className="grid grid-cols-2 gap-4">
              {[
                { key: 'crash_rate',     label: 'Crash Rate',  color: '#ff3b3b', threshold: 2.0  },
                { key: 'p95_latency',    label: 'p95 Latency', color: '#f5a623', threshold: 300  },
                { key: 'error_rate',     label: 'Error Rate',  color: '#fc8181', threshold: 0.5  },
                { key: 'payment_success',label: 'Payment %',   color: '#00d97e', threshold: 97.5 },
              ].map(c => (
                <div key={c.key}>
                  <p className="text-xs text-gray-600 font-mono mb-1">{c.label}</p>
                  <MiniChart dataKey={c.key} color={c.color} threshold={c.threshold} />
                </div>
              ))}
            </div>
          </div>

          {/* Feedback sentiment */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm font-medium text-white">User Feedback Themes</p>
              <div className="flex gap-3 text-xs text-gray-600">
                <span><span className="text-red-400">■</span> Negative</span>
                <span><span className="text-green-400">■</span> Positive</span>
                <span><span className="text-gray-600">■</span> Neutral</span>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={180}>
              <BarChart
                data={FEEDBACK_THEMES}
                layout="vertical"
                margin={{ top: 0, right: 8, bottom: 0, left: 60 }}
              >
                <XAxis type="number" hide />
                <YAxis
                  type="category" dataKey="theme"
                  tick={{ fill: '#718096', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                  axisLine={false} tickLine={false} width={60}
                />
                <Tooltip
                  contentStyle={{ background: '#1a1d2e', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, fontSize: 11 }}
                  labelStyle={{ color: '#718096' }}
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {FEEDBACK_THEMES.map((entry, i) => (
                    <Cell key={i} fill={SENTIMENT_COLORS[entry.sentiment]} fillOpacity={0.7} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {/* Summary pills */}
            <div className="flex gap-3 mt-3 pt-3 border-t border-white/5">
              <div className="flex-1 text-center">
                <p className="text-lg font-display" style={{ color: '#ff3b3b' }}>54.3%</p>
                <p className="text-xs text-gray-600">Negative</p>
              </div>
              <div className="flex-1 text-center">
                <p className="text-lg font-display text-gray-500">17.1%</p>
                <p className="text-xs text-gray-600">Neutral</p>
              </div>
              <div className="flex-1 text-center">
                <p className="text-lg font-display" style={{ color: '#00d97e' }}>28.6%</p>
                <p className="text-xs text-gray-600">Positive</p>
              </div>
              <div className="flex-1 text-center">
                <p className="text-lg font-display" style={{ color: '#f5a623' }}>35</p>
                <p className="text-xs text-gray-600">Total entries</p>
              </div>
            </div>
          </div>
        </div>

        {/* Release notes summary */}
        <div className="card p-5">
          <p className="text-sm font-medium text-white mb-4">Release Notes — SmartDash 2.0</p>
          <div className="grid grid-cols-2 gap-4">
            {[
              { id: 'KI-001', sev: 'high',     comp: 'GraphQL / DataLoader',  desc: 'N+1 query risk under sustained concurrent load (>500 simultaneous loads)',      status: 'accepted_risk' },
              { id: 'KI-002', sev: 'medium',   comp: 'Auto-Migration Script', desc: 'Migration timeout for accounts with >500 saved configs — blank panels on load', status: 'known_bug'     },
              { id: 'KI-005', sev: 'critical',  comp: 'iOS App',               desc: 'iOS 17 crash on AI Summary Widget in low-power mode — nil reference in bridge', status: 'in_progress'   },
              { id: 'KI-006', sev: 'critical',  comp: 'Payment Gateway',       desc: 'Race condition causing duplicate Stripe charges — affects ~0.8% of upgrades',  status: 'hotfix_deployed'},
            ].map(issue => (
              <div key={issue.id} className="card-2 p-3 flex gap-3">
                <div className="flex-shrink-0">
                  <span className={`text-xs font-mono px-1.5 py-0.5 rounded ${
                    issue.sev === 'critical' ? 'badge-critical' :
                    issue.sev === 'high'     ? 'badge-high'     : 'badge-medium'
                  }`}>
                    {issue.id}
                  </span>
                </div>
                <div className="min-w-0">
                  <p className="text-xs text-gray-400 font-mono mb-0.5">{issue.comp}</p>
                  <p className="text-xs text-gray-500 leading-relaxed">{issue.desc}</p>
                  <p className="text-xs mt-1 font-mono"
                    style={{ color: issue.status === 'hotfix_deployed' ? '#00d97e' : issue.status === 'in_progress' ? '#f5a623' : '#718096' }}>
                    {issue.status.replace('_', ' ')}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}