/**
 * KairosAI — Agent Redux Slice
 * Manages: per-agent status, verdict, confidence, findings
 */

let _agents = []
const _listeners = []

function notify() {
  _listeners.forEach(fn => fn(_agents))
}

export const agentStore = {
  getAgents: () => _agents,

  subscribe: (fn) => {
    _listeners.push(fn)
    return () => {
      const i = _listeners.indexOf(fn)
      if (i > -1) _listeners.splice(i, 1)
    }
  },

  addAgent: (name, tools = []) => {
    const exists = _agents.find(a => a.agent === name)
    if (!exists) {
      _agents = [..._agents, {
        agent:        name,
        tools,
        status:       'running',   // "running" | "done"
        verdict:      null,
        confidence:   null,
        summary:      null,
        key_findings: [],
        risks:        [],
      }]
      notify()
    }
  },

  updateVerdict: (name, { verdict, confidence, summary, key_findings, risks }) => {
    _agents = _agents.map(a =>
      a.agent === name
        ? { ...a, status: 'done', verdict, confidence, summary, key_findings: key_findings || [], risks: risks || [] }
        : a
    )
    notify()
  },

  reset: () => {
    _agents = []
    notify()
  },
}

export default agentStore