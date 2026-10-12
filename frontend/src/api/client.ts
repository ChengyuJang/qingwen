import axios, { AxiosError } from 'axios'

// Vite 代理：/api 会转发到后端 :8000
export const apiClient = axios.create({
  baseURL: '/api',
  timeout: 120_000, // 2 分钟（LLM 调用可能慢）
  headers: {
    'Content-Type': 'application/json',
  },
})

// ---------- 请求拦截器：自动带 token ----------
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ---------- 响应拦截器：401 自动清 token + 跳转 ----------
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // token 失效：清掉本地状态并跳登录
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

/** 从 axios 错误里提取后端 message */
export function extractErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { message?: string } | undefined
    if (data?.message) return data.message
    if (err.message) return err.message
  }
  return '未知错误'
}