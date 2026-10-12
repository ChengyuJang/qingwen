import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { extractErrorMessage } from '@/api/client'
import { Button, Input, Label } from '@/components'

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
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <Label muted>邮箱</Label>
        <Input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
        />
      </div>
      <div>
        <Label muted>密码</Label>
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="至少 6 位"
          required
        />
      </div>

      {error && (
        <div style={{ fontSize: '13px', color: 'var(--error)' }}>{error}</div>
      )}

      <Button type="submit" variant="primary" block disabled={isLoading}>
        {isLoading ? '登录中…' : '登录'}
      </Button>

      <div style={{ textAlign: 'center', fontSize: '13px', color: 'var(--muted)' }}>
        还没账号？<a href="/register" style={{ color: 'var(--gold)' }}>注册</a>
      </div>
    </form>
  )
}