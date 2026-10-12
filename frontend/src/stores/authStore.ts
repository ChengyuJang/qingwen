import { create } from 'zustand'
import { login as apiLogin, register as apiRegister, fetchMe } from '@/api/auth'
import type { User } from '@/types'

interface AuthState {
  user: User | null
  isLoading: boolean
  initialized: boolean

  // actions
  init: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: false,
  initialized: false,

  /** 应用启动时调用：如果有 token，拉一次 /auth/me */
  init: async () => {
    const token = localStorage.getItem('access_token')
    if (!token) {
      set({ initialized: true })
      return
    }
    try {
      const user = await fetchMe()
      set({ user, initialized: true })
    } catch {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, initialized: true })
    }
  },

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const tokens = await apiLogin({ email, password })
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      const user = await fetchMe()
      set({ user, isLoading: false })
    } catch (err) {
      set({ isLoading: false })
      throw err
    }
  },

  register: async (email, password) => {
    set({ isLoading: true })
    try {
      const tokens = await apiRegister({ email, password })
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      const user = await fetchMe()
      set({ user, isLoading: false })
    } catch (err) {
      set({ isLoading: false })
      throw err
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null })
  },

  setUser: (user) => set({ user }),
}))

/** 便于在非组件环境里读取 token */
export function getAccessToken(): string | null {
  return localStorage.getItem('access_token')
}