export default function Toast({ message, type = 'error' }) {
  if (!message) return null
  return (
    <div className={`fixed top-5 right-5 px-4 py-3 rounded shadow text-white ${type === 'error' ? 'bg-red-600' : 'bg-emerald-600'}`}>
      {message}
    </div>
  )
}
