import { useCallback, useRef, useState } from 'react'

/** 单个 Agent 在一条 assistant 消息里的分段 */
export interface AgentSegment {
  agent: string
  content: string
  tools: string[]
  finished: boolean
}

/** 一条消息：用户消息是纯文本，assistant 消息由多个 AgentSegment 组成 */
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  segments: AgentSegment[]
}

interface StreamState {
  messages: ChatMessage[]
  streaming: boolean
  status: string
  error: string
  sessionId: number | null
  sendMessage: (text: string) => Promise<void>
  newChat: () => void
  loadHistory: (sessionId: number) => Promise<void>
}

export function useChatStream(initialSessionId: number | null = null): StreamState {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streaming, setStreaming] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const [sessionId, setSessionId] = useState<number | null>(initialSessionId)
  const abortRef = useRef<AbortController | null>(null)

  const newChat = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setSessionId(null)
    setStreaming(false)
    setStatus('')
    setError('')
  }, [])

  const loadHistory = useCallback(async (sid: number) => {
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`/api/sessions/${sid}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) return
      const data = (await res.json()) as Array<{
        id: number
        role: string
        agent: string | null
        content: string
      }>
      const msgs: ChatMessage[] = data.map((m) => ({
        id: String(m.id),
        role: m.role as 'user' | 'assistant',
        content: m.role === 'user' ? m.content : '',
        segments:
          m.role === 'assistant'
            ? [
                {
                  agent: m.agent || 'orchestrator',
                  content: m.content,
                  tools: [],
                  finished: true,
                },
              ]
            : [],
      }))
      setMessages(msgs)
      setSessionId(sid)
    } catch (e) {
      console.error('加载历史失败', e)
    }
  }, [])

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || streaming) return

      setError('')
      setStatus('正在连接…')
      setStreaming(true)

      // 1) 立刻追加用户消息 + 空的 assistant 消息
      const userMsg: ChatMessage = {
        id: `u-${Date.now()}`,
        role: 'user',
        content: text,
        segments: [],
      }
      const assistantId = `a-${Date.now()}`
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        segments: [],
      }
      setMessages((prev) => [...prev, userMsg, assistantMsg])

      // 2) 创建 abort controller
      const ac = new AbortController()
      abortRef.current = ac

      try {
        const token = localStorage.getItem('access_token')
        const resp = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ message: text, session_id: sessionId }),
          signal: ac.signal,
        })

        if (!resp.ok) {
          const errBody = await resp.json().catch(() => ({}))
          throw new Error(errBody.message || `HTTP ${resp.status}`)
        }

        const reader = resp.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const blocks = buffer.split(/\r?\n\r?\n/)
          buffer = blocks.pop() || ''

          for (const block of blocks) {
            const lines = block.split(/\r?\n/)
            let eventType = ''
            let dataStr = ''
            for (const line of lines) {
              if (line.startsWith('event: ')) eventType = line.slice(7).trim()
              if (line.startsWith('data: ')) dataStr = line.slice(6)
            }
            if (!dataStr) continue

            let data: any
            try {
              data = JSON.parse(dataStr)
            } catch {
              continue
            }

            // 分发事件
            if (eventType === 'start') {
              setSessionId(data.session_id)
              setStatus('')
            } else if (eventType === 'agent_start') {
              const agent = data.agent as string
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? {
                        ...m,
                        segments: [
                          ...m.segments,
                          { agent, content: '', tools: [], finished: false },
                        ],
                      }
                    : m
                )
              )
              setStatus(agentLabel(agent) + ' 正在输入…')
            } else if (eventType === 'token') {
              const agent = data.agent as string
              const delta = data.delta as string
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.id !== assistantId) return m
                  const segments = [...m.segments]
                  // 找最后一个匹配 agent 的分段
                  for (let i = segments.length - 1; i >= 0; i--) {
                    if (segments[i].agent === agent) {
                      segments[i] = {
                        ...segments[i],
                        content: segments[i].content + delta,
                      }
                      break
                    }
                  }
                  return { ...m, segments }
                })
              )
            } else if (eventType === 'tool_call') {
              const agent = data.agent as string
              const tool = data.tool as string
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.id !== assistantId) return m
                  const segments = [...m.segments]
                  for (let i = segments.length - 1; i >= 0; i--) {
                    if (segments[i].agent === agent) {
                      segments[i] = {
                        ...segments[i],
                        tools: [...segments[i].tools, tool],
                      }
                      break
                    }
                  }
                  return { ...m, segments }
                })
              )
            } else if (eventType === 'agent_end') {
              const agent = data.agent as string
              setMessages((prev) =>
                prev.map((m) => {
                  if (m.id !== assistantId) return m
                  const segments = m.segments.map((s) =>
                    s.agent === agent ? { ...s, finished: true } : s
                  )
                  return { ...m, segments }
                })
              )
            } else if (eventType === 'end') {
              setStatus('')
            } else if (eventType === 'error') {
              setError(data.message || '生成失败')
            }
          }
        }
      } catch (e: any) {
        if (e.name !== 'AbortError') {
          setError(e.message || '请求失败')
        }
      } finally {
        setStreaming(false)
        setStatus('')
        abortRef.current = null
      }
    },
    [sessionId, streaming]
  )

  return { messages, streaming, status, error, sessionId, sendMessage, newChat, loadHistory }
}

export function agentLabel(agent: string): string {
  const map: Record<string, string> = {
    orchestrator: '轻问 · 协调者',
    intake: '信息采集',
    training: '训练专家',
    nutrition: '营养专家',
    recovery: '恢复专家',
  }
  return map[agent] || agent
}

export function agentVariant(agent: string): 'gold' | 'sage' | 'outline' | 'default' {
  const map: Record<string, 'gold' | 'sage' | 'outline' | 'default'> = {
    orchestrator: 'gold',
    intake: 'outline',
    training: 'sage',
    nutrition: 'gold',
    recovery: 'sage',
  }
  return map[agent] || 'default'
}