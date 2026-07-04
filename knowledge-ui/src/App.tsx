import { Navigate, Route, Routes } from 'react-router-dom'
import AdminPage from './pages/AdminPage'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <Routes>
      <Route path="/admin" element={<AdminPage />} />
      <Route path="/chat/:slug" element={<ChatPage />} />
      <Route path="*" element={<Navigate to="/admin" replace />} />
    </Routes>
  )
}
