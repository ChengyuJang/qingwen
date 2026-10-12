import { Outlet } from 'react-router-dom'
import styles from './AuthLayout.module.css'

export default function AuthLayout() {
  return (
    <div className={styles.wrap}>
      <div className={styles.card}>
        <div className={styles.logo}>
          轻<span>问</span>
        </div>
        <div className={styles.sub}>Light Ask</div>
        <Outlet />
      </div>
    </div>
  )
}