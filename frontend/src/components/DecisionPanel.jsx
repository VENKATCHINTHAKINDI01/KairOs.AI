import React from 'react'

const VERDICT_CONFIG = {
  PROCEED:   { label: 'PROCEED',   icon: '✓', color: '#00d97e', glow: 'glow-green',  bg: 'rgba(0,217,126,0.08)'  },
  PAUSE:     { label: 'PAUSE',     icon: '⏸', color: '#f5a623', glow: '',            bg: 'rgba(245,166,35,0.08)' },
  ROLL_BACK: { label: 'ROLL BACK', icon: '↩', color: '#ff3b3b', glow: 'glow-red',    bg: 'rgba(255,59,59,0.08)'  },
}

export default function DecisionPanel({ decision, confidence, tally, interpretation }) {
  if (!decision) return null

  const cfg = VERDICT_CONFIG[decision] || VERDICT_CONFIG.PAUSE
  const score = confidence?.weighted_score ?? 0

  return (
    <div
      className={`card p-8 text-center ${cfg.glow} animate-fade-in`}
      style={{ borderColor: `${cfg.color}30`, background: cfg.bg }}
    >
      {/* Verdict */}
      <div className="flex items-center justify-center gap-4 mb-6">
        <span
          className="text-5xl font-display font-bold tracking-widest"
          style={{ color: cfg.color }}
        >
          {cfg.icon}
        </span>
        <h1
          className="text-4xl font-display tracking-widest"
          style={{ color: cfg.color }}
        >
          {cfg.label}
        </h1>
      </div>

      {/* Confidence bar */}
      <div className="max-w-sm mx-auto mb-6">
        <div className="flex justify-between text-xs text-gray-500 mb-1 font-mono">
          <span>CONFIDENCE</span>
          <span style={{ color: cfg.color }}>{score}/100</span>
        </div>
        <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-1000"
            style={{ width: `${score}%`, background: cfg.color }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-2">{interpretation}</p>
      </div>

      {/* Tally pills */}
      {tally && (
        <div className="flex justify-center gap-3 flex-wrap">
          {Object.entries(tally).map(([v, count]) => {
            const c = VERDICT_CONFIG[v]
            return (
              <span
                key={v}
                className="text-xs font-mono px-3 py-1 rounded-full"
                style={{
                  color:      c?.color || '#888',
                  background: `${c?.color || '#888'}15`,
                  border:     `1px solid ${c?.color || '#888'}30`,
                }}
              >
                {v.replace('_', ' ')}: {count}
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}