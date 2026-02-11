"""PDF generation using reportlab with professional GST layout."""

import base64
from io import BytesIO

from reportlab.graphics.barcode import qr
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _logo_image(logo_base64: str | None):
    if not logo_base64:
        return None
    try:
        raw = logo_base64.split(",", 1)[-1]
        data = base64.b64decode(raw)
        return Image(BytesIO(data), width=90, height=45)
    except Exception:
        return None


def generate_invoice_pdf(invoice: dict) -> bytes:
    """Create GST invoice PDF with logo, HSN table, tax summary, terms, and signature."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=28, rightMargin=28, topMargin=30, bottomMargin=24)
    styles = getSampleStyleSheet()

    story = []
    logo = _logo_image(invoice.get("logo_base64"))
    title = Paragraph(f"GST TAX INVOICE<br/><b>{invoice['invoice_number']}</b>", styles["Title"])
    if logo:
        head = Table([[logo, title]], colWidths=[110, 420])
    else:
        head = Table([[title]], colWidths=[530])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.extend([head, Spacer(1, 10)])

    seller_block = f"<b>Seller</b><br/>{invoice['seller']['name']}<br/>{invoice['seller']['address']}<br/>GSTIN: {invoice['seller']['gstin']}"
    buyer_block = f"<b>Buyer</b><br/>{invoice['buyer']['name']}<br/>{invoice['buyer']['address']}<br/>GSTIN: {invoice['buyer'].get('gstin') or 'N/A'}"
    party_tbl = Table([[Paragraph(seller_block, styles["BodyText"]), Paragraph(buyer_block, styles["BodyText"])]], colWidths=[265, 265])
    party_tbl.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, colors.black), ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([party_tbl, Spacer(1, 10)])

    headers = ["Item", "HSN", "Qty", "Rate", "GST%", "Tax", "Total"]
    rows = [[i["name"], i["hsn_code"], f"{i['quantity']}", f"₹{i['unit_price']:.2f}", f"{i['gst_rate']}%", f"₹{i['tax_amount']:.2f}", f"₹{i['total_value']:.2f}"] for i in invoice["line_items"]]
    item_tbl = Table([headers] + rows, repeatRows=1, colWidths=[160, 60, 45, 75, 50, 60, 80])
    item_tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]))
    story.extend([item_tbl, Spacer(1, 10)])

    summary = Table([
        ["Taxable", f"₹{invoice['tax_summary']['total_taxable']:.2f}"],
        ["CGST", f"₹{invoice['tax_summary']['total_cgst']:.2f}"],
        ["SGST", f"₹{invoice['tax_summary']['total_sgst']:.2f}"],
        ["IGST", f"₹{invoice['tax_summary']['total_igst']:.2f}"],
        ["Grand Total", f"₹{invoice['tax_summary']['grand_total']:.2f}"],
    ], colWidths=[160, 120])
    summary.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.black), ("FONTNAME", (0, 4), (-1, 4), "Helvetica-Bold")]))

    qr_code = qr.QrCodeWidget(f"invoice_id:{invoice['invoice_id']}")
    from reportlab.graphics.shapes import Drawing

    bounds = qr_code.getBounds()
    drawing = Drawing(80, 80, transform=[80.0 / (bounds[2] - bounds[0]), 0, 0, 80.0 / (bounds[3] - bounds[1]), 0, 0])
    drawing.add(qr_code)
    foot = Table([[summary, drawing]], colWidths=[390, 120])
    foot.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.extend([foot, Spacer(1, 8), Paragraph(invoice["tax_summary"]["grand_total_words"], styles["BodyText"])])

    story.extend([
        Spacer(1, 12),
        Paragraph("<b>Terms & Conditions</b>", styles["Heading4"]),
        Paragraph(invoice.get("terms_conditions") or "-", styles["BodyText"]),
        Spacer(1, 30),
        Paragraph(f"For {invoice['seller']['name']}", styles["BodyText"]),
        Spacer(1, 20),
        Paragraph("________________________", styles["BodyText"]),
        Paragraph(invoice.get("signature_name") or "Authorized Signatory", styles["BodyText"]),
    ])

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
