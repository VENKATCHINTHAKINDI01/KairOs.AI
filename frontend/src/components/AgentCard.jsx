import React, { useState } from 'react'

const VERDICT_COLOR = {
  PROCEED:   '#00d97e',
  PAUSE:     '#f5a623',
  ROLL_BACK: '#ff3b3b',
}

const AGENT_ICONS = {
  'Data Analyst':      '📊',
  'Product Manager':   '🎯',
  'Marketing / Comms': '📣',
  'SRE / Engineering': '⚙️',
  'Risk / Critic':     '⚠️',
  'Debate Moderator':  '⚖️',
}

export default function AgentCard({ agent, isStreaming = false }) {
  const [expanded, setExpanded] = useState(false)

  const color = VERDICT_COLOR[agent.verdict] || '#888'
  const icon  = AGENT_ICONS[agent.agent] || '🤖'

  return (
    <div
      className="card p-4 cursor-pointer transition-all duration-200 hover:border-white/10 animate-slide-up"
      style={{ borderColor: isStreaming ? `${color}40` : 'rgba(255,255,255,0.07)' }}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Header row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl">{icon}</span>
          <div>
            <p className="text-sm font-medium text-white">{agent.agent}</p>
            {isStreaming && (
              <div className="flex items-center gap-1 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full animate-pulse" style={{ background: color }} />
                <span className="text-xs text-gray-500">processing...</span>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {agent.confidence && (
            <span className="text-xs font-mono text-gray-500">{agent.confidence}/100</span>
          )}
          {agent.verdict && (
            <span
              className="text-xs font-mono font-medium px-2 py-0.5 rounded"
              style={{ color, background: `${color}15`, border: `1px solid ${color}30` }}
            >
              {agent.verdict?.replace('_', ' ')}
            </span>
          )}
          <span className="text-gray-600 text-xs">{expanded ? '▲' : '▼'}</span>
        </div>
      </div>

      {/* Confidence bar */}
      {agent.confidence && (
        <div className="mt-3 h-0.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${agent.confidence}%`, background: color }}
          />
        </div>
      )}

      {/* Expanded — summary + findings */}
      {expanded && agent.summary && (
        <div className="mt-4 space-y-3 animate-fade-in">
          <p className="text-sm text-gray-400 leading-relaxed">{agent.summary}</p>

          {agent.key_findings?.length > 0 && (
            <div>
              <p className="text-xs font-mono text-gray-600 mb-2 uppercase tracking-wider">Key findings</p>
              <ul className="space-y-1">
                {agent.key_findings.map((f, i) => (
                  <li key={i} className="text-xs text-gray-400 flex gap-2">
                    <span style={{ color }} className="mt-0.5 flex-shrink-0">›</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}