const WS_URL = 'ws://localhost:8000/api/v1/warroom/stream'

/**
 * Connect to the war room WebSocket stream.
 * Calls onEvent(event) for each message received.
 * Calls onClose() when the stream ends.
 * Returns a close() function to disconnect manually.
 */
export function connectWarRoomStream({ onEvent, onClose, onError }) {
  const ws = new WebSocket(WS_URL)

  ws.onopen = () => {
    console.log('[KairosAI] WebSocket connected — war room streaming...')
  }

  ws.onmessage = (msg) => {
    try {
      const event = JSON.parse(msg.data)
      onEvent(event)
    } catch (e) {
      console.error('[KairosAI] Failed to parse WS message:', e)
    }
  }

  ws.onerror = (err) => {
    console.error('[KairosAI] WebSocket error:', err)
    if (onError) onError(err)
  }

  ws.onclose = () => {
    console.log('[KairosAI] WebSocket closed')
    if (onClose) onClose()
  }

  return {
    close: () => ws.close(),
    send:  (data) => ws.send(JSON.stringify(data)),
  }
}