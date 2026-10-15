import { apiClient } from './client'

export interface Session {
  id: number
  thread_id: string
  title: string | null
  created_at: string
  updated_at: string
  last_message: string | null
}

export interface SessionMessage {
  id: number
  role: string
  agent: string | null
  content: string
  created_at: string
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await apiClient.get<Session[]>('/sessions')
  return res.data
}

export async function fetchSessionMessages(
  sessionId: number
): Promise<SessionMessage[]> {
  const res = await apiClient.get<SessionMessage[]>(
    `/sessions/${sessionId}/messages`
  )
  return res.data
}

export async function deleteSession(sessionId: number): Promise<void> {
  await apiClient.delete(`/sessions/${sessionId}`)
}