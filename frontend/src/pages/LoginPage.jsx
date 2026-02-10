import { useState } from 'react'
import api, { setToken } from '../services/api'

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('owner@example.com')
  const [password, setPassword] = useState('Password123!')

  const submit = async (e) => {
    e.preventDefault()
    const form = new URLSearchParams({ username: email, password })
    const { data } = await api.post('/auth/login', form)
    setToken(data.access_token)
    onLogin(data.access_token)
  }

  return (
    <div className="max-w-md mx-auto mt-16 bg-white rounded-lg p-8 shadow">
      <h2 className="font-semibold text-xl mb-6">Login</h2>
      <form onSubmit={submit} className="space-y-4">
        <input className="w-full border p-2 rounded" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input className="w-full border p-2 rounded" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="bg-blue-700 text-white px-4 py-2 rounded">Sign in</button>
      </form>
    </div>
  )
}
