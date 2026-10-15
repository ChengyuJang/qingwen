import { FormEvent, useEffect, useState } from 'react'
import { Check, Dumbbell, Moon, Smile, Trash2 } from 'lucide-react'
import { Badge, Button, DatePicker, Input, Label, Textarea } from '@/components'
import { confirmAsync } from '@/stores/confirmStore'
import { fetchLogs, upsertLog, deleteLog, type DailyLog } from '@/api/logs'
import { extractErrorMessage } from '@/api/client'
import styles from './Logs.module.css'

const MOODS = [
  { value: 'great', label: '很棒', emoji: '😄' },
  { value: 'good', label: '不错', emoji: '😊' },
  { value: 'ok', label: '一般', emoji: '😐' },
  { value: 'bad', label: '不佳', emoji: '😕' },
  { value: 'awful', label: '糟透了', emoji: '😣' },
]

function todayISO(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

export default function Logs() {
  const [logs, setLogs] = useState<DailyLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  // 表单状态
  const [logDate, setLogDate] = useState(todayISO())
  const [trained, setTrained] = useState(false)
  const [trainingNote, setTrainingNote] = useState('')
  const [dietNote, setDietNote] = useState('')
  const [sleepHours, setSleepHours] = useState('')
  const [mood, setMood] = useState('good')
  const [note, setNote] = useState('')

  const todayLog = logs.find((l) => l.log_date.slice(0, 10) === todayISO())

  async function load() {
    setLoading(true)
    try {
      const data = await fetchLogs(30)
      setLogs(data)
    } catch (e) {
      setError(extractErrorMessage(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  // 如果今天已经有打卡，回填表单
  useEffect(() => {
    if (todayLog) {
      setTrained(todayLog.trained)
      setTrainingNote(todayLog.training_note || '')
      setDietNote(todayLog.diet_note || '')
      setSleepHours(todayLog.sleep_hours?.toString() || '')
      setMood(todayLog.mood || 'good')
      setNote(todayLog.note || '')
    }
  }, [todayLog])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    try {
      await upsertLog({
        log_date: `${logDate}T00:00:00Z`,
        trained,
        training_note: trainingNote.trim() || null,
        diet_note: dietNote.trim() || null,
        sleep_hours: sleepHours ? Number(sleepHours) : null,
        mood,
        note: note.trim() || null,
      })
      await load()
      // 重置非日期字段
      setTrainingNote('')
      setDietNote('')
      setSleepHours('')
      setNote('')
    } catch (err) {
      setError(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(id: number) {
    if (!(await confirmAsync('删除这条打卡？'))) return
    try {
      await deleteLog(id)
      setLogs((prev) => prev.filter((l) => l.id !== id))
    } catch (e) {
      setError(extractErrorMessage(e))
    }
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <h1 className={styles.title}>训练日志</h1>
        <p className={styles.sub}>每天 1 分钟，记录你的节奏</p>
      </div>

      {error && <div className={styles.error}>{error}</div>}

      {/* ---------- 打卡表单 ---------- */}
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.formHeader}>
          <div className={styles.formTitle}>
            {todayLog ? '今日已打卡 · 可更新' : '今日打卡'}
          </div>
          <div style={{ width: 160 }}>
            <DatePicker value={logDate} onChange={setLogDate} />
          </div>
        </div>

        {/* 训练开关 */}
        <div className={styles.row}>
          <button
            type="button"
            className={`${styles.toggle} ${trained ? styles.toggleOn : ''}`}
            onClick={() => setTrained(!trained)}
          >
            <Dumbbell size={14} />
            <span>{trained ? '今天训练了' : '今天没训练'}</span>
            {trained && <Check size={14} />}
          </button>
        </div>

        {/* 睡眠 */}
        <div className={styles.row}>
          <div className={styles.field}>
            <Label muted>
              <Moon size={11} style={{ display: 'inline', marginRight: 4 }} />
              睡眠时长（小时）
            </Label>
            <Input
              type="number"
              step="0.5"
              min="0"
              max="24"
              placeholder="7.5"
              value={sleepHours}
              onChange={(e) => setSleepHours(e.target.value)}
            />
          </div>

          <div className={styles.field}>
            <Label muted>
              <Smile size={11} style={{ display: 'inline', marginRight: 4 }} />
              今日心情
            </Label>
            <div className={styles.moodRow}>
              {MOODS.map((m) => (
                <button
                  key={m.value}
                  type="button"
                  className={`${styles.moodBtn} ${mood === m.value ? styles.moodActive : ''}`}
                  onClick={() => setMood(m.value)}
                  title={m.label}
                >
                  {m.emoji}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 训练备注 */}
        {trained && (
          <div className={styles.row}>
            <div className={styles.field}>
              <Label muted>训练内容</Label>
              <Input
                placeholder="例如：哑铃练腿 3 组深蹲"
                value={trainingNote}
                onChange={(e) => setTrainingNote(e.target.value)}
              />
            </div>
          </div>
        )}

        {/* 饮食备注 */}
        <div className={styles.row}>
          <div className={styles.field}>
            <Label muted>饮食备注</Label>
            <Input
              placeholder="例如：蛋白质摄入够了 / 今天吃多了"
              value={dietNote}
              onChange={(e) => setDietNote(e.target.value)}
            />
          </div>
        </div>

        {/* 自由备注 */}
        <div className={styles.row}>
          <div className={styles.field}>
            <Label muted>其他想说的</Label>
            <Textarea
              rows={2}
              placeholder="身体感受、情绪、任何想记录的…"
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
        </div>

        <div className={styles.formActions}>
          <Button type="submit" variant="primary" disabled={saving}>
            {saving ? '保存中…' : todayLog ? '更新今日打卡' : '提交打卡'}
          </Button>
        </div>
      </form>

      {/* ---------- 历史列表 ---------- */}
      <div className={styles.historyHeader}>
        <div className={styles.historyTitle}>最近 30 天</div>
        <div className={styles.historyCount}>{logs.length} 条</div>
      </div>

      {loading ? (
        <div className={styles.empty}>加载中…</div>
      ) : logs.length === 0 ? (
        <div className={styles.empty}>
          <div className={styles.emptyTitle}>还没有打卡记录</div>
          <div className={styles.emptySub}>从今天开始，记录每一天的节奏</div>
        </div>
      ) : (
        <div className={styles.list}>
          {logs.map((log) => (
            <LogCard key={log.id} log={log} onDelete={() => handleDelete(log.id)} />
          ))}
        </div>
      )}
    </div>
  )
}

// ---------- 单个历史卡片 ----------
function LogCard({ log, onDelete }: { log: DailyLog; onDelete: () => void }) {
  const moodData = MOODS.find((m) => m.value === log.mood)
  const date = new Date(log.log_date)
  const weekday = ['日', '一', '二', '三', '四', '五', '六'][date.getDay()]

  return (
    <div className={styles.logCard}>
      <div className={styles.logHeader}>
        <div className={styles.logDate}>
          <div className={styles.logDay}>
            {date.getMonth() + 1}/{date.getDate()}
          </div>
          <div className={styles.logWeekday}>周{weekday}</div>
        </div>
        <div className={styles.logBadges}>
          <Badge variant={log.trained ? 'sage' : 'outline'}>
            {log.trained ? '已训练' : '未训练'}
          </Badge>
          {moodData && <span className={styles.moodEmoji}>{moodData.emoji}</span>}
          {log.sleep_hours != null && (
            <span className={styles.sleepBadge}>💤 {log.sleep_hours}h</span>
          )}
        </div>
        <button className={styles.deleteBtn} onClick={onDelete} title="删除">
          <Trash2 size={13} />
        </button>
      </div>

      {(log.training_note || log.diet_note || log.note) && (
        <div className={styles.logBody}>
          {log.training_note && (
            <div className={styles.logItem}>
              <span className={styles.logLabel}>训练</span>
              {log.training_note}
            </div>
          )}
          {log.diet_note && (
            <div className={styles.logItem}>
              <span className={styles.logLabel}>饮食</span>
              {log.diet_note}
            </div>
          )}
          {log.note && (
            <div className={styles.logItem}>
              <span className={styles.logLabel}>备注</span>
              {log.note}
            </div>
          )}
        </div>
      )}
    </div>
  )
}