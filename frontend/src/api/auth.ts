import { apiClient } from './client'
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from '@/types'

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/auth/login', data)
  return res.data
}

export async function register(data: RegisterRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/auth/register', data)
  return res.data
}

export async function fetchMe(): Promise<User> {
  const res = await apiClient.get<User>('/auth/me')
  return res.data
}