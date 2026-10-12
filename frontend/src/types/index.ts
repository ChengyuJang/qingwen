// ---------- Auth ----------
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: number
  email: string
  is_active: boolean
  created_at: string
}

// ---------- 通用 API 错误格式（和后端统一异常格式对齐） ----------
export interface ApiError {
  code: number
  message: string
  detail?: unknown
}