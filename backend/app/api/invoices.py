"""Invoice CRUD and export endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Buyer, Invoice, InvoiceItem, Seller, TaxSummary, User
from app.schemas.schemas import InvoiceCreate, InvoiceRead
from app.services.pdf_service import generate_invoice_pdf
from app.services.tax_service import compute_line, compute_totals
from app.utils.number_words import amount_to_words

router = APIRouter(prefix="/invoices", tags=["invoices"])


def next_invoice_number(db: Session) -> str:
    """Generate deterministic auto-increment invoice number."""
    year = datetime.utcnow().year
    prefix = f"INV-{year}-"
    latest = db.query(Invoice).filter(Invoice.invoice_number.like(f"{prefix}%")).order_by(Invoice.id.desc()).first()
    sequence = 1
    if latest:
        sequence = int(latest.invoice_number.split("-")[-1]) + 1
    return f"{prefix}{sequence:05d}"


@router.post("", response_model=InvoiceRead)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """Create draft invoice with tax calculations."""
    seller = db.query(Seller).filter(Seller.id == payload.seller_id, Seller.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    buyer = db.query(Buyer).filter(Buyer.id == payload.buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")

    supply_type = "intra" if seller.state_code == buyer.state_code else "inter"
    if payload.invoice_type == "B2B" and not buyer.gstin:
        raise HTTPException(status_code=400, detail="Buyer GSTIN required for B2B")

    invoice_number = next_invoice_number(db)
    if db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first():
        raise HTTPException(status_code=409, detail="Duplicate invoice number")

    line_results = [compute_line(i.quantity, i.unit_price, i.discount, i.gst_rate) for i in payload.items]
    totals = compute_totals(line_results, intra_state=supply_type == "intra")

    invoice = Invoice(
        seller_id=payload.seller_id,
        buyer_id=payload.buyer_id,
        invoice_number=invoice_number,
        invoice_type=payload.invoice_type,
        reverse_charge=payload.reverse_charge,
        supply_type=supply_type,
        total_taxable=totals.total_taxable,
        total_cgst=totals.total_cgst,
        total_sgst=totals.total_sgst,
        total_igst=totals.total_igst,
        grand_total=totals.grand_total,
        grand_total_words=amount_to_words(totals.grand_total),
    )
    db.add(invoice)
    db.flush()

    for idx, item in enumerate(payload.items):
        result = line_results[idx]
        db.add(
            InvoiceItem(
                invoice_id=invoice.id,
                name=item.name,
                hsn_sac=item.hsn_sac,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount,
                gst_rate=item.gst_rate,
                taxable_value=result.taxable_value,
                tax_amount=result.tax_amount,
                total_value=result.total_value,
            )
        )

    db.add(
        TaxSummary(
            invoice_id=invoice.id,
            total_taxable=totals.total_taxable,
            total_cgst=totals.total_cgst,
            total_sgst=totals.total_sgst,
            total_igst=totals.total_igst,
            total_tax=totals.total_tax,
        )
    )
    db.commit()
    db.refresh(invoice)
    return db.query(Invoice).options(joinedload(Invoice.items)).get(invoice.id)


@router.put("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(
    invoice_id: int,
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """Update draft invoice before finalization."""
    invoice = (
        db.query(Invoice)
        .join(Seller, Seller.id == Invoice.seller_id)
        .filter(Invoice.id == invoice_id, Seller.user_id == current_user.id)
        .options(joinedload(Invoice.items))
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if invoice.status == "finalized":
        raise HTTPException(status_code=400, detail="Invoice is locked after finalization")

    seller = db.query(Seller).filter(Seller.id == payload.seller_id, Seller.user_id == current_user.id).first()
    buyer = db.query(Buyer).filter(Buyer.id == payload.buyer_id).first()
    if not seller or not buyer:
        raise HTTPException(status_code=404, detail="Seller or buyer not found")
    supply_type = "intra" if seller.state_code == buyer.state_code else "inter"

    line_results = [compute_line(i.quantity, i.unit_price, i.discount, i.gst_rate) for i in payload.items]
    totals = compute_totals(line_results, intra_state=supply_type == "intra")

    invoice.seller_id = payload.seller_id
    invoice.buyer_id = payload.buyer_id
    invoice.invoice_type = payload.invoice_type
    invoice.reverse_charge = payload.reverse_charge
    invoice.supply_type = supply_type
    invoice.total_taxable = totals.total_taxable
    invoice.total_cgst = totals.total_cgst
    invoice.total_sgst = totals.total_sgst
    invoice.total_igst = totals.total_igst
    invoice.grand_total = totals.grand_total
    invoice.grand_total_words = amount_to_words(totals.grand_total)

    db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).delete()
    for idx, item in enumerate(payload.items):
        result = line_results[idx]
        db.add(
            InvoiceItem(
                invoice_id=invoice.id,
                name=item.name,
                hsn_sac=item.hsn_sac,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount,
                gst_rate=item.gst_rate,
                taxable_value=result.taxable_value,
                tax_amount=result.tax_amount,
                total_value=result.total_value,
            )
        )

    tax = db.query(TaxSummary).filter(TaxSummary.invoice_id == invoice.id).first()
    if tax:
        tax.total_taxable = totals.total_taxable
        tax.total_cgst = totals.total_cgst
        tax.total_sgst = totals.total_sgst
        tax.total_igst = totals.total_igst
        tax.total_tax = totals.total_tax
    db.commit()
    db.refresh(invoice)
    return db.query(Invoice).options(joinedload(Invoice.items)).get(invoice.id)


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Invoice]:
    """List user-owned invoices."""
    return (
        db.query(Invoice)
        .join(Seller, Seller.id == Invoice.seller_id)
        .filter(Seller.user_id == current_user.id)
        .options(joinedload(Invoice.items))
        .all()
    )


@router.post("/{invoice_id}/finalize", response_model=InvoiceRead)
def finalize_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """Finalize invoice and lock it from edits."""
    invoice = (
        db.query(Invoice)
        .join(Seller, Seller.id == Invoice.seller_id)
        .filter(Invoice.id == invoice_id, Seller.user_id == current_user.id)
        .options(joinedload(Invoice.items))
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = "finalized"
    db.commit()
    db.refresh(invoice)
    return invoice


@router.get("/{invoice_id}/json")
def export_invoice_json(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    """Export invoice as JSON."""
    invoice = db.query(Invoice).options(joinedload(Invoice.items), joinedload(Invoice.seller), joinedload(Invoice.buyer)).get(invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "invoice_number": invoice.invoice_number,
        "seller": {"name": invoice.seller.name, "gstin": invoice.seller.gstin},
        "buyer": {"name": invoice.buyer.name, "gstin": invoice.buyer.gstin},
        "items": [{"name": i.name, "hsn_sac": i.hsn_sac, "quantity": i.quantity, "total_value": i.total_value} for i in invoice.items],
        "total_taxable": invoice.total_taxable,
        "total_cgst": invoice.total_cgst,
        "total_sgst": invoice.total_sgst,
        "total_igst": invoice.total_igst,
        "grand_total": invoice.grand_total,
        "grand_total_words": invoice.grand_total_words,
    }


@router.get("/{invoice_id}/pdf")
def export_invoice_pdf(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> Response:
    """Export invoice as PDF download."""
    data = export_invoice_json(invoice_id, db, user)
    content = generate_invoice_pdf(data)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={data['invoice_number']}.pdf"},
    )


@router.get("/{invoice_id}/print", response_class=HTMLResponse)
def print_invoice_html(invoice_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> str:
    """Generate print-friendly HTML."""
    data = export_invoice_json(invoice_id, db, user)
    rows = "".join(
        f"<tr><td>{i['name']}</td><td>{i['hsn_sac']}</td><td>{i['quantity']}</td><td>{i['total_value']:.2f}</td></tr>"
        for i in data["items"]
    )
    return f"""
    <html><body>
    <h1>GST Invoice {data['invoice_number']}</h1>
    <p>Seller: {data['seller']['name']} ({data['seller']['gstin']})</p>
    <p>Buyer: {data['buyer']['name']} ({data['buyer'].get('gstin', 'N/A')})</p>
    <table border='1' cellpadding='6'><tr><th>Item</th><th>HSN/SAC</th><th>Qty</th><th>Total</th></tr>{rows}</table>
    <p>Grand Total: ₹{data['grand_total']:.2f}</p>
    <p>{data['grand_total_words']}</p>
    </body></html>
    """
