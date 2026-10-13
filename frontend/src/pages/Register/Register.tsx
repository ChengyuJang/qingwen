import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { extractErrorMessage } from '@/api/client'
import { Button, Input, Label, PasswordInput } from '@/components'
import styles from './Register.module.css'

export default function Register() {
  const navigate = useNavigate()
  const register = useAuthStore((s) => s.register)
  const isLoading = useAuthStore((s) => s.isLoading)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [fieldError, setFieldError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setFieldError('')

    // 字段校验
    if (!email.trim()) {
      setFieldError('请输入邮箱')
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setFieldError('邮箱格式不正确')
      return
    }
    if (password.length < 6) {
      setFieldError('密码至少 6 位')
      return
    }
    if (password !== confirm) {
      setFieldError('两次输入的密码不一致')
      return
    }

    try {
      await register(email, password)
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
          onChange={(e) => {
            setEmail(e.target.value)
            if (fieldError) setFieldError('')
          }}
          placeholder="you@example.com"
          error={!!fieldError}
          autoComplete="email"
        />
      </div>

      <div className={styles.field}>
        <Label muted>密码</Label>
        <PasswordInput
          value={password}
          onChange={(e) => {
            setPassword(e.target.value)
            if (fieldError) setFieldError('')
          }}
          placeholder="至少 6 位"
          error={!!fieldError}
          autoComplete="new-password"
        />
      </div>

      <div className={styles.field}>
        <Label muted>确认密码</Label>
        <PasswordInput
          value={confirm}
          onChange={(e) => {
            setConfirm(e.target.value)
            if (fieldError) setFieldError('')
          }}
          placeholder="再输一遍"
          error={!!fieldError}
          autoComplete="new-password"
        />
      </div>

      {fieldError && <div className={styles.fieldError}>{fieldError}</div>}
      {error && <div className={styles.formError}>{error}</div>}

      <Button
        type="submit"
        variant="primary"
        block
        disabled={isLoading}
        className={styles.submit}
      >
        {isLoading ? '注册中…' : '创建账号'}
      </Button>

      <div className={styles.bottom}>
        已有账号？<a href="/login" className={styles.link}>登录</a>
      </div>
    </form>
  )
}