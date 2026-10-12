import { HTMLAttributes, ReactNode } from 'react'
import styles from './Badge.module.css'

type Variant = 'default' | 'gold' | 'sage' | 'error' | 'outline'

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant
  children: ReactNode
}

export default function Badge({
  variant = 'default',
  className,
  children,
  ...rest
}: BadgeProps) {
  const classes = [styles.badge, styles[variant], className || '']
    .filter(Boolean)
    .join(' ')
  return (
    <span className={classes} {...rest}>
      {children}
    </span>
  )
}