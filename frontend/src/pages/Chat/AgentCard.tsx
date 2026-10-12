import { Badge } from '@/components'
import type { AgentSegment } from '@/hooks/useChatStream'
import { agentLabel, agentVariant } from '@/hooks/useChatStream'
import styles from './AgentCard.module.css'

interface Props {
  segment: AgentSegment
}

export default function AgentCard({ segment }: Props) {
  // Orchestrator 输出：无卡片，直接文本
   if (segment.agent === 'orchestrator') {
    // 前端兜底：过滤掉 Orchestrator 的"收尾语"模式
    const text = segment.content || ''
    const isFiller =
      text.length < 40 &&
      /^(以上|希望|感谢|如需|如果|若|需要).{0,30}(参考|帮助|告知|随时|进一步|告诉我|为你|安排)/.test(
        text
      )

    if (isFiller || (!text && segment.finished)) {
      return null
    }
    if (!text && !segment.finished) {
      return null
    }
    return <div className={styles.orchestrator}>{text}</div>
  }
  // 专家输出：带徽章的卡片
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <Badge variant={agentVariant(segment.agent)}>{agentLabel(segment.agent)}</Badge>
        {segment.tools.map((tool, i) => (
          <Badge key={i} variant="outline">
            ⚙ {tool}
          </Badge>
        ))}
      </div>
      <div className={styles.content}>
        {renderContent(segment.content)}
        {!segment.finished && segment.content && <span className={styles.cursor}>▍</span>}
      </div>
    </div>
  )
}

function renderContent(text: string) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g)
    const rendered = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j}>{part.slice(2, -2)}</strong>
      }
      return <span key={j}>{part}</span>
    })
    if (line.trim().startsWith('- ') || line.trim().startsWith('• ')) {
      return (
        <div key={i} className={styles.listItem}>
          · {rendered}
        </div>
      )
    }
    return (
      <div key={i} className={styles.line}>
        {rendered || '\u00A0'}
      </div>
    )
  })
}