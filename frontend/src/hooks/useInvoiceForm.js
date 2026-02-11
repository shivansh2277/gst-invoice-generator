import { useEffect, useMemo, useState } from 'react'
import useDebouncedValue from './useDebouncedValue'
import useInvoiceValidation from './useInvoiceValidation'

const KEY = 'gst.invoice.form.v2'
const emptyItem = { name: '', hsn_code: '', quantity: 1, unit_price: 0, discount: 0, gst_rate: 18 }
const q = (n) => Math.round((Number(n) + Number.EPSILON) * 100) / 100

const initialPayload = {
  seller_id: 0,
  buyer_id: 0,
  invoice_type: 'B2B',
  reverse_charge: false,
  export_flag: false,
  composition_flag: false,
  logo_base64: null,
  terms_conditions: '',
  signature_name: 'Authorized Signatory',
  items: [{ ...emptyItem }]
}

export default function useInvoiceForm() {
  const [payload, setPayload] = useState(() => {
    try {
      const saved = localStorage.getItem(KEY)
      return saved ? JSON.parse(saved) : initialPayload
    } catch {
      return initialPayload
    }
  })

  const debouncedPayload = useDebouncedValue(payload, 220)
  const errors = useInvoiceValidation(payload)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(debouncedPayload))
  }, [debouncedPayload])

  const preview = useMemo(() => {
    const lines = debouncedPayload.items.map((item) => {
      const taxable = q(q(item.quantity) * q(item.unit_price) - q(item.discount))
      const tax = debouncedPayload.composition_flag || debouncedPayload.export_flag ? 0 : q((taxable * q(item.gst_rate)) / 100)
      return { taxable, tax, total: q(taxable + tax) }
    })
    const totalTaxable = q(lines.reduce((s, l) => s + l.taxable, 0))
    const totalTax = q(lines.reduce((s, l) => s + l.tax, 0))
    return { lines, totalTaxable, totalTax, grandTotal: q(totalTaxable + totalTax) }
  }, [debouncedPayload])

  const addItem = () => setPayload((p) => ({ ...p, items: [...p.items, { ...emptyItem }] }))
  const removeItem = (idx) =>
    setPayload((p) => {
      const next = p.items.filter((_, i) => i !== idx)
      return { ...p, items: next.length ? next : [{ ...emptyItem }] }
    })
  const updateItem = (idx, key, value) => setPayload((p) => ({ ...p, items: p.items.map((it, i) => (i === idx ? { ...it, [key]: value } : it)) }))
  const clearDraft = () => {
    localStorage.removeItem(KEY)
    setPayload(initialPayload)
  }

  return { payload, setPayload, preview, errors, addItem, removeItem, updateItem, clearDraft }
}
