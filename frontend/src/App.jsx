import { useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Toast from './components/Toast'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import NewInvoicePage from './pages/NewInvoicePage'

export default function App() {
  const [token, setTokenState] = useState(localStorage.getItem('token'))
  const [toast, setToast] = useState({ message: '', type: 'error' })
  const [highContrast, setHighContrast] = useState(localStorage.getItem('ui.highContrast') === '1')

  const notify = (message, type = 'error') => {
    setToast({ message, type })
    setTimeout(() => setToast({ message: '', type: 'error' }), 2500)
  }

  const onLogin = (newToken) => {
    localStorage.setItem('token', newToken)
    setTokenState(newToken)
    notify('Login successful', 'success')
  }

  const toggleContrast = () => {
    const next = !highContrast
    setHighContrast(next)
    localStorage.setItem('ui.highContrast', next ? '1' : '0')
  }

  if (!token) {
    return (
      <>
        <LoginPage onLogin={onLogin} />
        <Toast message={toast.message} type={toast.type} />
      </>
    )
  }

  return (
    <BrowserRouter>
      <Layout highContrast={highContrast} onToggleContrast={toggleContrast}>
        <Routes>
          <Route path="/" element={<DashboardPage notify={notify} />} />
          <Route path="/invoices/new" element={<NewInvoicePage notify={notify} />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
        <Toast message={toast.message} type={toast.type} />
      </Layout>
    </BrowserRouter>
  )
}
