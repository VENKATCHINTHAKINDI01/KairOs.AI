import React from 'react'

const SEV_BADGE = {
  critical: 'badge-critical',
  high:     'badge-high',
  medium:   'badge-medium',
  low:      'badge-low',
}

export default function RiskRegister({ risks = [] }) {
  if (!risks.length) return null

  return (
    <div className="card overflow-hidden">
      <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
        <span className="text-sm font-medium text-white">Risk Register</span>
        <span className="text-xs font-mono text-gray-600">{risks.length} risks</span>
      </div>

      <div className="divide-y divide-white/5">
        {risks.map((risk, i) => (
          <div key={i} className="px-5 py-3 flex items-start gap-4 hover:bg-white/2 transition-colors">
            <span className={`text-xs font-mono px-2 py-0.5 rounded mt-0.5 flex-shrink-0 ${SEV_BADGE[risk.severity] || 'badge-low'}`}>
              {risk.severity?.toUpperCase()}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-200 leading-snug">{risk.risk}</p>
              <p className="text-xs text-gray-600 mt-1">
                <span className="text-gray-500">Mitigation: </span>{risk.mitigation}
              </p>
            </div>
            {risk.source_agent && (
              <span className="text-xs text-gray-700 flex-shrink-0 font-mono">{risk.source_agent?.split(' ')[0]}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}