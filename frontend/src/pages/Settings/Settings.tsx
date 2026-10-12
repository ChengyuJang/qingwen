import { useNavigate } from 'react-router-dom'
import { LogOut, Mail, Calendar, Info, Shield } from 'lucide-react'
import { Badge, Button } from '@/components'
import { useAuthStore } from '@/stores/authStore'
import styles from './Settings.module.css'

export default function Settings() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

  function handleLogout() {
    if (!confirm('确定要退出登录吗？')) return
    logout()
    navigate('/login')
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.header}>
        <h1 className={styles.title}>设置</h1>
      </div>

      {/* ---------- 账户信息 ---------- */}
      <section className={styles.section}>
        <div className={styles.sectionLabel}>账户</div>
        <div className={styles.card}>
          <div className={styles.row}>
            <div className={styles.rowIcon}>
              <Mail size={16} />
            </div>
            <div className={styles.rowContent}>
              <div className={styles.rowLabel}>邮箱</div>
              <div className={styles.rowValue}>{user?.email || '—'}</div>
            </div>
          </div>

          <div className={styles.divider} />

          <div className={styles.row}>
            <div className={styles.rowIcon}>
              <Calendar size={16} />
            </div>
            <div className={styles.rowContent}>
              <div className={styles.rowLabel}>注册时间</div>
              <div className={styles.rowValue}>
                {user?.created_at ? formatDateTime(user.created_at) : '—'}
              </div>
            </div>
          </div>

          <div className={styles.divider} />

          <div className={styles.row}>
            <div className={styles.rowIcon}>
              <Shield size={16} />
            </div>
            <div className={styles.rowContent}>
              <div className={styles.rowLabel}>账户状态</div>
              <div className={styles.rowValue}>
                <Badge variant={user?.is_active ? 'sage' : 'error'}>
                  {user?.is_active ? '正常' : '已禁用'}
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- 安全（占位） ---------- */}
      <section className={styles.section}>
        <div className={styles.sectionLabel}>安全</div>
        <div className={styles.card}>
          <div className={styles.row}>
            <div className={styles.rowContent}>
              <div className={styles.rowLabel}>修改密码</div>
              <div className={styles.rowHint}>Phase 5 开放</div>
            </div>
            <Button variant="gold" disabled>
              即将推出
            </Button>
          </div>
        </div>
      </section>

      {/* ---------- 关于 ---------- */}
      <section className={styles.section}>
        <div className={styles.sectionLabel}>关于</div>
        <div className={styles.card}>
          <div className={styles.row}>
            <div className={styles.rowIcon}>
              <Info size={16} />
            </div>
            <div className={styles.rowContent}>
              <div className={styles.rowLabel}>轻问 · 你的健身规划 Agent</div>
              <div className={styles.rowHint}>版本 0.4.0 · 多 Agent 架构</div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------- 退出 ---------- */}
      <section className={styles.section}>
        <button className={styles.logoutBtn} onClick={handleLogout}>
          <LogOut size={14} />
          退出登录
        </button>
      </section>
    </div>
  )
}

function formatDateTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch {
    return iso
  }
}