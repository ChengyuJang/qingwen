import { Badge } from '@/components'
import type { AgentSegment } from '@/hooks/useChatStream'
import { agentLabel, agentVariant } from '@/hooks/useChatStream'
import styles from './AgentCard.module.css'

interface Props {
  segment: AgentSegment
}

export default function AgentCard({ segment }: Props) {
  // Orchestrator 输出：轻量级纯文本样式
  if (segment.agent === 'orchestrator') {
    const text = segment.content || ''

    // 👇 兜底：如果全是空格或极短标点，直接抛弃
    if (!text.trim() || text.trim().length < 2) {
      return null
    }

    // 过滤掉无意义的收尾语
    const isFiller =
      text.length < 40 &&
      /^(以上|希望|感谢|如需|如果|若|需要).{0,30}(参考|帮助|告知|随时|进一步|告诉我|为你|安排)/.test(
        text
      )

    if (isFiller || (!text && segment.finished)) {
      return null
    }

    return (
      <div className={styles.orchestrator}>
        <div className={styles.orchestratorText}>
          {text}
          {!segment.finished && <span className={styles.cursor}>▍</span>}
        </div>
      </div>
    )
  }

  // 专家输出：带徽章的卡片
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <Badge variant={agentVariant(segment.agent)}>
          {agentLabel(segment.agent)}
        </Badge>
        {segment.tools.map((tool, i) => (
          <Badge key={i} variant="outline">
            ⚙ {tool}
          </Badge>
        ))}
      </div>
      <div className={styles.content}>
        {renderContent(segment.content)}
        {!segment.finished && segment.content && (
          <span className={styles.cursor}>▍</span>
        )}
      </div>
    </div>
  )
}

/** 简单的 markdown 渲染：支持 **加粗**、换行、- 列表 */
function renderContent(text: string) {
  if (!text) return null
  return text.split('\n').map((line, i) => {
    // 加粗
    const parts = line.split(/(\*\*[^*]+\*\*)/g)
    const rendered = parts.map((part, j) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={j}>{part.slice(2, -2)}</strong>
      }
      return <span key={j}>{part}</span>
    })

    // 列表项
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