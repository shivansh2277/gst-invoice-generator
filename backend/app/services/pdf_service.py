"""PDF generation using reportlab."""

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_invoice_pdf(invoice: dict) -> bytes:
    """Create a simple GST invoice PDF."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    y = 800
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"GST Invoice #{invoice['invoice_number']}")
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Seller: {invoice['seller']['name']} ({invoice['seller']['gstin']})")
    y -= 15
    c.drawString(50, y, f"Buyer: {invoice['buyer']['name']} ({invoice['buyer'].get('gstin', 'N/A')})")
    y -= 25
    c.drawString(50, y, "Items:")
    y -= 15
    for item in invoice["items"]:
        c.drawString(
            60,
            y,
            f"{item['name']} | HSN {item['hsn_sac']} | Qty {item['quantity']} | ₹{item['total_value']:.2f}",
        )
        y -= 15
    y -= 10
    c.drawString(50, y, f"Taxable: ₹{invoice['total_taxable']:.2f}")
    y -= 15
    c.drawString(50, y, f"CGST: ₹{invoice['total_cgst']:.2f} SGST: ₹{invoice['total_sgst']:.2f} IGST: ₹{invoice['total_igst']:.2f}")
    y -= 15
    c.drawString(50, y, f"Grand Total: ₹{invoice['grand_total']:.2f}")
    y -= 15
    c.drawString(50, y, invoice["grand_total_words"])
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()
