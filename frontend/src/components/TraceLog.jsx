import React, { useEffect, useRef } from 'react'

const EVENT_STYLES = {
  session_start:    { color: '#63b3ed', prefix: 'SESSION' },
  phase_start:      { color: '#9f7aea', prefix: 'PHASE'   },
  agent_start:      { color: '#f5a623', prefix: 'AGENT'   },
  tool_call:        { color: '#4a5568', prefix: 'TOOL'    },
  agent_verdict:    { color: '#00d97e', prefix: 'VERDICT' },
  debate_start:     { color: '#ed8936', prefix: 'DEBATE'  },
  debate_resolved:  { color: '#ed8936', prefix: 'RULING'  },
  final_decision:   { color: '#ff3b3b', prefix: 'FINAL'   },
  complete:         { color: '#00d97e', prefix: 'DONE'    },
  error:            { color: '#ff3b3b', prefix: 'ERROR'   },
}

function formatEvent(event) {
  const d = event.data || {}
  switch (event.type) {
    case 'session_start':   return `War room started — session ${d.session_id}`
    case 'phase_start':     return `Phase ${d.number}: ${d.title}`
    case 'agent_start':     return `${d.agent} starting — tools: [${(d.tools||[]).join(', ')}]`
    case 'tool_call':       return `${d.tool}() → ${d.elapsed_ms}ms`
    case 'agent_verdict':   return `${d.agent} → ${d.verdict} (${d.confidence}/100)`
    case 'debate_start':    return 'Debate round beginning...'
    case 'debate_resolved': return `Moderator: ${d.resolved_verdict} (confidence ${d.resolved_confidence})`
    case 'final_decision':  return `FINAL: ${d.decision} — ${d.confidence}/100`
    case 'complete':        return `Session complete — reports written`
    case 'error':           return `Error: ${d.message}`
    default:                return JSON.stringify(d).slice(0, 80)
  }
}

export default function TraceLog({ events = [] }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events.length])

  return (
    <div className="card h-80 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5">
        <span className="text-xs font-mono text-gray-500 uppercase tracking-wider">Live Trace</span>
        <span className="text-xs font-mono text-gray-600">{events.length} events</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-xs">
        {events.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <span className="text-gray-700">Waiting for war room to start...</span>
          </div>
        )}

        {events.map((event, i) => {
          const style = EVENT_STYLES[event.type] || { color: '#718096', prefix: 'INFO' }
          const ts = event.timestamp
            ? new Date(event.timestamp).toLocaleTimeString('en-US', { hour12: false })
            : ''

          return (
            <div key={i} className="flex gap-2 items-baseline animate-fade-in">
              <span className="text-gray-700 flex-shrink-0 w-20">{ts}</span>
              <span
                className="flex-shrink-0 w-16 text-right"
                style={{ color: style.color }}
              >
                [{style.prefix}]
              </span>
              <span className="text-gray-400 truncate">{formatEvent(event)}</span>
            </div>
          )
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}