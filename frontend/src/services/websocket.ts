import { ref } from 'vue'
import type { TrainingTask } from '@/types'

type MessageHandler = (data: any) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private url: string = ''
  private reconnectInterval: number = 3000
  private reconnectTimer: number | null = null
  private handlers: Map<string, MessageHandler[]> = new Map()
  public connected = ref(false)

  connect(url: string) {
    this.url = url
    this.connectWebSocket()
  }

  private connectWebSocket() {
    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        console.log('WebSocket connected')
        this.connected.value = true
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer)
          this.reconnectTimer = null
        }
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.emit(data.type, data.data)
        } catch (error) {
          console.error('WebSocket message parse error:', error)
        }
      }

      this.ws.onclose = () => {
        console.log('WebSocket closed, reconnecting...')
        this.connected.value = false
        this.reconnectTimer = window.setTimeout(() => {
          this.connectWebSocket()
        }, this.reconnectInterval)
      }

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (error) {
      console.error('WebSocket connect error:', error)
      this.reconnectTimer = window.setTimeout(() => {
        this.connectWebSocket()
      }, this.reconnectInterval)
    }
  }

  on(event: string, handler: MessageHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, [])
    }
    this.handlers.get(event)!.push(handler)
  }

  off(event: string, handler: MessageHandler) {
    const handlers = this.handlers.get(event)
    if (handlers) {
      const index = handlers.indexOf(handler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  private emit(event: string, data: any) {
    const handlers = this.handlers.get(event)
    if (handlers) {
      handlers.forEach((handler) => handler(data))
    }
  }

  send(type: string, data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, data }))
    } else {
      console.warn('WebSocket not connected')
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.connected.value = false
  }
}

export const wsService = new WebSocketService()
