import { useEffect, useMemo, useState } from 'react'
import api from '../services/api'
import InvoiceBuilderGrid from '../components/invoice/InvoiceBuilderGrid'
import TaxPreviewPanel from '../components/invoice/TaxPreviewPanel'
import useInvoiceForm from '../hooks/useInvoiceForm'

const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$/

export default function NewInvoicePage({ notify }) {
  const [sellers, setSellers] = useState([])
  const [buyers, setBuyers] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [invoice, setInvoice] = useState(null)
  const { payload, setPayload, preview, errors, addItem, removeItem, updateItem, clearDraft } = useInvoiceForm()

  useEffect(() => {
    Promise.all([api.get('/sellers'), api.get('/buyers')]).then(([s, b]) => {
      setSellers(s.data)
      setBuyers(b.data)
      setPayload((p) => ({ ...p, seller_id: p.seller_id || s.data[0]?.id || 0, buyer_id: p.buyer_id || b.data[0]?.id || 0 }))
    })
  }, [setPayload])

  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
        e.preventDefault()
        addItem()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [addItem])

  const seller = sellers.find((s) => s.id === Number(payload.seller_id))
  const buyer = buyers.find((b) => b.id === Number(payload.buyer_id))
  const taxMode = payload.export_flag ? 'zero' : seller && buyer && seller.state_code === buyer.state_code ? 'cgst+sgst' : 'igst'
  const isFinal = invoice?.status === 'FINAL'

  const offlineLabel = useMemo(() => (navigator.onLine ? 'Online' : 'Offline (local autosave active)'), [])

  const onHsnInput = async (index, value) => {
    updateItem(index, 'hsn_code', value)
    if (value.length >= 2) {
      try {
        const { data } = await api.get('/hsn', { params: { q: value } })
        setSuggestions(data)
      } catch {
        setSuggestions([])
      }
    }
  }

  const onLogoUpload = async (file) => {
    if (!file) return
    const base64 = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result))
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
    setPayload((p) => ({ ...p, logo_base64: base64 }))
  }

  const submit = async (e) => {
    e.preventDefault()
    if (Object.keys(errors).length) {
      notify('Fix inline errors before submit')
      return
    }
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-2xl md:text-3xl font-semibold">Professional Invoice Builder</h2>
        <div className="text-sm text-slate-600">{offlineLabel} • Autosave enabled</div>
      </div>

      <div className="bg-white p-4 rounded-xl border grid grid-cols-1 md:grid-cols-3 gap-4">
        <select aria-label="Seller" className={`border rounded-lg p-3 text-lg ${errors.seller_id ? 'border-red-600' : ''}`} value={payload.seller_id} onChange={(e) => setPayload({ ...payload, seller_id: Number(e.target.value) })}>
          {sellers.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <select aria-label="Buyer" className={`border rounded-lg p-3 text-lg ${errors.buyer_id ? 'border-red-600' : ''}`} value={payload.buyer_id} onChange={(e) => setPayload({ ...payload, buyer_id: Number(e.target.value) })}>
          {buyers.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <select aria-label="Invoice Type" className="border rounded-lg p-3 text-lg" value={payload.invoice_type} onChange={(e) => setPayload({ ...payload, invoice_type: e.target.value })}>
          <option>B2B</option><option>B2C</option>
        </select>
        <label className="text-sm"><input type="checkbox" checked={payload.reverse_charge} onChange={(e) => setPayload({ ...payload, reverse_charge: e.target.checked })} /> Reverse Charge</label>
        <label className="text-sm"><input type="checkbox" checked={payload.export_flag} onChange={(e) => setPayload({ ...payload, export_flag: e.target.checked })} /> Export</label>
        <label className="text-sm"><input type="checkbox" checked={payload.composition_flag} onChange={(e) => setPayload({ ...payload, composition_flag: e.target.checked })} /> Composition</label>
      </div>

      <div className="bg-white p-4 rounded-xl border grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium">Company Logo (used in PDF)</label>
          <input type="file" accept="image/*" className="mt-1 w-full border rounded-lg p-3" onChange={(e) => onLogoUpload(e.target.files?.[0])} />
          {payload.logo_base64 && <p className="text-xs text-emerald-700 mt-1">Logo attached</p>}
        </div>
        <div>
          <label className="block text-sm font-medium">Signature Name</label>
          <input className="mt-1 w-full border rounded-lg p-3 text-lg" value={payload.signature_name} onChange={(e) => setPayload({ ...payload, signature_name: e.target.value })} />
        </div>
        <div className="md:col-span-2">
          <label className="block text-sm font-medium">Terms & Conditions</label>
          <textarea className="mt-1 w-full border rounded-lg p-3 text-lg" rows={3} value={payload.terms_conditions} onChange={(e) => setPayload({ ...payload, terms_conditions: e.target.value })} />
        </div>
      </div>

      <div className="bg-white p-4 rounded-xl border text-sm">
        <div>Seller GSTIN: <span className={gstinRegex.test(seller?.gstin || '') ? 'text-emerald-700' : 'text-red-700'}>{seller?.gstin || 'N/A'}</span></div>
        <div>Buyer GSTIN: <span className={buyer?.gstin && gstinRegex.test(buyer.gstin) ? 'text-emerald-700' : 'text-amber-700'}>{buyer?.gstin || 'Optional for B2C'}</span></div>
        <div>Tax Mode (auto): <strong>{taxMode}</strong></div>
      </div>

      <InvoiceBuilderGrid items={payload.items} errors={errors} suggestions={suggestions} onField={updateItem} onHsnInput={onHsnInput} onAdd={addItem} onRemove={removeItem} disabled={isFinal} />
      <TaxPreviewPanel preview={preview} taxMode={taxMode} />

      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={clearDraft} className="bg-slate-200 px-4 py-3 rounded-lg">Reset Draft</button>
        <button className="bg-blue-700 text-white px-4 py-3 rounded-lg" disabled={isFinal}>Create Invoice</button>
        <button type="button" onClick={finalize} className="bg-emerald-700 text-white px-4 py-3 rounded-lg" disabled={!invoice || isFinal}>Finalize</button>
      </div>

      {invoice && (
        <div className="bg-white p-4 rounded-xl border space-x-3">
          <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/pdf`} target="_blank">PDF</a>
          <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/json`} target="_blank">JSON</a>
          <a className="text-blue-700 underline" href={`http://localhost:8000/api/v1/invoices/${invoice.id}/print`} target="_blank">Print</a>
        </div>
      )}
    </form>
  )
}
