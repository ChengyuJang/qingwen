import { HTMLAttributes, ReactNode } from 'react'
import styles from './Card.module.css'

type Variant = 'glass' | 'solid' | 'plain'

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: Variant
  clickable?: boolean
  children: ReactNode
}

export default function Card({
  variant = 'glass',
  clickable = false,
  className,
  children,
  ...rest
}: CardProps) {
  const classes = [
    styles.card,
    styles[variant],
    clickable ? styles.clickable : '',
    className || '',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className={classes} {...rest}>
      {children}
    </div>
  )
}