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
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-200">
            <tr>
              <th className="p-3">Number</th>
              <th>Status</th>
              <th>Total</th>
              <th>Tax Mode</th>
              <th>Exports</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map((invoice) => (
              <tr key={invoice.id} className="border-t">
                <td className="p-3">{invoice.invoice_number}</td>
                <td>{invoice.status}</td>
                <td>₹{invoice.grand_total.toFixed(2)}</td>
                <td>{invoice.supply_type}</td>
                <td className="space-x-2">
                  <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/pdf`} target="_blank">PDF</a>
                  <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/json`} target="_blank">JSON</a>
                  <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/print`} target="_blank">Print</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
