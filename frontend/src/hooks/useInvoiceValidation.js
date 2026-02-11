const hsnRegex = /^\d{4,8}$/

export default function useInvoiceValidation(payload) {
  const errors = {}
  if (!payload.seller_id) errors.seller_id = 'Seller is required'
  if (!payload.buyer_id) errors.buyer_id = 'Buyer is required'
  payload.items.forEach((item, idx) => {
    if (!item.name) errors[`items.${idx}.name`] = 'Item name required'
    if (!hsnRegex.test(item.hsn_code || '')) errors[`items.${idx}.hsn_code`] = 'HSN must be 4-8 digits'
    if (Number(item.quantity) <= 0) errors[`items.${idx}.quantity`] = 'Qty must be > 0'
  })
  return errors
}
