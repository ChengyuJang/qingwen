import { apiClient } from './client'

export interface Report {
  id: number
  kind: string
  period_start: string
  period_end: string
  summary: string | null
  content: {
    stats: Record<string, unknown>
    text: string
  }
  created_at: string
}

export async function fetchReports(params?: {
  kind?: string
  limit?: number
}): Promise<Report[]> {
  const res = await apiClient.get<Report[]>('/reports', { params })
  return res.data
}

export async function generateReport(
  kind: 'weekly' | 'monthly' = 'weekly'
): Promise<Report> {
  const res = await apiClient.post<Report>('/reports/generate', { kind })
  return res.data
}

export async function deleteReport(id: number): Promise<void> {
  await apiClient.delete(`/reports/${id}`)
}