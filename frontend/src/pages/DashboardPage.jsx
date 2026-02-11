import { useEffect, useState } from 'react'
import api from '../services/api'

export default function DashboardPage() {
  const [invoices, setInvoices] = useState([])

  useEffect(() => {
    api.get('/invoices').then((res) => setInvoices(res.data))
  }, [])

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-4">Invoices</h2>
      <div className="bg-white rounded shadow overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-200">
            <tr>
              <th className="p-3">Number</th>
              <th>Status</th>
              <th>Total</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((invoice) => (
              <tr key={invoice.id} className="border-t">
                <td className="p-3">{invoice.invoice_number}</td>
                <td>{invoice.status}</td>
                <td>₹{invoice.grand_total.toFixed(2)}</td>
                <td>{invoice.invoice_type}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
