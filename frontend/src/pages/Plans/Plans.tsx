import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Trash2 } from 'lucide-react'
import { Badge, Button, MarkdownText } from '@/components'
import { fetchPlans, deletePlan, type Plan } from '@/api/plans'
import { confirmAsync } from '@/stores/confirmStore'
import { extractErrorMessage } from '@/api/client'
import styles from './Plans.module.css'

const KIND_LABELS: Record<string, string> = {
  training: '训练',
  nutrition: '营养',
  recovery: '恢复',
  report: '报告',
}

const KIND_VARIANTS: Record<string, 'gold' | 'sage' | 'outline' | 'default'> = {
  training: 'sage',
  nutrition: 'gold',
  recovery: 'outline',
  report: 'default',
}

type Filter = 'all' | 'training' | 'nutrition' | 'recovery'

export default function Plans() {
  const [plans, setPlans] = useState<Plan[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filter, setFilter] = useState<Filter>('all')
  const [expanded, setExpanded] = useState<number | null>(null)

  async function load() {
    setLoading(true)
    setError('')
    try {
      const data = await fetchPlans({ limit: 100 })
      setPlans(data)
    } catch (e) {
      setError(extractErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    if (filter === 'all') return plans
    return plans.filter((p) => p.kind === filter)
  }, [plans, filter])

  const latestId = plans.length > 0 ? plans[0].id : null

  async function handleDelete(id: number) {
    if (!(await confirmAsync('删除这条规划？'))) return
    try {
      await deletePlan(id)
      setPlans((prev) => prev.filter((p) => p.id !== id))
    } catch (e) {
      setError(extractErrorMessage(e))
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>我的规划</h1>
          <p className={styles.sub}>由专家在对话中生成的训练、营养、恢复方案</p>
        </div>
      </div>

      <div className={styles.tabs}>
        {(['all', 'training', 'nutrition', 'recovery'] as Filter[]).map((f) => (
          <button
            key={f}
            className={`${styles.tab} ${filter === f ? styles.tabActive : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? '全部' : KIND_LABELS[f]}
            {f !== 'all' && (
              <span className={styles.count}>
                {plans.filter((p) => p.kind === f).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {loading ? (
        <div className={styles.empty}>加载中…</div>
      ) : filtered.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyTitle}>还没有规划</div>
          <div className={styles.emptySub}>
            去<Link to="/chat" className={styles.link}>对话页</Link>告诉轻问你的目标，
            专家会为你生成方案。
          </div>
          <Link to="/chat">
            <Button variant="primary">开启对话</Button>
          </Link>
        </div>
      ) : (
        <div className={styles.list}>
          {filtered.map((plan) => {
            const isExpanded = expanded === plan.id
            const text = plan.content?.text || ''
            return (
              <div key={plan.id} className={styles.card}>
                <div className={styles.cardHeader}>
                  <div className={styles.cardMeta}>
                    <Badge variant={KIND_VARIANTS[plan.kind] || 'default'}>
                      {KIND_LABELS[plan.kind] || plan.kind}
                    </Badge>
                    {plan.id === latestId && <Badge variant="gold">最新</Badge>}
                    <span className={styles.date}>
                      {formatDate(plan.created_at)}
                    </span>
                  </div>
                  <button
                    className={styles.deleteBtn}
                    onClick={() => handleDelete(plan.id)}
                    title="删除"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>

                <div
                  className={`${styles.content} ${isExpanded ? styles.contentExpanded : ''}`}
                  onClick={() => setExpanded(isExpanded ? null : plan.id)}
                >
                  <MarkdownText text={isExpanded ? text : truncate(text, 240)} />
                  {!isExpanded && text.length > 240 && (
                    <div className={styles.fadeMask} />
                  )}
                </div>

                <div className={styles.cardFooter}>
                  <Link
                    to={`/chat?session=${plan.session_id}`}
                    className={styles.sourceLink}
                  >
                    来源会话 →
                  </Link>
                  <button
                    className={styles.expandBtn}
                    onClick={() => setExpanded(isExpanded ? null : plan.id)}
                  >
                    {isExpanded ? '收起' : '展开全部'}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

function truncate(text: string, max: number): string {
  if (!text) return ''
  return text.length > max ? text.slice(0, max) + '…' : text
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diffH = (now.getTime() - d.getTime()) / 3_600_000
  if (diffH < 1) return '刚刚'
  if (diffH < 24) return `${Math.floor(diffH)} 小时前`
  if (diffH < 24 * 7) return `${Math.floor(diffH / 24)} 天前`
  return d.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
}