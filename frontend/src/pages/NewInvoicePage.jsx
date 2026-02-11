import { useEffect, useMemo, useState } from 'react'
import api from '../services/api'

const hsnRegex = /^\d{4,8}$/
const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$/
const emptyItem = { name: '', hsn_code: '', quantity: 1, unit_price: 0, discount: 0, gst_rate: 18 }

const q = (n) => Math.round((Number(n) + Number.EPSILON) * 100) / 100

export default function NewInvoicePage({ notify }) {
  const [sellers, setSellers] = useState([])
  const [buyers, setBuyers] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [invoice, setInvoice] = useState(null)
  const [payload, setPayload] = useState({ seller_id: 0, buyer_id: 0, invoice_type: 'B2B', reverse_charge: false, export_flag: false, composition_flag: false, items: [{ ...emptyItem }] })

  useEffect(() => {
    Promise.all([api.get('/sellers'), api.get('/buyers')]).then(([s, b]) => {
      setSellers(s.data)
      setBuyers(b.data)
      setPayload((p) => ({ ...p, seller_id: s.data[0]?.id || 0, buyer_id: b.data[0]?.id || 0 }))
    })
  }, [])

  const seller = sellers.find((s) => s.id === Number(payload.seller_id))
  const buyer = buyers.find((b) => b.id === Number(payload.buyer_id))
  const taxMode = payload.export_flag ? 'zero' : seller && buyer && seller.state_code === buyer.state_code ? 'cgst+sgst' : 'igst'

  const preview = useMemo(() => {
    const lines = payload.items.map((item) => {
      const taxable = q(q(item.quantity) * q(item.unit_price) - q(item.discount))
      const tax = payload.composition_flag || payload.export_flag ? 0 : q((taxable * q(item.gst_rate)) / 100)
      return { taxable, tax, total: q(taxable + tax) }
    })
    const totalTaxable = q(lines.reduce((s, l) => s + l.taxable, 0))
    const totalTax = q(lines.reduce((s, l) => s + l.tax, 0))
    return { totalTaxable, totalTax, grandTotal: q(totalTaxable + totalTax) }
  }, [payload])

  const updateItem = (idx, key, value) => {
    setPayload((p) => {
      const items = [...p.items]
      items[idx] = { ...items[idx], [key]: value }
      return { ...p, items }
    })
  }

  const addItem = () => setPayload((p) => ({ ...p, items: [...p.items, { ...emptyItem }] }))

  const onHsnChange = async (idx, value) => {
    updateItem(idx, 'hsn_code', value)
    if (value.length >= 2) {
      try {
        const { data } = await api.get('/hsn', { params: { q: value } })
        setSuggestions(data)
      } catch {
        setSuggestions([])
      }
    }
  }

  const submit = async (e) => {
    e.preventDefault()
    try {
      const headers = { 'Idempotency-Key': crypto.randomUUID() }
      const { data } = await api.post('/invoices', payload, { headers })
      setInvoice(data)
      notify('Invoice created', 'success')
    } catch (err) {
      notify(err?.response?.data?.detail || 'Failed to create invoice')
    }
  }

  const finalize = async () => {
    if (!invoice) return
    try {
      const { data } = await api.post(`/invoices/${invoice.id}/finalize`)
      setInvoice(data)
      notify('Invoice finalized', 'success')
    } catch (err) {
      notify(err?.response?.data?.detail || 'Finalize failed')
    }
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <h2 className="text-2xl font-semibold">Create Invoice</h2>

      <div className="bg-white p-4 rounded shadow grid grid-cols-3 gap-4">
        <select className="border p-2 rounded" value={payload.seller_id} onChange={(e) => setPayload({ ...payload, seller_id: Number(e.target.value) })}>
          {sellers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select className="border p-2 rounded" value={payload.buyer_id} onChange={(e) => setPayload({ ...payload, buyer_id: Number(e.target.value) })}>
          {buyers.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <select className="border p-2 rounded" value={payload.invoice_type} onChange={(e) => setPayload({ ...payload, invoice_type: e.target.value })}>
          <option>B2B</option>
          <option>B2C</option>
        </select>
        <label><input type="checkbox" checked={payload.reverse_charge} onChange={(e) => setPayload({ ...payload, reverse_charge: e.target.checked })} /> Reverse Charge</label>
        <label><input type="checkbox" checked={payload.export_flag} onChange={(e) => setPayload({ ...payload, export_flag: e.target.checked })} /> Export</label>
        <label><input type="checkbox" checked={payload.composition_flag} onChange={(e) => setPayload({ ...payload, composition_flag: e.target.checked })} /> Composition</label>
      </div>

      <div className="bg-white p-4 rounded shadow text-sm">
        <div>Seller GSTIN: <span className={gstinRegex.test(seller?.gstin || '') ? 'text-emerald-700' : 'text-red-700'}>{seller?.gstin || 'N/A'}</span></div>
        <div>Buyer GSTIN: <span className={buyer?.gstin && gstinRegex.test(buyer.gstin) ? 'text-emerald-700' : 'text-amber-700'}>{buyer?.gstin || 'Optional for B2C'}</span></div>
        <div>Tax Mode: <strong>{taxMode}</strong></div>
      </div>

      {payload.items.map((item, idx) => (
        <div key={idx} className="grid grid-cols-7 gap-2 bg-white p-4 rounded shadow">
          <input className="border p-2 rounded" placeholder="Item" value={item.name} onChange={(e) => updateItem(idx, 'name', e.target.value)} disabled={invoice?.status === 'FINAL'} />
          <div>
            <input className={`border p-2 rounded w-full ${item.hsn_code && !hsnRegex.test(item.hsn_code) ? 'border-red-600' : ''}`} placeholder="HSN" value={item.hsn_code} onChange={(e) => onHsnChange(idx, e.target.value)} disabled={invoice?.status === 'FINAL'} />
            {suggestions.length > 0 && <div className="text-xs mt-1 text-slate-500">{suggestions.slice(0, 2).map((s) => `${s.code} ${s.description}`).join(' · ')}</div>}
          </div>
          <input className="border p-2 rounded" type="number" value={item.quantity} onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))} disabled={invoice?.status === 'FINAL'} />
          <input className="border p-2 rounded" type="number" value={item.unit_price} onChange={(e) => updateItem(idx, 'unit_price', Number(e.target.value))} disabled={invoice?.status === 'FINAL'} />
          <input className="border p-2 rounded" type="number" value={item.discount} onChange={(e) => updateItem(idx, 'discount', Number(e.target.value))} disabled={invoice?.status === 'FINAL'} />
          <select className="border p-2 rounded" value={item.gst_rate} onChange={(e) => updateItem(idx, 'gst_rate', Number(e.target.value))} disabled={invoice?.status === 'FINAL'}>
            {[0, 5, 12, 18, 28, 40].map((r) => <option key={r} value={r}>{r}%</option>)}
          </select>
          <div className="text-sm p-2">₹{q((item.quantity * item.unit_price - item.discount) * (1 + ((payload.composition_flag || payload.export_flag) ? 0 : item.gst_rate / 100))).toFixed(2)}</div>
        </div>
      ))}

      <div className="bg-white p-4 rounded shadow">
        <div>Taxable: ₹{preview.totalTaxable.toFixed(2)}</div>
        <div>Tax: ₹{preview.totalTax.toFixed(2)}</div>
        <div className="font-semibold">Grand Total: ₹{preview.grandTotal.toFixed(2)}</div>
      </div>

      <button type="button" onClick={addItem} className="bg-slate-600 text-white px-4 py-2 rounded mr-2" disabled={invoice?.status === 'FINAL'}>Add item</button>
      <button className="bg-blue-700 text-white px-4 py-2 rounded mr-2" disabled={invoice?.status === 'FINAL'}>Create</button>
      <button type="button" onClick={finalize} className="bg-emerald-700 text-white px-4 py-2 rounded" disabled={!invoice || invoice.status === 'FINAL'}>Finalize Invoice</button>

      {invoice && (
        <div className="bg-white p-4 rounded shadow space-x-3">
          <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/pdf`} target="_blank">PDF</a>
          <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/json`} target="_blank">JSON</a>
          <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/print`} target="_blank">Print</a>
        </div>
      )}
    </form>
  )
}
