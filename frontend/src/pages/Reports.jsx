import React, { useState, useEffect } from 'react'
import { listSessions, getReport } from '../services/api'

const VERDICT_CONFIG = {
  PROCEED:   { color: '#00d97e', label: 'PROCEED',   icon: '✓' },
  PAUSE:     { color: '#f5a623', label: 'PAUSE',     icon: '⏸' },
  ROLL_BACK: { color: '#ff3b3b', label: 'ROLL BACK', icon: '↩' },
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}

function SessionRow({ session, onSelect, isSelected }) {
  const cfg = VERDICT_CONFIG[session.decision] || { color: '#718096', label: session.decision, icon: '?' }
  return (
    <div
      className={`card p-4 cursor-pointer transition-all duration-200 ${
        isSelected ? 'border-orange-500/30' : 'hover:border-white/10'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-lg">{cfg.icon}</span>
          <div>
            <p className="text-sm font-mono text-gray-300">{session.session_id}</p>
            <p className="text-xs text-gray-600">{formatDate(session.generated)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-gray-500">
            {session.confidence}/100
          </span>
          <span
            className="text-xs font-mono px-2 py-0.5 rounded"
            style={{ color: cfg.color, background: `${cfg.color}15`, border: `1px solid ${cfg.color}30` }}
          >
            {cfg.label}
          </span>
        </div>
      </div>
    </div>
  )
}

function ReportDetail({ report }) {
  if (!report) return null

  const cfg    = VERDICT_CONFIG[report.decision] || { color: '#718096', label: report.decision, icon: '?' }
  const conf   = report.confidence || {}
  const risks  = report.risk_register || []
  const agents = report.agent_verdicts || []
  const comms  = report.communication_plan || {}
  const debate = report.debate_summary || {}
  const actions = report.action_plan || {}

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `warroom_${report.meta?.session_id}_report.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-5 animate-fade-in">

      {/* Verdict banner */}
      <div
        className="card p-6 text-center"
        style={{ borderColor: `${cfg.color}30`, background: `${cfg.color}08` }}
      >
        <p className="text-3xl font-display mb-1" style={{ color: cfg.color }}>
          {cfg.icon} {cfg.label}
        </p>
        <p className="text-sm text-gray-500 font-mono">
          Confidence {conf.weighted_score}/100 · {conf.interpretation}
        </p>
        <div className="flex justify-center gap-3 mt-3 flex-wrap">
          {Object.entries(conf.verdict_distribution || {}).map(([v, c]) => {
            const vc = VERDICT_CONFIG[v]
            return (
              <span
                key={v}
                className="text-xs font-mono px-3 py-0.5 rounded-full"
                style={{ color: vc?.color || '#888', background: `${vc?.color || '#888'}15`, border: `1px solid ${vc?.color || '#888'}30` }}
              >
                {v.replace('_', ' ')}: {c}
              </span>
            )
          })}
        </div>
      </div>

      {/* Agent verdicts */}
      <div className="card p-5">
        <p className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-3">Agent Verdicts</p>
        <div className="space-y-2">
          {agents.map((a, i) => {
            const ac = VERDICT_CONFIG[a.verdict] || { color: '#718096' }
            return (
              <div key={i} className="flex items-start gap-3 card-2 p-3">
                <span
                  className="text-xs font-mono px-2 py-0.5 rounded flex-shrink-0 mt-0.5"
                  style={{ color: ac.color, background: `${ac.color}15`, border: `1px solid ${ac.color}30` }}
                >
                  {(a.verdict || '').replace('_', ' ')}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-medium text-gray-300">{a.agent_name || a.agent}</p>
                  <p className="text-xs text-gray-600 mt-0.5 leading-relaxed">{a.summary}</p>
                </div>
                <span className="text-xs font-mono text-gray-700 flex-shrink-0">{a.confidence}/100</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Debate summary */}
      {debate.tension && (
        <div className="card p-5">
          <p className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-3">Debate Summary</p>
          <div className="space-y-2 text-sm">
            <div className="flex gap-2">
              <span className="text-gray-600 flex-shrink-0 w-24 text-xs font-mono">Tension</span>
              <span className="text-gray-400 text-xs">{debate.tension}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-600 flex-shrink-0 w-24 text-xs font-mono">Ruling</span>
              <span className="text-gray-400 text-xs">{debate.ruling || debate.resolved_verdict}</span>
            </div>
            <div className="flex gap-2">
              <span className="text-gray-600 flex-shrink-0 w-24 text-xs font-mono">Open Q</span>
              <span className="text-gray-500 text-xs italic">{debate.key_unresolved}</span>
            </div>
          </div>
        </div>
      )}

      {/* Risk register */}
      {risks.length > 0 && (
        <div className="card overflow-hidden">
          <p className="text-xs font-mono text-gray-600 uppercase tracking-wider px-5 py-3 border-b border-white/5">
            Risk Register ({risks.length})
          </p>
          <div className="divide-y divide-white/5">
            {risks.map((risk, i) => (
              <div key={i} className="px-5 py-3 flex gap-3 items-start">
                <span className={`text-xs font-mono px-2 py-0.5 rounded flex-shrink-0 mt-0.5 ${
                  risk.severity === 'critical' ? 'badge-critical' :
                  risk.severity === 'high'     ? 'badge-high'     :
                  risk.severity === 'medium'   ? 'badge-medium'   : 'badge-low'
                }`}>
                  {(risk.severity || '').toUpperCase()}
                </span>
                <div className="min-w-0">
                  <p className="text-xs text-gray-300">{risk.risk}</p>
                  <p className="text-xs text-gray-600 mt-0.5">{risk.mitigation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action plan */}
      {Object.keys(actions).some(k => actions[k]?.length > 0) && (
        <div className="card p-5">
          <p className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-3">Action Plan</p>
          <div className="space-y-4">
            {[
              { key: 'immediate',  label: '🚨 Immediate',  color: '#ff3b3b' },
              { key: 'within_24h', label: '⚡ Within 24h', color: '#f5a623' },
              { key: 'within_48h', label: '📋 Within 48h', color: '#63b3ed' },
            ].map(({ key, label, color }) => {
              const items = actions[key] || []
              if (!items.length) return null
              return (
                <div key={key}>
                  <p className="text-xs font-mono mb-2" style={{ color }}>{label}</p>
                  <div className="space-y-1.5 ml-4">
                    {items.map((a, i) => (
                      <div key={i} className="flex gap-2 text-xs">
                        <span className="text-gray-600 flex-shrink-0 font-mono">[{a.owner}]</span>
                        <span className="text-gray-400">{a.action}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Communication plan */}
      {comms.internal_message && (
        <div className="card p-5">
          <p className="text-xs font-mono text-gray-600 uppercase tracking-wider mb-3">Communication Plan</p>
          <div className="space-y-3">
            {[
              { label: 'Internal',    text: comms.internal_message,   color: '#9f7aea' },
              { label: 'User-facing', text: comms.user_message,       color: '#63b3ed' },
              { label: 'Enterprise',  text: comms.enterprise_message,  color: '#f5a623' },
            ].map(({ label, text, color }) => (
              <div key={label} className="card-2 p-3">
                <p className="text-xs font-mono mb-1" style={{ color }}>{label}</p>
                <p className="text-xs text-gray-400 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Download */}
      <button
        onClick={downloadJSON}
        className="w-full py-3 rounded-xl text-sm font-medium transition-all hover:opacity-90"
        style={{ background: 'rgba(232,85,42,0.15)', color: '#e8552a', border: '1px solid rgba(232,85,42,0.25)' }}
      >
        ↓ Download JSON Report
      </button>

    </div>
  )
}

// ── Main Reports page ────────────────────────────────────────────────────────

export default function Reports() {
  const [sessions, setSessions]   = useState([])
  const [loading, setLoading]     = useState(true)
  const [selected, setSelected]   = useState(null)
  const [report, setReport]       = useState(null)
  const [loadingReport, setLoadingReport] = useState(false)
  const [error, setError]         = useState(null)

  useEffect(() => {
    listSessions()
      .then(res => {
        setSessions(res.data.sessions || [])
        setLoading(false)
      })
      .catch(() => {
        setError('Could not connect to API. Make sure the backend is running.')
        setLoading(false)
      })
  }, [])

  const selectSession = async (sessionId) => {
    setSelected(sessionId)
    setReport(null)
    setLoadingReport(true)
    try {
      const res = await getReport(sessionId)
      setReport(res.data)
    } catch {
      setReport(null)
    } finally {
      setLoadingReport(false)
    }
  }

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
          <span className="text-xs text-gray-700 font-mono ml-2">REPORTS</span>
        </div>
        <div className="flex gap-3">
          <a href="/dashboard" className="text-xs text-gray-600 hover:text-gray-400 transition-colors px-3 py-1.5">Dashboard</a>
          <a
            href="/"
            className="text-xs px-4 py-1.5 rounded-lg font-medium transition-all"
            style={{ background: 'rgba(232,85,42,0.15)', color: '#e8552a', border: '1px solid rgba(232,85,42,0.2)' }}
          >
            → War Room
          </a>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="grid grid-cols-5 gap-6">

          {/* Left — session list */}
          <div className="col-span-2 space-y-3">
            <p className="text-xs font-mono text-gray-600 uppercase tracking-wider">Sessions</p>

            {loading && (
              <div className="card p-8 text-center">
                <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse inline-block mr-2" />
                <span className="text-sm text-gray-600">Loading sessions...</span>
              </div>
            )}

            {error && (
              <div className="card p-5 border-red-500/20">
                <p className="text-xs text-red-400">{error}</p>
              </div>
            )}

            {!loading && !error && sessions.length === 0 && (
              <div className="card p-8 text-center">
                <p className="text-sm text-gray-600 mb-3">No sessions yet</p>
                <a
                  href="/"
                  className="text-xs px-4 py-2 rounded-lg"
                  style={{ background: 'rgba(232,85,42,0.15)', color: '#e8552a' }}
                >
                  Run your first war room →
                </a>
              </div>
            )}

            {sessions.map(s => (
              <SessionRow
                key={s.session_id}
                session={s}
                isSelected={selected === s.session_id}
                onSelect={() => selectSession(s.session_id)}
              />
            ))}
          </div>

          {/* Right — report detail */}
          <div className="col-span-3">
            {!selected && (
              <div className="card p-16 text-center h-48 flex flex-col items-center justify-center">
                <p className="text-sm text-gray-600">Select a session to view the full report</p>
              </div>
            )}

            {loadingReport && (
              <div className="card p-16 text-center flex flex-col items-center justify-center">
                <span className="w-2 h-2 rounded-full bg-orange-500 animate-pulse inline-block mr-2" />
                <span className="text-sm text-gray-600">Loading report...</span>
              </div>
            )}

            {report && !loadingReport && <ReportDetail report={report} />}
          </div>

        </div>
      </div>
    </div>
  )
}