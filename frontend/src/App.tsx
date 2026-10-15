import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import AuthLayout from '@/layouts/AuthLayout'
import MainLayout from '@/layouts/MainLayout'
import Home from '@/pages/Home/Home'
import Login from '@/pages/Login/Login'
import Register from '@/pages/Register/Register'
import Chat from '@/pages/Chat/Chat'
import Plans from '@/pages/Plans/Plans'
import Logs from '@/pages/Logs/Logs'
import Weight from '@/pages/Weight/Weight'
import Settings from '@/pages/Settings/Settings'
import { useAuthStore } from '@/stores/authStore'
import { ConfirmDialog } from '@/components'
import Reports from '@/pages/Reports/Reports'

export default function App() {
  const init = useAuthStore((s) => s.init)

  useEffect(() => {
    init()
  }, [init])

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />

        <Route element={<AuthLayout />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>

        <Route element={<MainLayout />}>
          <Route path="/chat" element={<Chat />} />
          <Route path="/plans" element={<Plans />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/weight" element={<Weight />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/reports" element={<Reports />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ConfirmDialog />
    </BrowserRouter>
  )
}