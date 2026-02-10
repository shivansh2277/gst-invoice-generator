import { useState } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import NewInvoicePage from './pages/NewInvoicePage'

export default function App() {
  const [token, setTokenState] = useState(localStorage.getItem('token'))

  const onLogin = (newToken) => {
    localStorage.setItem('token', newToken)
    setTokenState(newToken)
  }

  if (!token) {
    return <LoginPage onLogin={onLogin} />
  }

  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/invoices/new" element={<NewInvoicePage />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
