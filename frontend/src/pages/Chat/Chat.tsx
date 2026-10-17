import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { SendHorizontal } from 'lucide-react'
import { useChatStream } from '@/hooks/useChatStream'
import { useSessionStore } from '@/stores/sessionStore'
import AgentCard from './AgentCard'
import Welcome from './Welcome'
import styles from './Chat.module.css'

export default function Chat() {
  const [params, setParams] = useSearchParams()
  const initialSession = params.get('session') ? Number(params.get('session')) : null

  const {
    messages,
    streaming,
    status,
    error,
    sessionId,
    sendMessage,
    loadHistory,
    newChat,
  } = useChatStream(initialSession)

  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const scrollRef = useRef<HTMLDivElement>(null)

  // 新会话创建 → URL 同步 + 刷新侧边栏
  // 用 ref 记录"已同步过的 sessionId"，防重复触发
  const lastSyncedRef = useRef<number | null>(null)

  useEffect(() => {
    if (sessionId && sessionId !== lastSyncedRef.current) {
      lastSyncedRef.current = sessionId
      setParams({ session: String(sessionId) }, { replace: true })
      useSessionStore.getState().refresh()
    }
  }, [sessionId, setParams])

  // 自动滚动到底部
  useEffect(() => {
    const el = scrollRef.current
    if (el) {
      requestAnimationFrame(() => {
        el.scrollTop = el.scrollHeight
      })
    }
  }, [messages, status])

  // 自动调整 textarea 高度
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 140) + 'px'
  }, [input])

  const hasMessages = messages.length > 0

  async function handleSend() {
    const text = input.trim()
    if (!text || streaming) return
    setInput('')
    await sendMessage(text)
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.scroll} ref={scrollRef}>
        {!hasMessages ? (
          <Welcome onPick={(text) => setInput(text)} />
        ) : (
          <div className={styles.messages}>
            {messages.map((m) => {
              if (m.role === 'user') {
                return (
                  <div key={m.id} className={styles.userMsg}>
                    {m.content}
                  </div>
                )
              }
              const hasSpecialist = m.segments.some(
                (s) => s.agent !== 'orchestrator'
              )

              const visibleSegments = hasSpecialist
                ? m.segments.filter((s) => s.agent !== 'orchestrator')
                : m.segments

              return (
                <div key={m.id} className={styles.assistantGroup}>
                  {visibleSegments.map((seg, i) => (
                    <AgentCard key={i} segment={seg} />
                  ))}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {error && <div className={styles.error}>{error}</div>}
      {status && <div className={styles.status}>{status}</div>}

      <div className={styles.inputBar}>
        <div className={styles.inputWrap}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="说点什么…"
            rows={1}
            disabled={streaming}
          />
          <button
            className={styles.sendBtn}
            onClick={handleSend}
            disabled={!input.trim() || streaming}
            title="发送"
          >
            <SendHorizontal size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}