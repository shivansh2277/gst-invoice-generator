import { Link } from 'react-router-dom'

export default function Layout({ children, highContrast, onToggleContrast }) {
  return (
    <div className={`min-h-screen ${highContrast ? 'contrast-mode' : ''}`}>
      <header className="bg-blue-700 text-white p-4 shadow">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="font-bold text-lg">GST Invoice Generator</h1>
          <nav className="space-x-4 text-sm">
            <Link to="/">Dashboard</Link>
            <Link to="/invoices/new">New Invoice</Link>
            <button type="button" className="ml-3 border border-white/60 rounded px-2 py-1" onClick={onToggleContrast} aria-label="Toggle high contrast mode">
              {highContrast ? 'Normal Mode' : 'High Contrast'}
            </button>
          </nav>
        </div>
      </header>
      <main className="max-w-6xl mx-auto p-4 md:p-6">{children}</main>
    </div>
  )
}
