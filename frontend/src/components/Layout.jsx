import { Link } from 'react-router-dom'

export default function Layout({ children }) {
  return (
    <div className="min-h-screen">
      <header className="bg-blue-700 text-white p-4 shadow">
        <div className="max-w-5xl mx-auto flex justify-between">
          <h1 className="font-bold">GST Invoice Generator</h1>
          <nav className="space-x-4 text-sm">
            <Link to="/">Dashboard</Link>
            <Link to="/invoices/new">New Invoice</Link>
          </nav>
        </div>
      </header>
      <main className="max-w-5xl mx-auto p-6">{children}</main>
    </div>
  )
}
