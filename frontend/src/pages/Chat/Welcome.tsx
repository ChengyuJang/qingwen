import styles from './Welcome.module.css'

const SUGGESTIONS = [
  '帮我制定一份减脂计划',
  '我想练腿，只有一对哑铃',
  '每天该吃多少蛋白质',
  '昨晚只睡了 5 小时，今天还能练吗',
]

interface Props {
  onPick: (text: string) => void
}

export default function Welcome({ onPick }: Props) {
  return (
    <div className={styles.wrap}>
      <div className={styles.eyebrow}>A LITTLE LIGHTER</div>
      <h1 className={styles.title}>
        为下一次改变，
        <br />
        问得刚刚好。
      </h1>
      <p className={styles.sub}>
        说说你现在的状态和想去的方向。
        <br />
        不着急，轻问陪你慢慢排。
      </p>

      <div className={styles.mark}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <circle cx="10" cy="10" r="7" stroke="currentColor" strokeWidth="1.3" />
          <path d="M10 6v4l2.5 2" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
        </svg>
      </div>

      <div className={styles.question}>今天想聊什么？</div>

      <div className={styles.suggestions}>
        {SUGGESTIONS.map((s) => (
          <button key={s} onClick={() => onPick(s)}>
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}