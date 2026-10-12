import { apiClient } from './client'

export interface Plan {
  id: number
  session_id: number
  kind: string
  content: { text: string }
  summary: string | null
  created_at: string
}

export async function fetchPlans(params?: {
  kind?: string
  session_id?: number
  limit?: number
}): Promise<Plan[]> {
  const res = await apiClient.get<Plan[]>('/plans', { params })
  return res.data
}

export async function deletePlan(id: number): Promise<void> {
  await apiClient.delete(`/plans/${id}`)
}