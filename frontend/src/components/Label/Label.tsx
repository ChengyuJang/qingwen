import { LabelHTMLAttributes, ReactNode } from 'react'
import styles from './Label.module.css'

interface LabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
  muted?: boolean
  children: ReactNode
}

export default function Label({
  muted = false,
  className,
  children,
  ...rest
}: LabelProps) {
  const classes = [styles.label, muted ? styles.muted : '', className || '']
    .filter(Boolean)
    .join(' ')
  return (
    <label className={classes} {...rest}>
      {children}
    </label>
  )
}