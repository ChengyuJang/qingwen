import { Link } from 'react-router-dom'
import { Button } from '@/components'

export default function Home() {
  return (
    <div style={{ padding: '120px 56px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ fontSize: '11px', letterSpacing: '0.18em', color: 'var(--gold)', marginBottom: '32px' }}>
        AI 健身规划 AGENT
      </div>
      <h1
        style={{
          fontFamily: 'var(--font-serif)',
          fontSize: 'clamp(48px, 6vw, 88px)',
          fontWeight: 400,
          lineHeight: 1.12,
          letterSpacing: '-0.02em',
          marginBottom: '36px',
        }}
      >
        让减脂<em style={{ fontStyle: 'normal', color: 'var(--gold)' }}>轻</em>一点，
        <br />
        让改变<em style={{ fontStyle: 'normal', color: 'var(--gold)' }}>问</em>出来。
      </h1>
      <p
        style={{
          fontSize: '16px',
          lineHeight: 1.8,
          color: 'var(--muted)',
          maxWidth: '460px',
          fontWeight: 300,
          marginBottom: '48px',
        }}
      >
        不是又一份冷冰冰的卡路里表格。轻问通过对话理解你的节奏，生成会呼吸的饮食与训练规划。
      </p>
      <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
        <Link to="/chat">
          <Button variant="primary">开始你的规划 →</Button>
        </Link>
        <Link to="/login" style={{ color: 'var(--muted)', fontSize: '13px' }}>
          已有账号？登录
        </Link>
      </div>
    </div>
  )
}