"""PDF generation using reportlab with GST layout."""

from io import BytesIO

from reportlab.graphics.barcode import qr
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def generate_invoice_pdf(invoice: dict) -> bytes:
    """Create GST invoice PDF with seller/buyer blocks and tax summary."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [Paragraph(f"GST Invoice: {invoice['invoice_number']}", styles["Title"]), Spacer(1, 8)]

    seller_block = f"<b>Seller</b><br/>{invoice['seller']['name']}<br/>{invoice['seller']['address']}<br/>GSTIN: {invoice['seller']['gstin']}"
    buyer_block = f"<b>Buyer</b><br/>{invoice['buyer']['name']}<br/>{invoice['buyer']['address']}<br/>GSTIN: {invoice['buyer'].get('gstin') or 'N/A'}"
    party_tbl = Table([[Paragraph(seller_block, styles["BodyText"]), Paragraph(buyer_block, styles["BodyText"])]], colWidths=[260, 260])
    party_tbl.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([party_tbl, Spacer(1, 10)])

    headers = ["Item", "HSN", "Qty", "Rate", "GST%", "Tax", "Total"]
    rows = [
        [
            item["name"],
            item["hsn_code"],
            f"{item['quantity']}",
            f"₹{item['unit_price']:.2f}",
            f"{item['gst_rate']}%",
            f"₹{item['tax_amount']:.2f}",
            f"₹{item['total_value']:.2f}",
        ]
        for item in invoice["line_items"]
    ]
    item_tbl = Table([headers] + rows, repeatRows=1)
    item_tbl.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.extend([item_tbl, Spacer(1, 10)])

    tax = invoice
    summary = Table(
        [
            ["Taxable", f"₹{tax['tax_summary']['total_taxable']:.2f}"],
            ["CGST", f"₹{tax['tax_summary']['total_cgst']:.2f}"],
            ["SGST", f"₹{tax['tax_summary']['total_sgst']:.2f}"],
            ["IGST", f"₹{tax['tax_summary']['total_igst']:.2f}"],
            ["Grand Total", f"₹{tax['tax_summary']['grand_total']:.2f}"],
        ],
        colWidths=[150, 120],
    )
    summary.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.black), ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold")]))
    story.append(summary)
    story.append(Spacer(1, 8))
    story.append(Paragraph(tax["tax_summary"]["grand_total_words"], styles["BodyText"]))

    qr_code = qr.QrCodeWidget(f"invoice_id:{invoice['invoice_id']}")
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    from reportlab.graphics.shapes import Drawing

    drawing = Drawing(80, 80, transform=[80.0 / width, 0, 0, 80.0 / height, 0, 0])
    drawing.add(qr_code)
    story.extend([Spacer(1, 6), Paragraph("Scan QR (invoice id)", styles["Italic"]), drawing])

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
