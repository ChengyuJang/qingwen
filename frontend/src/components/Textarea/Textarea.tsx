import { forwardRef, TextareaHTMLAttributes } from 'react'
import styles from './Textarea.module.css'

const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...rest }, ref) => {
  const classes = [styles.textarea, className || ''].filter(Boolean).join(' ')
  return <textarea ref={ref} className={classes} {...rest} />
})

Textarea.displayName = 'Textarea'
export default Textarea