import { useEffect, useMemo, useState } from 'react'
import { FileText, Trash2 } from 'lucide-react'
import { Badge, Button, MarkdownText } from '@/components'
import { confirmAsync } from '@/stores/confirmStore'
import {
  fetchReports,
  generateReport,
  deleteReport,
  type Report,
} from '@/api/reports'
import { extractErrorMessage } from '@/api/client'
import styles from './Reports.module.css'

const KIND_LABELS: Record<string, string> = {
  weekly: '周报',
  monthly: '月报',
}

export default function Reports() {
  const [reports, setReports] = useState<Report[]>([])
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState<'weekly' | 'monthly' | null>(null)
  const [error, setError] = useState('')
  const [expanded, setExpanded] = useState<number | null>(null)
  const [filter, setFilter] = useState<'all' | 'weekly' | 'monthly'>('all')

  async function load() {
    setLoading(true)
    setError('')
    try {
      const data = await fetchReports({ limit: 50 })
      setReports(data)
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
  if (filter === 'all') return reports
  return reports.filter((r) => r.kind === filter)
}, [reports, filter])

  async function handleGenerate(kind: 'weekly' | 'monthly') {
    setGenerating(kind)
    setError('')
    try {
      const newReport = await generateReport(kind)
      setReports((prev) => [newReport, ...prev])
      setExpanded(newReport.id)
    } catch (e) {
      setError(extractErrorMessage(e))
    } finally {
      setGenerating(null)
    }
  }

  async function handleDelete(id: number) {
    if (!(await confirmAsync('删除这份报告？'))) return
    try {
      await deleteReport(id)
      setReports((prev) => prev.filter((r) => r.id !== id))
    } catch (e) {
      setError(extractErrorMessage(e))
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <div>
          <h1 className={styles.title}>报告中心</h1>
          <p className={styles.sub}>由报告生成师根据你的数据定期生成</p>
        </div>
        <div className={styles.actions}>
          <Button
            variant="gold"
            onClick={() => handleGenerate('weekly')}
            disabled={generating !== null}
          >
            {generating === 'weekly' ? '生成中…' : '生成本周报告'}
          </Button>
          <Button
            variant="primary"
            onClick={() => handleGenerate('monthly')}
            disabled={generating !== null}
          >
            {generating === 'monthly' ? '生成中…' : '生成本月报告'}
          </Button>
        </div>
      </div>

      {generating && (
        <div className={styles.tip}>
          <span className={styles.pulse} />
          报告生成中，大约需要 15-30 秒，请稍候…
        </div>
      )}

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.tabs}>
        {(['all', 'weekly', 'monthly'] as const).map((f) => (
          <button
            key={f}
            className={`${styles.tab} ${filter === f ? styles.tabActive : ''}`}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? '全部' : f === 'weekly' ? '周报' : '月报'}
            {f !== 'all' && (
              <span className={styles.count}>
                {filtered.filter((r) => r.kind === f).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <div className={styles.empty}>加载中…</div>
      ) : filtered.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyIcon}>
            <FileText size={32} strokeWidth={1.2} />
          </div>
          <div className={styles.emptyTitle}>还没有报告</div>
          <div className={styles.emptySub}>
            点击右上角按钮，让报告生成师为你的训练与生活节奏做一次回顾。
          </div>
        </div>
      ) : (
        <div className={styles.list}>
          {reports.map((r) => (
            <ReportCard
              key={r.id}
              report={r}
              expanded={expanded === r.id}
              onToggle={() => setExpanded(expanded === r.id ? null : r.id)}
              onDelete={() => handleDelete(r.id)}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function ReportCard({
  report,
  expanded,
  onToggle,
  onDelete,
}: {
  report: Report
  expanded: boolean
  onToggle: () => void
  onDelete: () => void
}) {
  const text = report.content?.text || ''
  const range = `${formatDay(report.period_start)} — ${formatDay(report.period_end)}`

  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.cardMeta}>
          <Badge variant={report.kind === 'monthly' ? 'gold' : 'sage'}>
            {KIND_LABELS[report.kind] || report.kind}
          </Badge>
          <span className={styles.range}>{range}</span>
          <span className={styles.date}>{formatTime(report.created_at)}</span>
        </div>
        <div className={styles.cardActions}>
          <button
            className={styles.actionBtn}
            onClick={onToggle}
            type="button"
          >
            {expanded ? '收起' : '展开全部'}
          </button>
          <button
            className={styles.deleteBtn}
            onClick={onDelete}
            title="删除"
            type="button"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {!expanded && (
        <div className={styles.summary} onClick={onToggle}>
          {report.summary || text.slice(0, 120)}
        </div>
      )}

      {expanded && (
        <div className={styles.body}>
          <MarkdownText text={text} />
        </div>
      )}
    </div>
  )
}

function formatDay(iso: string): string {
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function formatTime(iso: string): string {
  const d = new Date(iso)
  const now = new Date()
  const diff = (now.getTime() - d.getTime()) / 1000

  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} 天前`
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}