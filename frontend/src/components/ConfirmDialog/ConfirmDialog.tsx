import { createPortal } from 'react-dom'
import { useConfirmStore } from '@/stores/confirmStore'
import styles from './ConfirmDialog.module.css'

export default function ConfirmDialog() {
  const open = useConfirmStore((s) => s.open)
  const message = useConfirmStore((s) => s.message)
  const close = useConfirmStore((s) => s.close)

  if (!open) return null

  return createPortal(
    <div className={styles.overlay} onClick={() => close(false)}>
      <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
        <div className={styles.message}>{message}</div>
        <div className={styles.actions}>
          <button
            type="button"
            className={styles.cancelBtn}
            onClick={() => close(false)}
          >
            取消
          </button>
          <button
            type="button"
            className={styles.confirmBtn}
            onClick={() => close(true)}
          >
            确定
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}