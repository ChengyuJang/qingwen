import { useCallback, useEffect, useRef, useState } from 'react'
import { API_BASE } from '@/api/client'

export interface AgentSegment {
  agent: string
  content: string
  tools: string[]
  finished: boolean
}

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
  // 关键：记录"已经处理过的 URL sessionId"，避免重复加载
  // 初始用 undefined 表示"从未处理"，不能初始化成 initialSessionId
  const handledSessionRef = useRef<number | null | undefined>(undefined)
    // 用于控制串行输出的状态
  const activeAgentRef = useRef<string | null>(null)
  const pendingTokensRef = useRef<Record<string, string[]>>({})
  const typingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  const newChat = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setSessionId(null)
    setStreaming(false)
    setStatus('')
    setError('')
  }, [])

  const loadHistory = useCallback(async (sid: number) => {
    abortRef.current?.abort()
    setMessages([])          // 立即清空，避免闪现
    setSessionId(sid)
    setError('')
    setStatus('')
    try {
      const token = localStorage.getItem('access_token')
      const res = await fetch(`${API_BASE}/sessions/${sid}/messages`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!res.ok) return
      const data = (await res.json()) as Array<{
        id: number
        role: string
        agent: string | null
        content: string
      }>
      // 把消息按"用户 → assistant 分段组"归并
      const msgs: ChatMessage[] = []

      for (const m of data) {
        if (m.role === 'user') {
          msgs.push({
            id: String(m.id),
            role: 'user',
            content: m.content,
            segments: [],
          })
        } else {
          // assistant：如果上一条也是 assistant，就追加 segment
          const last = msgs[msgs.length - 1]
          const segment: AgentSegment = {
            agent: m.agent || 'orchestrator',
            content: m.content,
            tools: [],
            finished: true,
          }
          if (last && last.role === 'assistant') {
            last.segments.push(segment)
          } else {
            msgs.push({
              id: String(m.id),
              role: 'assistant',
              content: '',
              segments: [segment],
            })
          }
        }
      }
      setMessages(msgs)
    } catch (e) {
      console.error('加载历史失败', e)
    }
  }, [])

  // 监听 URL 参数变化，但只处理"没处理过的"
  // 加"正在处理"标志，防止重入
  const processingRef = useRef(false)

  useEffect(() => {
    if (initialSessionId === handledSessionRef.current) return
    if (processingRef.current) return

    handledSessionRef.current = initialSessionId
    processingRef.current = true

    ;(async () => {
      try {
        if (initialSessionId) {
          await loadHistory(initialSessionId)
        } else {
          newChat()
        }
      } finally {
        processingRef.current = false
      }
    })()
  }, [initialSessionId, loadHistory, newChat])

    const startNextAgent = () => {
    activeAgentRef.current = null
    const nextAgent = Object.keys(pendingTokensRef.current).find(k => pendingTokensRef.current[k].length > 0)
    if (!nextAgent) return

    activeAgentRef.current = nextAgent
    const tokens = [...pendingTokensRef.current[nextAgent]]
    pendingTokensRef.current[nextAgent] = []

    let i = 0
    typingIntervalRef.current = setInterval(() => {
      // 检查播放过程中有没有新的真实 token 进来
      if (i >= tokens.length) {
        if (pendingTokensRef.current[nextAgent!] && pendingTokensRef.current[nextAgent!].length > 0) {
           tokens.push(...pendingTokensRef.current[nextAgent!])
           pendingTokensRef.current[nextAgent!] = []
        } else {
           clearInterval(typingIntervalRef.current!)
           typingIntervalRef.current = null
           activeAgentRef.current = null
           startNextAgent() // 递归找下一个
           return
        }
      }

      const d = tokens[i]
      i++
      setMessages((prev) =>
        prev.map((m) => {
          // 匹配正在流式输出的那条 assistant 消息
          if (m.role !== 'assistant' || m.segments.length === 0) return m
          const isLastMsg = prev[prev.length - 1].id === m.id
          if (!isLastMsg) return m

          const segments = [...m.segments]
          for (let j = segments.length - 1; j >= 0; j--) {
            if (segments[j].agent === nextAgent) {
              segments[j] = { ...segments[j], content: segments[j].content + d }
              break
            }
          }
          return { ...m, segments }
        })
      )
    }, 30) // 30ms 吐一个字
  }

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || streaming) return

      setError('')
      setStatus('正在连接…')
      setStreaming(true)

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

      const ac = new AbortController()
      abortRef.current = ac

      try {
        const token = localStorage.getItem('access_token')
        const resp = await fetch(`${API_BASE}/chat/stream`, {
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

            if (eventType === 'start') {
              const newSid = data.session_id as number
              setSessionId(newSid)
              handledSessionRef.current = newSid
              setStatus('')
            } else if (eventType === 'agent_start') {
              const agent = data.agent as string
              if (!pendingTokensRef.current[agent]) pendingTokensRef.current[agent] = []

              setMessages((prev) =>
                prev.map((m) => {
                  if (m.id !== assistantId) return m

                  const hasActiveSegment = m.segments.some(
                    (s) => s.agent === agent && !s.finished
                  )

                  if (hasActiveSegment) {
                    return m
                  }

                  return {
                    ...m,
                    segments: [...m.segments, { agent, content: '', tools: [], finished: false }]
                  }
                })
              )
              setStatus(agentLabel(agent) + ' 正在输入…')
            } else if (eventType === 'token') {
              const agent = data.agent as string
              const delta = data.delta as string

              if (!activeAgentRef.current) {
                activeAgentRef.current = agent
              }

              if (activeAgentRef.current !== agent || typingIntervalRef.current) {
                if (!pendingTokensRef.current[agent]) pendingTokensRef.current[agent] = []
                pendingTokensRef.current[agent].push(delta)
                continue
              }

              setMessages((prev) =>
                prev.map((m) => {
                  if (m.id !== assistantId) return m
                  const segments = [...m.segments]
                  for (let i = segments.length - 1; i >= 0; i--) {
                    if (segments[i].agent === agent) {
                      segments[i] = { ...segments[i], content: segments[i].content + delta }
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
                      segments[i] = { ...segments[i], tools: [...segments[i].tools, tool] }
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

              if (activeAgentRef.current === agent) {
                if (!typingIntervalRef.current) {
                  startNextAgent()
                }
              }
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
        // 清理打字机定时器
        if (typingIntervalRef.current) {
          clearInterval(typingIntervalRef.current)
          typingIntervalRef.current = null
        }
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