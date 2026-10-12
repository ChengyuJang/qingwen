import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import {
  MessageSquare,
  Calendar,
  LineChart,
  Activity,
  Settings as SettingsIcon,
  Plus,
} from 'lucide-react'
import styles from './MainLayout.module.css'

const NAV = [
  { to: '/chat', label: '对话', icon: MessageSquare },
  { to: '/plans', label: '我的规划', icon: Calendar },
  { to: '/logs', label: '训练日志', icon: Activity },
  { to: '/weight', label: '体重趋势', icon: LineChart },
  { to: '/settings', label: '设置', icon: SettingsIcon },
]

export default function MainLayout() {
  const location = useLocation()
  const current = NAV.find((n) => location.pathname.startsWith(n.to))
  const user = useAuthStore((s) => s.user)

  return (
    <div className={styles.app}>
      <aside className={styles.sidebar}>
        <NavLink to="/" className={styles.logo}>
          轻<span>问</span>
        </NavLink>

        <NavLink to="/chat" className={styles.newChat}>
          <Plus size={14} />
          <span>开启新对话</span>
        </NavLink>

        <nav className={styles.nav}>
          {NAV.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `${styles.navItem} ${isActive ? styles.active : ''}`
                }
              >
                <Icon />
                <span>{item.label}</span>
              </NavLink>
            )
          })}
        </nav>

        <div className={styles.spacer} />

        <div className={styles.user}>
          <div className={styles.avatar}>
            {user?.email ? user.email[0].toUpperCase() : '·'}
          </div>
          <div className={styles.userName}>
            {user?.email || '未登录'}
          </div>
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