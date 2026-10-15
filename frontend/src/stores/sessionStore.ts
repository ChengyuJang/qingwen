import { create } from 'zustand'
import { fetchSessions, deleteSession, type Session } from '@/api/sessions'

interface SessionState {
  sessions: Session[]
  loading: boolean
  refresh: () => Promise<void>
  remove: (id: number) => Promise<void>
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  loading: false,

  refresh: async () => {
    set({ loading: true })
    try {
      const sessions = await fetchSessions()
      set({ sessions, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  remove: async (id) => {
    await deleteSession(id)
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
    }))
  },
}))