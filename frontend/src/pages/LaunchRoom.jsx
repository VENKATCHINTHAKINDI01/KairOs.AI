import React, { useState } from 'react'
import DecisionPanel  from '../components/DecisionPanel'
import AgentCard      from '../components/AgentCard'
import TraceLog       from '../components/TraceLog'
import RiskRegister   from '../components/RiskRegister'
import WarRoomMonitor from '../components/WarRoomMonitor'
import MetricsChart   from '../components/MetricsChart'
import { runWarRoom } from '../services/api'

const PHASE_LABELS = ['Data Analyst', 'PM / Marketing / SRE', 'Risk / Critic', 'Debate', 'Decision']

const AGENT_ORDER = [
  'Data Analyst',
  'Product Manager',
  'Marketing / Comms',
  'SRE / Engineering',
  'Risk / Critic',
]

export default function LaunchRoom() {
  const [status, setStatus]     = useState('idle')    // idle | running | complete | error
  const [decision, setDecision] = useState(null)
  const [sessionId, setSessionId] = useState(null)
  const [errorMsg, setErrorMsg] = useState('')
  const [elapsed, setElapsed]   = useState(0)
  const [timerRef, setTimerRef] = useState(null)

  const startWarRoom = async () => {
    setStatus('running')
    setDecision(null)
    setErrorMsg('')
    setElapsed(0)

    // Start elapsed timer
    const start = Date.now()
    const ref = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000)
    setTimerRef(ref)

    try {
      const res = await runWarRoom()
      const data = res.data
      clearInterval(ref)
      setDecision(data)
      setSessionId(data?.meta?.session_id)
      setStatus('complete')
    } catch (err) {
      clearInterval(ref)
      setErrorMsg(err?.response?.data?.detail || err.message || 'Unknown error')
      setStatus('error')
    }
  }

  const reset = () => {
    setStatus('idle')
    setDecision(null)
    setErrorMsg('')
    setElapsed(0)
    if (timerRef) clearInterval(timerRef)
  }

  // Build agent cards from decision data
  const agents = decision
    ? (decision.agent_verdicts || []).map(a => ({
        agent:        a.agent_name || a.agent,
        verdict:      a.verdict,
        confidence:   a.confidence,
        summary:      a.summary,
        key_findings: a.key_findings || [],
      }))
    : []

  // Build fake trace from decision for display
  const traceEvents = decision
    ? [
        { type: 'session_start',   data: { session_id: decision.meta?.session_id }, timestamp: new Date().toISOString() },
        ...agents.map(a => ({ type: 'agent_verdict', data: a, timestamp: new Date().toISOString() })),
        { type: 'debate_resolved', data: decision.debate_summary || {}, timestamp: new Date().toISOString() },
        { type: 'final_decision',  data: { decision: decision.decision, confidence: decision.confidence?.weighted_score, tally: decision.session_stats?.verdict_tally }, timestamp: new Date().toISOString() },
        { type: 'complete',        data: {}, timestamp: new Date().toISOString() },
      ]
    : []

  return (
    <div className="min-h-screen" style={{ background: 'var(--night)' }}>

      {/* Header */}
      <header className="border-b border-white/5 px-8 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center text-sm font-bold"
            style={{ background: 'var(--kairos-orange)', color: 'white' }}>K</div>
          <span className="font-display text-white text-lg tracking-wide">KairosAI</span>
          <span className="text-xs text-gray-700 font-mono ml-2">WAR ROOM</span>
        </div>

        <nav className="flex items-center gap-1">
          <a href="/dashboard" className="text-xs px-3 py-1.5 text-gray-600 hover:text-gray-300 rounded-lg hover:bg-white/5 transition-all">Dashboard</a>
          <a href="/reports"   className="text-xs px-3 py-1.5 text-gray-600 hover:text-gray-300 rounded-lg hover:bg-white/5 transition-all">Reports</a>
        </nav>

        <div className="flex items-center gap-3">
          {status === 'running' && (
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <span className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
              <span className="font-mono">{elapsed}s elapsed — agents thinking...</span>
            </div>
          )}
          {(status === 'idle' || status === 'complete' || status === 'error') && (
            <button onClick={status === 'complete' ? reset : startWarRoom}
              className="px-5 py-2 rounded-lg text-sm font-medium transition-all hover:opacity-90"
              style={{ background: 'var(--kairos-orange)', color: 'white' }}>
              {status === 'complete' ? 'Run Again' : 'Start War Room'}
            </button>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-8 py-8 space-y-6">

        {/* Phase progress indicator */}
        {status === 'running' && (
          <div className="card p-6 text-center animate-fade-in">
            <div className="flex justify-center gap-3 mb-5">
              {AGENT_ORDER.map((agent, i) => (
                <div key={agent} className="flex flex-col items-center gap-2">
                  <div className="w-2 h-2 rounded-full animate-pulse"
                    style={{ background: 'rgba(232,85,42,0.6)', animationDelay: `${i * 0.3}s` }} />
                  <span className="text-xs text-gray-600 font-mono">{agent.split(' ')[0]}</span>
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-500 mb-2">
              War room in progress — all 5 agents are analysing the data
            </p>
            <p className="text-xs text-gray-700 font-mono">
              This takes 2–3 minutes. Please keep this tab open.
            </p>
            <div className="mt-4 h-0.5 bg-white/5 rounded-full overflow-hidden mx-auto max-w-xs">
              <div className="h-full rounded-full animate-pulse"
                style={{ width: `${Math.min((elapsed / 150) * 100, 95)}%`, background: 'var(--kairos-orange)' }} />
            </div>
          </div>
        )}

        {/* Error state */}
        {status === 'error' && (
          <div className="card p-6 border-red-500/20 animate-fade-in">
            <p className="text-sm font-medium text-red-400 mb-2">War room failed</p>
            <p className="text-xs text-gray-500 font-mono">{errorMsg}</p>
            <button onClick={startWarRoom} className="mt-4 text-xs px-4 py-2 rounded-lg"
              style={{ background: 'rgba(232,85,42,0.15)', color: '#e8552a' }}>
              Retry
            </button>
          </div>
        )}

        {/* Idle state */}
        {status === 'idle' && (
          <div className="card p-16 text-center animate-fade-in">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center text-2xl mx-auto mb-6"
              style={{ background: 'rgba(232,85,42,0.1)', border: '1px solid rgba(232,85,42,0.2)' }}>⚡</div>
            <h2 className="font-display text-2xl text-white mb-3">Ready to launch</h2>
            <p className="text-gray-600 text-sm max-w-md mx-auto mb-8">
              5 AI agents will analyse the PurpleMerit SmartDash 2.0 launch data and produce
              a structured <span style={{ color: 'var(--kairos-orange)' }}>Proceed / Pause / Roll Back</span> decision.
              Takes about 2–3 minutes.
            </p>
            <button onClick={startWarRoom}
              className="px-8 py-3 rounded-xl text-sm font-medium transition-all hover:opacity-90"
              style={{ background: 'var(--kairos-orange)', color: 'white' }}>
              Start War Room
            </button>
          </div>
        )}

        {/* Complete — full results */}
        {status === 'complete' && decision && (
          <>
            {/* Decision banner */}
            <DecisionPanel
              decision={decision.decision}
              confidence={decision.confidence}
              tally={decision.session_stats?.verdict_tally}
              interpretation={decision.confidence?.interpretation}
            />

            {/* Agent cards + trace */}
            <div className="grid grid-cols-3 gap-6">
              <div className="col-span-2 space-y-3">
                <p className="text-xs font-mono text-gray-600 uppercase tracking-wider">Agent Verdicts</p>
                {agents.map(agent => (
                  <AgentCard key={agent.agent} agent={agent} isStreaming={false} />
                ))}
              </div>
              <div className="space-y-3">
                <p className="text-xs font-mono text-gray-600 uppercase tracking-wider">Session Trace</p>
                <TraceLog events={traceEvents} />
              </div>
            </div>

            {/* Metrics + risks + monitor */}
            <div className="grid grid-cols-2 gap-6">
              <MetricsChart />
              <div className="space-y-4">
                {decision.risk_register?.length > 0 && (
                  <RiskRegister risks={decision.risk_register} />
                )}
                <WarRoomMonitor sessionId={sessionId} />
              </div>
            </div>

            {/* Action plan */}
            {decision.action_plan && (
              <div className="card p-5 animate-fade-in">
                <p className="text-sm font-medium text-white mb-4">Action Plan</p>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    { key: 'immediate',  label: '🚨 Immediate',  color: '#ff3b3b' },
                    { key: 'within_24h', label: '⚡ Within 24h', color: '#f5a623' },
                    { key: 'within_48h', label: '📋 Within 48h', color: '#63b3ed' },
                  ].map(({ key, label, color }) => {
                    const actions = decision.action_plan[key] || []
                    return (
                      <div key={key}>
                        <p className="text-xs font-mono mb-2" style={{ color }}>{label}</p>
                        <div className="space-y-2">
                          {actions.length === 0
                            ? <p className="text-xs text-gray-700">—</p>
                            : actions.map((a, i) => (
                              <div key={i} className="card-2 px-3 py-2">
                                <p className="text-xs text-gray-300 leading-snug">{a.action}</p>
                                <p className="text-xs text-gray-600 mt-1 font-mono">{a.owner}</p>
                              </div>
                            ))
                          }
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Debate summary */}
            {decision.debate_summary?.tension && (
              <div className="card p-5 animate-fade-in">
                <p className="text-sm font-medium text-white mb-3">Debate Summary</p>
                <div className="space-y-2 text-xs">
                  <div className="flex gap-3">
                    <span className="text-gray-600 w-20 flex-shrink-0 font-mono">Tension</span>
                    <span className="text-gray-400">{decision.debate_summary.tension}</span>
                  </div>
                  <div className="flex gap-3">
                    <span className="text-gray-600 w-20 flex-shrink-0 font-mono">Ruling</span>
                    <span className="text-gray-400">{decision.debate_summary.ruling || decision.debate_summary.resolved_verdict}</span>
                  </div>
                  {decision.debate_summary.key_unresolved && (
                    <div className="flex gap-3">
                      <span className="text-gray-600 w-20 flex-shrink-0 font-mono">Open Q</span>
                      <span className="text-gray-500 italic">{decision.debate_summary.key_unresolved}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Comms plan */}
            {decision.communication_plan?.internal_message && (
              <div className="card p-5 animate-fade-in">
                <p className="text-sm font-medium text-white mb-3">Communication Plan</p>
                <div className="space-y-3">
                  {[
                    { label: 'Internal',    text: decision.communication_plan.internal_message,  color: '#9f7aea' },
                    { label: 'User-facing', text: decision.communication_plan.user_message,      color: '#63b3ed' },
                    { label: 'Enterprise',  text: decision.communication_plan.enterprise_message, color: '#f5a623' },
                  ].map(({ label, text, color }) => (
                    <div key={label} className="card-2 p-3">
                      <p className="text-xs font-mono mb-1" style={{ color }}>{label}</p>
                      <p className="text-xs text-gray-400 leading-relaxed">{text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  )
}