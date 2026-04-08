import axios from 'axios'

// Always point at port 8000 regardless of which port Vite uses
const BASE = 'http://localhost:8000'

export const api = axios.create({
  baseURL: BASE,
  timeout: 300_000,   // 5 min — war room takes 2-3 min
})

export const runWarRoom = (monitorQuestion = null) =>
  api.post('/api/v1/warroom/run', { monitor_question: monitorQuestion })

export const askMonitor = (sessionId, question) =>
  api.post('/api/v1/monitor/ask', { session_id: sessionId, question })

export const getReport = (sessionId) =>
  api.get(`/api/v1/warroom/report/${sessionId}`)

export const listSessions = () =>
  api.get('/api/v1/warroom/sessions')

export const checkHealth = () =>
  api.get('/health')