import { forwardRef, InputHTMLAttributes } from 'react'
import styles from './Input.module.css'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ error = false, className, ...rest }, ref) => {
    const classes = [styles.input, error ? styles.error : '', className || '']
      .filter(Boolean)
      .join(' ')
    return <input ref={ref} className={classes} {...rest} />
  }
)

Input.displayName = 'Input'
export default Input