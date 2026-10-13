import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { extractErrorMessage } from '@/api/client'
import { Button, Input, Label, PasswordInput } from '@/components'
import styles from './Login.module.css'

export default function Login() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const isLoading = useAuthStore((s) => s.isLoading)

  const [email, setEmail] = useState('test@qingwen.dev')
  const [password, setPassword] = useState('test123456')
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/chat')
    } catch (err) {
      setError(extractErrorMessage(err))
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <div className={styles.field}>
        <Label muted>邮箱</Label>
        <Input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          autoComplete="email"
        />
      </div>

      <div className={styles.field}>
        <Label muted>密码</Label>
        <PasswordInput
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="至少 6 位"
          autoComplete="current-password"
        />
      </div>

      {error && <div className={styles.formError}>{error}</div>}

      <Button type="submit" variant="primary" block disabled={isLoading} className={styles.submit}>
        {isLoading ? '登录中…' : '登录'}
      </Button>

      <div className={styles.bottom}>
        还没账号？<a href="/register" className={styles.link}>注册</a>
      </div>
    </form>
  )
}