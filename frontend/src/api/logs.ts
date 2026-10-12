import { apiClient } from './client'

export interface DailyLog {
  id: number
  log_date: string
  trained: boolean
  training_note: string | null
  diet_note: string | null
  sleep_hours: number | null
  mood: string | null
  note: string | null
  created_at: string
}

export interface DailyLogInput {
  log_date: string
  trained: boolean
  training_note?: string | null
  diet_note?: string | null
  sleep_hours?: number | null
  mood?: string | null
  note?: string | null
}

export async function upsertLog(data: DailyLogInput): Promise<DailyLog> {
  const res = await apiClient.post<DailyLog>('/logs', data)
  return res.data
}

export async function fetchLogs(days = 30): Promise<DailyLog[]> {
  const res = await apiClient.get<DailyLog[]>('/logs', { params: { days } })
  return res.data
}

export async function deleteLog(id: number): Promise<void> {
  await apiClient.delete(`/logs/${id}`)
}