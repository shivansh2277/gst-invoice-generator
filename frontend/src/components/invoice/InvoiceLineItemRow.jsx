export default function InvoiceLineItemRow({ item, index, errorMap, suggestions, onField, onHsnInput, onRemove, disabled }) {
  const error = (k) => errorMap[`items.${index}.${k}`]

  return (
    <div className="grid grid-cols-1 md:grid-cols-8 gap-3 bg-white p-4 rounded-xl border">
      <div className="md:col-span-2">
        <label className="sr-only" htmlFor={`item-${index}`}>Item name</label>
        <input id={`item-${index}`} className={`w-full border rounded-lg p-3 text-lg ${error('name') ? 'border-red-600' : ''}`} placeholder="Item name" value={item.name} onChange={(e) => onField(index, 'name', e.target.value)} disabled={disabled} />
        {error('name') && <p className="text-red-600 text-xs mt-1">{error('name')}</p>}
      </div>
      <div>
        <label className="sr-only" htmlFor={`hsn-${index}`}>HSN Code</label>
        <input id={`hsn-${index}`} className={`w-full border rounded-lg p-3 text-lg ${error('hsn_code') ? 'border-red-600' : ''}`} placeholder="HSN" value={item.hsn_code} onChange={(e) => onHsnInput(index, e.target.value)} disabled={disabled} />
        {suggestions.length > 0 && <p className="text-xs text-slate-500 mt-1">{suggestions.slice(0, 2).map((s) => `${s.code} ${s.description}`).join(' · ')}</p>}
        {error('hsn_code') && <p className="text-red-600 text-xs mt-1">{error('hsn_code')}</p>}
      </div>
      <input aria-label="Quantity" className={`border rounded-lg p-3 text-lg ${error('quantity') ? 'border-red-600' : ''}`} type="number" value={item.quantity} onChange={(e) => onField(index, 'quantity', Number(e.target.value))} disabled={disabled} />
      <input aria-label="Unit price" className="border rounded-lg p-3 text-lg" type="number" value={item.unit_price} onChange={(e) => onField(index, 'unit_price', Number(e.target.value))} disabled={disabled} />
      <input aria-label="Discount" className="border rounded-lg p-3 text-lg" type="number" value={item.discount} onChange={(e) => onField(index, 'discount', Number(e.target.value))} disabled={disabled} />
      <select aria-label="GST rate" className="border rounded-lg p-3 text-lg" value={item.gst_rate} onChange={(e) => onField(index, 'gst_rate', Number(e.target.value))} disabled={disabled}>
        {[0, 5, 12, 18, 28, 40].map((r) => <option key={r} value={r}>{r}%</option>)}
      </select>
      <button type="button" className="border border-red-400 text-red-700 rounded-lg p-3 font-semibold" onClick={() => onRemove(index)} disabled={disabled}>Remove</button>
    </div>
  )
}
