import { useEffect, useMemo, useRef, useState } from 'react'
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react'
import styles from './DatePicker.module.css'

interface Props {
  value: string // YYYY-MM-DD
  onChange: (value: string) => void
  placeholder?: string
}

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

function toISO(y: number, m: number, d: number): string {
  return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

function parseISO(s: string): { y: number; m: number; d: number } | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s)
  if (!m) return null
  return { y: Number(m[1]), m: Number(m[2]) - 1, d: Number(m[3]) }
}

export default function DatePicker({ value, onChange, placeholder = '选择日期' }: Props) {
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)

  const today = useMemo(() => {
    const d = new Date()
    return { y: d.getFullYear(), m: d.getMonth(), d: d.getDate() }
  }, [])

  const selected = useMemo(() => parseISO(value), [value])

  // 显示哪个月份（打开时同步到选中日期的月份）
  const [viewYear, setViewYear] = useState(selected?.y ?? today.y)
  const [viewMonth, setViewMonth] = useState(selected?.m ?? today.m)

  useEffect(() => {
    if (open) {
      setViewYear(selected?.y ?? today.y)
      setViewMonth(selected?.m ?? today.m)
    }
  }, [open, selected, today])

  // 点击外部关闭
  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current?.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener('mousedown', onDocClick)
      return () => document.removeEventListener('mousedown', onDocClick)
    }
  }, [open])

  // 生成月视图格子
  const days = useMemo(() => {
    const firstDay = new Date(viewYear, viewMonth, 1)
    // 周一作为一周第一天：把 JS 的周日=0 转换
    let startWeekday = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1
    const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate()
    const prevMonthDays = new Date(viewYear, viewMonth, 0).getDate()

    const cells: Array<{ y: number; m: number; d: number; currentMonth: boolean }> = []

    // 上个月的尾部
    for (let i = startWeekday - 1; i >= 0; i--) {
      const d = prevMonthDays - i
      const m = viewMonth === 0 ? 11 : viewMonth - 1
      const y = viewMonth === 0 ? viewYear - 1 : viewYear
      cells.push({ y, m, d, currentMonth: false })
    }

    // 本月
    for (let d = 1; d <= daysInMonth; d++) {
      cells.push({ y: viewYear, m: viewMonth, d, currentMonth: true })
    }

    // 补足 6 行 × 7 列 = 42
    const remaining = 42 - cells.length
    for (let d = 1; d <= remaining; d++) {
      const m = viewMonth === 11 ? 0 : viewMonth + 1
      const y = viewMonth === 11 ? viewYear + 1 : viewYear
      cells.push({ y, m, d, currentMonth: false })
    }

    return cells
  }, [viewYear, viewMonth])

  function prevMonth() {
    if (viewMonth === 0) {
      setViewMonth(11)
      setViewYear((y) => y - 1)
    } else {
      setViewMonth((m) => m - 1)
    }
  }

  function nextMonth() {
    if (viewMonth === 11) {
      setViewMonth(0)
      setViewYear((y) => y + 1)
    } else {
      setViewMonth((m) => m + 1)
    }
  }

  function pick(y: number, m: number, d: number) {
    onChange(toISO(y, m, d))
    setOpen(false)
  }

  function pickToday() {
    pick(today.y, today.m, today.d)
  }

  function clear() {
    onChange('')
    setOpen(false)
  }

  const displayText = value || placeholder

  return (
    <div className={styles.wrap} ref={wrapRef}>
      <button
        type="button"
        className={`${styles.trigger} ${open ? styles.triggerOpen : ''}`}
        onClick={() => setOpen(!open)}
      >
        <Calendar size={14} />
        <span className={value ? styles.valueText : styles.placeholder}>
          {displayText}
        </span>
      </button>

      {open && (
        <div className={styles.panel}>
          {/* 头部：年月 + 上下月切换 */}
          <div className={styles.panelHeader}>
            <button type="button" className={styles.navBtn} onClick={prevMonth}>
              <ChevronLeft size={16} />
            </button>
            <div className={styles.monthLabel}>
              {viewYear} 年 {viewMonth + 1} 月
            </div>
            <button type="button" className={styles.navBtn} onClick={nextMonth}>
              <ChevronRight size={16} />
            </button>
          </div>

          {/* 星期表头 */}
          <div className={styles.weekdays}>
            {WEEKDAYS.map((w) => (
              <div key={w} className={styles.weekday}>
                {w}
              </div>
            ))}
          </div>

          {/* 日期格子 */}
          <div className={styles.days}>
            {days.map((cell, i) => {
              const isSelected =
                selected &&
                selected.y === cell.y &&
                selected.m === cell.m &&
                selected.d === cell.d
              const isToday =
                today.y === cell.y && today.m === cell.m && today.d === cell.d

              return (
                <button
                  key={i}
                  type="button"
                  className={[
                    styles.day,
                    !cell.currentMonth ? styles.dayMuted : '',
                    isToday ? styles.dayToday : '',
                    isSelected ? styles.daySelected : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                  onClick={() => pick(cell.y, cell.m, cell.d)}
                >
                  {cell.d}
                </button>
              )
            })}
          </div>

          {/* 底部操作 */}
          <div className={styles.panelFooter}>
            <button type="button" className={styles.footerBtn} onClick={clear}>
              清除
            </button>
            <button
              type="button"
              className={`${styles.footerBtn} ${styles.footerPrimary}`}
              onClick={pickToday}
            >
              今天
            </button>
          </div>
        </div>
      )}
    </div>
  )
}