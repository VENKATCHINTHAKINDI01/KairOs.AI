import React, { useState, useRef, useEffect } from 'react'
import { askMonitor } from '../services/api'

const SUGGESTED = [
  'What did the Risk agent say about crash rate?',
  'Which agents voted ROLL_BACK?',
  'What are the immediate actions?',
  'What is the debate ruling?',
]

export default function WarRoomMonitor({ sessionId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (question) => {
    const q = question || input.trim()
    if (!q || !sessionId) return

    setMessages(m => [...m, { role: 'user', text: q }])
    setInput('')
    setLoading(true)

    try {
      const res = await askMonitor(sessionId, q)
      setMessages(m => [...m, { role: 'monitor', text: res.data.answer }])
    } catch (e) {
      setMessages(m => [...m, { role: 'error', text: 'Monitor unavailable. Run a war room first.' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card flex flex-col h-96">
      {/* Header */}
      <div className="px-4 py-3 border-b border-white/5 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
        <span className="text-sm font-medium text-white">War Room Monitor</span>
        {sessionId && (
          <span className="text-xs font-mono text-gray-600 ml-auto">{sessionId}</span>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-gray-600 mb-3">Ask anything about the war room session:</p>
            {SUGGESTED.map((s, i) => (
              <button
                key={i}
                onClick={() => send(s)}
                className="block w-full text-left text-xs text-gray-500 px-3 py-2 rounded-lg border border-white/5 hover:border-white/10 hover:text-gray-300 transition-all"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`animate-fade-in ${msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'}`}
          >
            <div
              className={`max-w-xs text-xs px-3 py-2 rounded-xl leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-orange-500/20 text-orange-100 border border-orange-500/20'
                  : msg.role === 'error'
                  ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                  : 'card-2 text-gray-300'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start animate-fade-in">
            <div className="card-2 px-3 py-2 flex gap-1">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t border-white/5 flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder={sessionId ? 'Ask about the session...' : 'Run a war room first...'}
          disabled={!sessionId || loading}
          className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-gray-300 placeholder-gray-700 focus:outline-none focus:border-orange-500/40 disabled:opacity-40"
        />
        <button
          onClick={() => send()}
          disabled={!input.trim() || !sessionId || loading}
          className="px-3 py-2 rounded-lg text-xs font-medium disabled:opacity-30 transition-all"
          style={{ background: 'rgba(232,85,42,0.2)', color: '#e8552a', border: '1px solid rgba(232,85,42,0.3)' }}
        >
          Ask
        </button>
      </div>
    </div>
  )
}