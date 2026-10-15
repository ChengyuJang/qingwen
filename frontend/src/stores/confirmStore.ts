import { create } from 'zustand'

interface ConfirmState {
  open: boolean
  message: string
  resolve: ((v: boolean) => void) | null
  show: (message: string) => Promise<boolean>
  close: (result: boolean) => void
}

export const useConfirmStore = create<ConfirmState>((set, get) => ({
  open: false,
  message: '',
  resolve: null,

  show: (message) =>
    new Promise<boolean>((resolve) => {
      set({ open: true, message, resolve })
    }),

  close: (result) => {
    const { resolve } = get()
    resolve?.(result)
    set({ open: false, message: '', resolve: null })
  },
}))

/** 在任意非组件环境里调用 */
export const confirmAsync = (message: string): Promise<boolean> =>
  useConfirmStore.getState().show(message)