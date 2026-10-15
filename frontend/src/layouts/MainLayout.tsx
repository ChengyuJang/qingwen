import { useEffect, useMemo } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { confirmAsync } from '@/stores/confirmStore'
import {
  MessageSquare,
  Calendar,
  LineChart,
  Activity,
  Settings as SettingsIcon,
  Plus,
  FileText,
  X,
} from 'lucide-react'

import { useAuthStore } from '@/stores/authStore'
import { useSessionStore } from '@/stores/sessionStore'
import styles from './MainLayout.module.css'

const NAV = [
  { to: '/chat', label: '对话', icon: MessageSquare },
  { to: '/plans', label: '我的规划', icon: Calendar },
  { to: '/logs', label: '训练日志', icon: Activity },
  { to: '/weight', label: '体重趋势', icon: LineChart },
  { to: '/reports', label: '报告中心', icon: FileText },
  { to: '/settings', label: '设置', icon: SettingsIcon },
]

export default function MainLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const sessions = useSessionStore((s) => s.sessions)
  const removeSession = useSessionStore((s) => s.remove)

  const current = NAV.find((n) => location.pathname.startsWith(n.to))


  // 当前高亮的 session id
  const currentSessionId = useMemo(() => {
    const p = new URLSearchParams(location.search)
    const v = p.get('session')
    return v ? Number(v) : null
  }, [location.search])

  // 挂载时拉一次会话列表
  useEffect(() => {
    useSessionStore.getState().refresh()
  }, [])

  return (
    <div className={styles.app}>
        <aside className={styles.sidebar}>
        <div className={styles.sidebarTop}>
          <NavLink to="/" className={styles.logo}>
            轻<span>问</span>
          </NavLink>
         <button
          type="button"
          className={styles.newChat}
          onClick={() => navigate('/chat')}
        >
          <Plus size={14} />
          <span>开启新对话</span>
        </button>

          <nav className={styles.nav}>
            {NAV.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === '/chat'}
                  className={({ isActive }) =>
                    `${styles.navItem} ${isActive && item.to !== '/chat' ? styles.active : ''} ${
                      item.to === '/chat' && location.pathname === '/chat' ? styles.active : ''
                    }`
                  }
                >
                  <Icon />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>
        </div>

        {sessions.length > 0 && (
          <>
            <div className={styles.recentLabel}>最近</div>
              <div className={styles.recentList}>
              {sessions.slice(0, 20).map((s) => (
                <div key={s.id} className={styles.recentItemWrap}>
                  <button
                    type="button"
                    className={`${styles.recentItem} ${
                      currentSessionId === s.id ? styles.recentItemActive : ''
                    }`}
                    onClick={() => navigate(`/chat?session=${s.id}`)}
                    title={s.title || s.last_message || '未命名对话'}
                  >
                    {s.title || s.last_message?.slice(0, 20) || '未命名对话'}
                  </button>
                  <button
                    type="button"
                    className={styles.recentDelete}
                    onClick={async (e) => {
                      e.stopPropagation()
                      const ok = await confirmAsync('删除这条对话？')
                      if (!ok) return
                      try {
                        await removeSession(s.id)
                        // 如果删除的是当前会话，跳回新对话
                        if (currentSessionId === s.id) {
                          navigate('/chat')
                        }
                      } catch {
                        // 静默失败
                      }
                    }}
                    title="删除"
                  >
                    <X size={12} />
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

        <div className={styles.user}>
          <div className={styles.avatar}>
            {user?.email ? user.email[0].toUpperCase() : '·'}
          </div>
          <div className={styles.userName}>{user?.email || '未登录'}</div>
        </div>
      </aside>

      <main className={styles.main}>
        <div className={styles.topbar}>
          <div className={styles.breadcrumb}>
            <span>轻问</span>
            <span className={styles.sep}>/</span>
            <span className={styles.breadcrumbCurrent}>
              {current?.label || '对话'}
            </span>
          </div>
        </div>

        <div className={styles.content}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}