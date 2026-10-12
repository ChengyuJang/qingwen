import { apiClient } from './client'

export interface WeightRecord {
  id: number
  record_date: string
  weight_kg: number
  note: string | null
  created_at: string
}

export interface WeightTrendPoint {
  record_date: string
  weight_kg: number
}

export async function fetchWeights(days = 90): Promise<WeightRecord[]> {
  const res = await apiClient.get<WeightRecord[]>('/weight', { params: { days } })
  return res.data
}

export async function fetchTrend(days = 90): Promise<WeightTrendPoint[]> {
  const res = await apiClient.get<WeightTrendPoint[]>('/weight/trend', {
    params: { days },
  })
  return res.data
}

export async function upsertWeight(data: {
  record_date: string
  weight_kg: number
  note?: string | null
}): Promise<WeightRecord> {
  const res = await apiClient.post<WeightRecord>('/weight', data)
  return res.data
}

export async function deleteWeight(id: number): Promise<void> {
  await apiClient.delete(`/weight/${id}`)
}