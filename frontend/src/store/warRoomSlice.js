/**
 * KairosAI — War Room Redux Slice
 * Manages: decision, confidence, action plan, debate summary, session stats
 * Note: We use simple useState in components instead of Redux for this project
 * since the state is local to the LaunchRoom page.
 * This file is kept for extensibility and future multi-page state sharing.
 */

// Simple state store using vanilla JS (no Redux dependency needed)
// Components import and use this directly if needed

const initialState = {
  sessionId:    null,
  decision:     null,       // "PROCEED" | "PAUSE" | "ROLL_BACK"
  confidence:   null,       // { weighted_score, interpretation, verdict_distribution }
  rationale:    null,
  riskRegister: [],
  actionPlan:   {},
  commsPlan:    {},
  debateSummary:{},
  sessionStats: {},
  reportPaths:  {},
  status:       'idle',     // "idle" | "running" | "complete" | "error"
}

let _state = { ...initialState }
const _listeners = []

function notify() {
  _listeners.forEach(fn => fn(_state))
}

export const warRoomStore = {
  getState: () => _state,

  subscribe: (fn) => {
    _listeners.push(fn)
    return () => {
      const i = _listeners.indexOf(fn)
      if (i > -1) _listeners.splice(i, 1)
    }
  },

  setStatus: (status) => {
    _state = { ..._state, status }
    notify()
  },

  setSessionId: (sessionId) => {
    _state = { ..._state, sessionId }
    notify()
  },

  setDecision: (decision) => {
    _state = { ..._state, ...decision, status: 'complete' }
    notify()
  },

  reset: () => {
    _state = { ...initialState }
    notify()
  },
}

export default warRoomStore