import styles from './MarkdownText.module.css'

interface Props {
  text: string
}

/**
 * 轻量 Markdown 渲染，兼容专家输出与报告两种格式：
 * - 【标题】 / ### 标题 / ## 标题 / # 标题
 * - - 无序列表 / 1. 有序列表
 * - **加粗**
 * - 空行分段
 */
export default function MarkdownText({ text }: Props) {
  if (!text) return null

  const lines = text.split('\n')
  type Block =
    | { type: 'heading'; content: string; level: 1 | 2 | 3 }
    | { type: 'list'; items: string[]; ordered: boolean }
    | { type: 'para'; content: string }

  const blocks: Block[] = []
  let currentList: string[] = []
  let currentOrdered = false

  function flushList() {
    if (currentList.length > 0) {
      blocks.push({ type: 'list', items: currentList, ordered: currentOrdered })
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

    // 【标题】 → 3 级标题
    const bracketMatch = /^【(.+?)】$/.exec(trimmed)
    if (bracketMatch) {
      flushList()
      blocks.push({ type: 'heading', content: bracketMatch[1], level: 3 })
      continue
    }

    // ### 标题 / ## 标题 / # 标题
    const mdHeading = /^(#{1,4})\s+(.+)$/.exec(trimmed)
    if (mdHeading) {
      flushList()
      const level = Math.min(mdHeading[1].length, 3) as 1 | 2 | 3
      blocks.push({ type: 'heading', content: mdHeading[2], level })
      continue
    }

    // 无序列表：- xxx / • xxx / · xxx
    const ulMatch = /^[-•·]\s+(.+)$/.exec(trimmed)
    if (ulMatch) {
      if (!currentOrdered && currentList.length > 0) {
        // 同类型列表，继续累积
      } else if (currentOrdered) {
        flushList()
        currentOrdered = false
      }
      currentList.push(ulMatch[1])
      continue
    }

    // 有序列表：1. xxx / 2. xxx
    const olMatch = /^(\d+)[.、]\s*(.+)$/.exec(trimmed)
    if (olMatch) {
      if (!currentOrdered && currentList.length > 0) {
        flushList()
        currentOrdered = true
      } else if (!currentOrdered && currentList.length === 0) {
        currentOrdered = true
      }
      currentList.push(olMatch[2])
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
          const cls =
            block.level === 1
              ? styles.heading1
              : block.level === 2
                ? styles.heading2
                : styles.heading3
          return (
            <div key={i} className={cls}>
              {renderInline(block.content)}
            </div>
          )
        }
        if (block.type === 'list') {
          return (
            <ul
              key={i}
              className={`${styles.list} ${block.ordered ? styles.listOrdered : ''}`}
            >
              {block.items.map((item, j) => (
                <li key={j} className={styles.listItem}>
                  {block.ordered ? (
                    <span className={styles.orderedIndex}>{j + 1}.</span>
                  ) : null}
                  <span>{renderInline(item)}</span>
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
/** 行内格式：**加粗** 和 [超链接](url) */
function renderInline(text: string) {
  // 匹配 **加粗** 或 [文字](链接)
  const parts = text.split(/(\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))/g)

  return parts.map((part, i) => {
    // 处理加粗
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className={styles.strong}>
          {part.slice(2, -2)}
        </strong>
      )
    }

    // 处理超链接
    const linkMatch = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(part)
    if (linkMatch) {
      return (
        <a key={i} href={linkMatch[2]} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--gold)', textDecoration: 'underline' }}>
          {linkMatch[1]}
        </a>
      )
    }

    return <span key={i}>{part}</span>
  })
}