import { forwardRef, InputHTMLAttributes, useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import Input from '../Input/Input'
import styles from './PasswordInput.module.css'

interface PasswordInputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  error?: boolean
}

const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(
  ({ error, className, ...rest }, ref) => {
    const [visible, setVisible] = useState(false)

    return (
      <div className={`${styles.wrap} ${className || ''}`}>
        <Input
          ref={ref}
          type={visible ? 'text' : 'password'}
          error={error}
          className={styles.input}
          {...rest}
        />
        <button
          type="button"
          className={styles.toggle}
          onClick={() => setVisible((v) => !v)}
          tabIndex={-1}
          aria-label={visible ? '隐藏密码' : '显示密码'}
          title={visible ? '隐藏密码' : '显示密码'}
        >
          {visible ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      </div>
    )
  }
)

PasswordInput.displayName = 'PasswordInput'
export default PasswordInput