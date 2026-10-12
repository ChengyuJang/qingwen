import styles from './MarkdownText.module.css'

interface Props {
  text: string
}

/**
 * 轻量 Markdown 渲染，专为专家输出设计。
 * 支持：
 * - 【标题】→ 小标题
 * - **加粗**
 * - - 列表
 * - 空行 → 段落分隔
 */
export default function MarkdownText({ text }: Props) {
  if (!text) return null

  const lines = text.split('\n')
  const blocks: Array<
    | { type: 'heading'; content: string }
    | { type: 'list'; items: string[] }
    | { type: 'para'; content: string }
  > = []

  let currentList: string[] = []

  function flushList() {
    if (currentList.length > 0) {
      blocks.push({ type: 'list', items: currentList })
      currentList = []
    }
  }

  for (const raw of lines) {
    const line = raw.trimEnd()
    const trimmed = line.trim()

    // 空行 → 结束当前列表
    if (!trimmed) {
      flushList()
      continue
    }

    // 【标题】
    const headingMatch = /^【(.+?)】$/.exec(trimmed)
    if (headingMatch) {
      flushList()
      blocks.push({ type: 'heading', content: headingMatch[1] })
      continue
    }

    // 列表项：- xxx / • xxx / · xxx
    const listMatch = /^[-•·]\s+(.+)$/.exec(trimmed)
    if (listMatch) {
      currentList.push(listMatch[1])
      continue
    }

    // 普通段落
    flushList()
    blocks.push({ type: 'para', content: line })
  }

  flushList()

  return (
    <div className={styles.wrap}>
      {blocks.map((block, i) => {
        if (block.type === 'heading') {
          return (
            <div key={i} className={styles.heading}>
              {block.content}
            </div>
          )
        }
        if (block.type === 'list') {
          return (
            <ul key={i} className={styles.list}>
              {block.items.map((item, j) => (
                <li key={j} className={styles.listItem}>
                  {renderInline(item)}
                </li>
              ))}
            </ul>
          )
        }
        return (
          <p key={i} className={styles.para}>
            {renderInline(block.content)}
          </p>
        )
      })}
    </div>
  )
}

/** 行内格式：**加粗** */
function renderInline(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className={styles.strong}>
          {part.slice(2, -2)}
        </strong>
      )
    }
    return <span key={i}>{part}</span>
  })
}