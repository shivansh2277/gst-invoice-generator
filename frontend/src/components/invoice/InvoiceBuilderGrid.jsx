import InvoiceLineItemRow from './InvoiceLineItemRow'

export default function InvoiceBuilderGrid({ items, errors, suggestions, onField, onHsnInput, onAdd, onRemove, disabled }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold">Invoice Builder</h3>
        <button type="button" onClick={onAdd} className="bg-slate-700 text-white px-4 py-2 rounded-lg" disabled={disabled}>+ Add Line</button>
      </div>
      {items.map((item, index) => (
        <InvoiceLineItemRow key={index} item={item} index={index} errorMap={errors} suggestions={suggestions} onField={onField} onHsnInput={onHsnInput} onRemove={onRemove} disabled={disabled} />
      ))}
    </section>
  )
}
