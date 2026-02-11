export default function TaxPreviewPanel({ preview, taxMode }) {
  const cgst = taxMode === 'cgst+sgst' ? preview.totalTax / 2 : 0
  const sgst = taxMode === 'cgst+sgst' ? preview.totalTax / 2 : 0
  const igst = taxMode === 'igst' ? preview.totalTax : 0

  return (
    <section className="bg-white border rounded-xl p-4" aria-live="polite">
      <h3 className="text-lg font-semibold mb-2">Live Tax Preview</h3>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>Taxable</div><div className="text-right">₹{preview.totalTaxable.toFixed(2)}</div>
        <div>GST Split Mode</div><div className="text-right uppercase">{taxMode}</div>
        <div>CGST</div><div className="text-right">₹{cgst.toFixed(2)}</div>
        <div>SGST</div><div className="text-right">₹{sgst.toFixed(2)}</div>
        <div>IGST</div><div className="text-right">₹{igst.toFixed(2)}</div>
        <div className="font-semibold">Grand Total</div><div className="text-right font-semibold">₹{preview.grandTotal.toFixed(2)}</div>
      </div>
    </section>
  )
}
