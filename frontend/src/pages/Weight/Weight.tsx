import { FormEvent, useEffect, useMemo, useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { Trash2, TrendingDown, TrendingUp, Minus } from 'lucide-react'
import { Badge, Button, DatePicker, Input, Label } from '@/components'
import {
  fetchWeights,
  fetchTrend,
  upsertWeight,
  deleteWeight,
  type WeightRecord,
  type WeightTrendPoint,
} from '@/api/weight'
import { extractErrorMessage } from '@/api/client'
import styles from './Weight.module.css'

function todayISO(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export default function Weight() {
  const [records, setRecords] = useState<WeightRecord[]>([])
  const [trend, setTrend] = useState<WeightTrendPoint[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const [recordDate, setRecordDate] = useState(todayISO())
  const [weightInput, setWeightInput] = useState('')
  const [noteInput, setNoteInput] = useState('')
  const [fieldError, setFieldError] = useState('')

  async function load() {
    setLoading(true)
    try {
      const [recs, tr] = await Promise.all([fetchWeights(90), fetchTrend(90)])
      setRecords(recs)
      setTrend(tr)
    } catch (e) {
      setError(extractErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  // ---------- 统计 ----------
  const stats = useMemo(() => {
    if (records.length === 0) return null
    const sorted = [...records].sort(
      (a, b) => new Date(a.record_date).getTime() - new Date(b.record_date).getTime()
    )
    const latest = sorted[sorted.length - 1]
    const first = sorted[0]
    const change = latest.weight_kg - first.weight_kg

    // 7 天前的数据
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
    const recent7 = sorted.filter(
      (r) => new Date(r.record_date).getTime() >= sevenDaysAgo.getTime()
    )
    const weeklyChange =
      recent7.length >= 2 ? recent7[recent7.length - 1].weight_kg - recent7[0].weight_kg : null

    return {
      latest: latest.weight_kg,
      totalChange: change,
      weeklyChange,
    }
  }, [records])

  // ---------- 图表数据（带格式化日期） ----------
  const chartData = useMemo(
    () =>
      trend.map((p) => ({
        ...p,
        label: formatShortDate(p.record_date),
        display: `${p.record_date.slice(5, 10)}`,
      })),
    [trend]
  )

async function handleSubmit(e: FormEvent) {
  e.preventDefault()

  // 字段级校验
  if (!weightInput.trim()) {
    setFieldError('请输入体重')
    return
  }
  const w = Number(weightInput)
  if (!w || w <= 0 || w > 500) {
    setFieldError('请输入有效体重（0-500 kg）')
    return
  }

  setFieldError('')
  setSaving(true)
  setError('')
    try {
      await upsertWeight({
        record_date: `${recordDate}T00:00:00Z`,
        weight_kg: w,
        note: noteInput.trim() || null,
      })
      await load()
      setWeightInput('')
      setNoteInput('')
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('删除这条记录？')) return
    try {
      await deleteWeight(id)
      setRecords((prev) => prev.filter((r) => r.id !== id))
      setTrend((prev) => prev)  // 简单起见不动图表，刷新页面会重新加载
      await load()
    } catch (e) {
      setError(extractErrorMessage(e))
    }
  }

  // 计算 y 轴范围（留一点 padding）
  const yDomain = useMemo(() => {
    if (chartData.length === 0) return [60, 80]
    const values = chartData.map((d) => d.weight_kg)
    const min = Math.min(...values)
    const max = Math.max(...values)
    const pad = Math.max((max - min) * 0.2, 1)
    return [Math.floor(min - pad), Math.ceil(max + pad)]
  }, [chartData])

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <h1 className={styles.title}>体重趋势</h1>
        <p className={styles.sub}>体重只是噪音，趋势才是信号</p>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {/* ---------- 统计卡 ---------- */}
      {stats && (
        <div className={styles.statsRow}>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>当前体重</div>
            <div className={styles.statValue}>
              {stats.latest.toFixed(1)}
              <span className={styles.statUnit}>kg</span>
            </div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>近 7 天</div>
            <div className={`${styles.statValue} ${changeColor(stats.weeklyChange)}`}>
              {formatChange(stats.weeklyChange)}
              <span className={styles.statUnit}>kg</span>
            </div>
          </div>
          <div className={styles.statCard}>
            <div className={styles.statLabel}>记录至今</div>
            <div className={`${styles.statValue} ${changeColor(stats.totalChange)}`}>
              {formatChange(stats.totalChange)}
              <span className={styles.statUnit}>kg</span>
            </div>
          </div>
        </div>
      )}

      {/* ---------- 图表 ---------- */}
      <div className={styles.chartCard}>
        {chartData.length === 0 ? (
          <div className={styles.chartEmpty}>还没有记录，从下方开始记录第一条吧</div>
        ) : (
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData} margin={{ top: 20, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid stroke="rgba(28,28,30,0.06)" vertical={false} />
              <XAxis
                dataKey="display"
                tick={{ fill: '#8C8279', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                interval="preserveStartEnd"
              />
              <YAxis
                domain={yDomain}
                tick={{ fill: '#8C8279', fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                width={40}
                tickFormatter={(v) => `${v}`}
              />
              <Tooltip
                contentStyle={{
                  background: 'rgba(255,255,255,0.95)',
                  border: '1px solid rgba(201,169,110,0.3)',
                  borderRadius: 12,
                  fontSize: 13,
                  padding: '8px 14px',
                  boxShadow: '0 8px 24px rgba(28,28,30,0.08)',
                }}
                labelStyle={{ color: '#8C8279', fontSize: 11, marginBottom: 4 }}
                formatter={(value: number) => [`${value} kg`, '体重']}
              />
              {/* 平均值参考线 */}
              <ReferenceLine
                y={
                  chartData.reduce((s, d) => s + d.weight_kg, 0) / chartData.length
                }
                stroke="rgba(201,169,110,0.4)"
                strokeDasharray="4 4"
                label={{
                  value: '平均',
                  position: 'right',
                  fill: '#C9A96E',
                  fontSize: 10,
                }}
              />
              <Line
                type="monotone"
                dataKey="weight_kg"
                stroke="#C9A96E"
                strokeWidth={2}
                dot={{ r: 3, fill: '#C9A96E', strokeWidth: 0 }}
                activeDot={{ r: 5, fill: '#C9A96E' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ---------- 记录表单 ---------- */}
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.formRow}>
          <div className={styles.field}>
            <Label muted>日期</Label>
            <DatePicker value={recordDate} onChange={setRecordDate} />
          </div>
          <div className={styles.field}>
            <Label muted>体重（kg）</Label>
            <Input
              type="number"
              step="0.1"
              min="0"
              max="500"
              placeholder="70.0"
              value={weightInput}
              onChange={(e) => {
                setWeightInput(e.target.value)
                if (fieldError) setFieldError('')
              }}
              error={!!fieldError}
            />
            {fieldError && (
              <div className={styles.fieldError}>{fieldError}</div>
            )}
          </div>
          <div className={styles.field + ' ' + styles.fieldWide}>
            <Label muted>备注（可选）</Label>
            <Input
              placeholder="例如：空腹测量"
              value={noteInput}
              onChange={(e) => setNoteInput(e.target.value)}
            />
          </div>
          <div className={styles.fieldButton}>
            <Label muted style={{ visibility: 'hidden' }}>占位</Label>
            <Button
              className={styles.recordBtn}
              type="submit"
              variant="primary"
              disabled={saving}
            >
              {saving ? '保存中…' : '记录'}
            </Button>
          </div>
        </div>
      </form>

      {/* ---------- 历史记录 ---------- */}
      <div className={styles.historyHeader}>
        <div className={styles.historyTitle}>历史记录</div>
        <div className={styles.historyCount}>{records.length} 条</div>
      </div>

      {loading ? (
        <div className={styles.empty}>加载中…</div>
      ) : records.length === 0 ? (
        <div className={styles.empty}>还没有记录</div>
      ) : (
        <div className={styles.list}>
          {records.map((r) => (
            <div key={r.id} className={styles.recordCard}>
              <div className={styles.recordDate}>{r.record_date.slice(0, 10)}</div>
              <div className={styles.recordValue}>{r.weight_kg.toFixed(1)} kg</div>
              {r.note && <div className={styles.recordNote}>{r.note}</div>}
              <button
                className={styles.deleteBtn}
                onClick={() => handleDelete(r.id)}
                title="删除"
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function formatChange(v: number | null): string {
  if (v == null) return '—'
  const sign = v > 0 ? '+' : ''
  return `${sign}${v.toFixed(1)}`
}

function changeColor(v: number | null): string {
  if (v == null) return ''
  if (v > 0.05) return styles.changeUp
  if (v < -0.05) return styles.changeDown
  return styles.changeFlat
}

function formatShortDate(iso: string): string {
  return iso.slice(5, 10)
}