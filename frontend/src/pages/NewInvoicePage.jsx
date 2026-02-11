import { useState } from 'react'
import api from '../services/api'

const emptyItem = { name: '', hsn_sac: '', quantity: 1, unit_price: 0, discount: 0, gst_rate: 18 }

export default function NewInvoicePage() {
  const [payload, setPayload] = useState({ seller_id: 1, buyer_id: 1, invoice_type: 'B2B', reverse_charge: false, items: [emptyItem] })

  const addItem = () => setPayload({ ...payload, items: [...payload.items, emptyItem] })

  const submit = async (e) => {
    e.preventDefault()
    await api.post('/invoices', payload)
    alert('Invoice created')
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h2 className="text-2xl font-semibold">Create Invoice</h2>
      {payload.items.map((item, idx) => (
        <div key={idx} className="grid grid-cols-6 gap-2 bg-white p-4 rounded shadow">
          <input className="border p-2 rounded" placeholder="Item" onChange={(e) => (item.name = e.target.value)} />
          <input className="border p-2 rounded" placeholder="HSN/SAC" onChange={(e) => (item.hsn_sac = e.target.value)} />
          <input className="border p-2 rounded" type="number" placeholder="Qty" onChange={(e) => (item.quantity = Number(e.target.value))} />
          <input className="border p-2 rounded" type="number" placeholder="Unit Price" onChange={(e) => (item.unit_price = Number(e.target.value))} />
          <input className="border p-2 rounded" type="number" placeholder="Discount" onChange={(e) => (item.discount = Number(e.target.value))} />
          <select className="border p-2 rounded" onChange={(e) => (item.gst_rate = Number(e.target.value))}>
            {[0, 5, 12, 18, 28, 40].map((r) => (
              <option key={r} value={r}>{r}%</option>
            ))}
          </select>
        </div>
      ))}
      <button type="button" onClick={addItem} className="bg-slate-600 text-white px-4 py-2 rounded mr-2">Add item</button>
      <button className="bg-blue-700 text-white px-4 py-2 rounded">Create</button>
    </form>
  )
}
