"""Invoice CRUD and export endpoints."""

import hashlib
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import Buyer, HsnMaster, IdempotencyKey, Invoice, InvoiceItem, Seller, TaxSummary, User
from app.schemas.schemas import InvoiceCreate, InvoiceRead
from app.services.gst_rules import resolve_tax_rule
from app.services.lock_service import assert_editable
from app.services.metrics_service import inc
from app.services.pdf_service import generate_invoice_pdf
from app.services.rate_limit import rate_limiter
from app.services.sequence_service import next_invoice_number
from app.services.tax_service import compute_line, compute_totals
from app.utils.number_words import amount_to_words

router = APIRouter(prefix="/invoices", tags=["invoices"])


def _invoice_query(db: Session, invoice_id: int) -> Invoice | None:
    return (
        db.query(Invoice)
        .options(joinedload(Invoice.items), joinedload(Invoice.seller), joinedload(Invoice.buyer), joinedload(Invoice.tax_summary))
        .filter(Invoice.id == invoice_id)
        .first()
    )


def _payload_hash(payload: InvoiceCreate) -> str:
    raw = json.dumps(payload.model_dump(), sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _resolve_rate(db: Session, hsn_code: str, payload_rate: float | None) -> float:
    hsn = db.query(HsnMaster).filter(HsnMaster.code == hsn_code).first()
    if not hsn:
        raise HTTPException(status_code=400, detail=f"Unknown HSN code: {hsn_code}")
    return float(payload_rate if payload_rate is not None else hsn.default_gst_rate)


def _to_gst_json(invoice: Invoice) -> dict:
    return {
        "invoice": {
            "invoice_id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "invoice_type": invoice.invoice_type,
            "status": invoice.status,
            "supply_type": invoice.supply_type,
            "reverse_charge": invoice.reverse_charge,
            "export_flag": invoice.export_flag,
            "composition_flag": invoice.composition_flag,
            "tax_shifted_to_recipient": invoice.tax_shifted_to_recipient,
            "seller": {
                "name": invoice.seller.name,
                "gstin": invoice.seller.gstin,
                "state_code": invoice.seller.state_code,
                "address": invoice.seller.address,
            },
            "buyer": {
                "name": invoice.buyer.name,
                "gstin": invoice.buyer.gstin,
                "state_code": invoice.buyer.state_code,
                "address": invoice.buyer.address,
            },
            "line_items": [
                {
                    "name": i.name,
                    "hsn_code": i.hsn_code,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "discount": i.discount,
                    "gst_rate": i.gst_rate,
                    "taxable_value": i.taxable_value,
                    "tax_amount": i.tax_amount,
                    "total_value": i.total_value,
                }
                for i in invoice.items
            ],
            "tax_summary": {
                "total_taxable": invoice.total_taxable,
                "total_cgst": invoice.total_cgst,
                "total_sgst": invoice.total_sgst,
                "total_igst": invoice.total_igst,
                "grand_total": invoice.grand_total,
                "grand_total_words": invoice.grand_total_words,
            },
        }
    }


@router.post("", response_model=InvoiceRead)
def create_invoice(
    payload: InvoiceCreate,
    request: Request,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Invoice:
    """Create draft invoice with tax calculations."""
    rate_key = f"create_invoice:{current_user.id}"
    if not rate_limiter.allow(rate_key, limit=30, per_seconds=60):
        raise HTTPException(status_code=429, detail="Invoice create rate limit exceeded")

    payload_digest = _payload_hash(payload)
    if idempotency_key:
        record = db.query(IdempotencyKey).filter(IdempotencyKey.key == idempotency_key, IdempotencyKey.user_id == current_user.id).first()
        if record:
            if record.request_hash != payload_digest:
                raise HTTPException(status_code=409, detail="Idempotency key reused with different payload")
            existing = _invoice_query(db, record.invoice_id)
            if not existing:
                raise HTTPException(status_code=409, detail="Idempotency reference missing")
            return existing

    seller = db.query(Seller).filter(Seller.id == payload.seller_id, Seller.user_id == current_user.id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller not found")
    buyer = db.query(Buyer).filter(Buyer.id == payload.buyer_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer not found")
    if payload.invoice_type == "B2B" and not buyer.gstin:
        raise HTTPException(status_code=400, detail="Buyer GSTIN required for B2B")

    rule = resolve_tax_rule(
        seller_state=seller.state_code,
        buyer_state=buyer.state_code,
        export_flag=payload.export_flag,
        reverse_charge_flag=payload.reverse_charge,
        composition_flag=payload.composition_flag or seller.composition_flag,
    )

    invoice_number = next_invoice_number(db, seller.state_code)

    line_results = []
    finalized_items = []
    for item in payload.items:
        rate = _resolve_rate(db, item.hsn_code, item.gst_rate)
        line = compute_line(item.quantity, item.unit_price, item.discount, rate, apply_tax=rule.apply_tax)
        line_results.append(line)
        finalized_items.append((item, rate, line))

    totals = compute_totals(line_results, tax_mode=rule.tax_mode)

    invoice = Invoice(
        seller_id=payload.seller_id,
        buyer_id=payload.buyer_id,
        invoice_number=invoice_number,
        invoice_type=payload.invoice_type,
        reverse_charge=rule.reverse_charge,
        export_flag=payload.export_flag,
        composition_flag=payload.composition_flag or seller.composition_flag,
        tax_shifted_to_recipient=rule.tax_shifted_to_recipient,
        supply_type=rule.supply_type,
        status="DRAFT",
        total_taxable=totals.total_taxable,
        total_cgst=totals.total_cgst,
        total_sgst=totals.total_sgst,
        total_igst=totals.total_igst,
        grand_total=totals.grand_total,
        grand_total_words=amount_to_words(totals.grand_total),
    )
    db.add(invoice)
    db.flush()

    for item, rate, result in finalized_items:
        db.add(
            InvoiceItem(
                invoice_id=invoice.id,
                name=item.name,
                hsn_code=item.hsn_code,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount,
                gst_rate=rate,
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

    if idempotency_key:
        db.add(IdempotencyKey(key=idempotency_key, user_id=current_user.id, request_hash=payload_digest, invoice_id=invoice.id))

    db.commit()
    inc("invoice_create_total")
    return _invoice_query(db, invoice.id)


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
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    try:
        assert_editable(invoice.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    seller = db.query(Seller).filter(Seller.id == payload.seller_id, Seller.user_id == current_user.id).first()
    buyer = db.query(Buyer).filter(Buyer.id == payload.buyer_id).first()
    if not seller or not buyer:
        raise HTTPException(status_code=404, detail="Seller or buyer not found")

    rule = resolve_tax_rule(
        seller_state=seller.state_code,
        buyer_state=buyer.state_code,
        export_flag=payload.export_flag,
        reverse_charge_flag=payload.reverse_charge,
        composition_flag=payload.composition_flag or seller.composition_flag,
    )

    lines = []
    final_items = []
    for item in payload.items:
        rate = _resolve_rate(db, item.hsn_code, item.gst_rate)
        line = compute_line(item.quantity, item.unit_price, item.discount, rate, apply_tax=rule.apply_tax)
        lines.append(line)
        final_items.append((item, rate, line))

    totals = compute_totals(lines, tax_mode=rule.tax_mode)

    invoice.seller_id = payload.seller_id
    invoice.buyer_id = payload.buyer_id
    invoice.invoice_type = payload.invoice_type
    invoice.reverse_charge = rule.reverse_charge
    invoice.export_flag = payload.export_flag
    invoice.composition_flag = payload.composition_flag or seller.composition_flag
    invoice.tax_shifted_to_recipient = rule.tax_shifted_to_recipient
    invoice.supply_type = rule.supply_type
    invoice.total_taxable = totals.total_taxable
    invoice.total_cgst = totals.total_cgst
    invoice.total_sgst = totals.total_sgst
    invoice.total_igst = totals.total_igst
    invoice.grand_total = totals.grand_total
    invoice.grand_total_words = amount_to_words(totals.grand_total)

    db.query(InvoiceItem).filter(InvoiceItem.invoice_id == invoice.id).delete()
    for item, rate, line in final_items:
        db.add(
            InvoiceItem(
                invoice_id=invoice.id,
                name=item.name,
                hsn_code=item.hsn_code,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount=item.discount,
                gst_rate=rate,
                taxable_value=line.taxable_value,
                tax_amount=line.tax_amount,
                total_value=line.total_value,
            )
        )
    tax = db.query(TaxSummary).filter(TaxSummary.invoice_id == invoice.id).first()
    tax.total_taxable = totals.total_taxable
    tax.total_cgst = totals.total_cgst
    tax.total_sgst = totals.total_sgst
    tax.total_igst = totals.total_igst
    tax.total_tax = totals.total_tax

    db.commit()
    return _invoice_query(db, invoice.id)


@router.get("", response_model=list[InvoiceRead])
def list_invoices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[Invoice]:
    return (
        db.query(Invoice)
        .join(Seller, Seller.id == Invoice.seller_id)
        .filter(Seller.user_id == current_user.id)
        .options(joinedload(Invoice.items))
        .order_by(Invoice.id.desc())
        .all()
    )


@router.post("/{invoice_id}/finalize", response_model=InvoiceRead)
def finalize_invoice(invoice_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Invoice:
    invoice = (
        db.query(Invoice)
        .join(Seller, Seller.id == Invoice.seller_id)
        .filter(Invoice.id == invoice_id, Seller.user_id == current_user.id)
        .first()
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = "FINAL"
    db.commit()
    inc("invoice_finalize_total")
    return _invoice_query(db, invoice.id)


@router.get("/{invoice_id}/json")
def export_invoice_json(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    invoice = _invoice_query(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _to_gst_json(invoice)


@router.get("/{invoice_id}/pdf")
def export_invoice_pdf(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> Response:
    invoice = _invoice_query(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    data = _to_gst_json(invoice)["invoice"]
    content = generate_invoice_pdf(data)
    return Response(content=content, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={invoice.invoice_number}.pdf"})


@router.get("/{invoice_id}/print", response_class=HTMLResponse)
def print_invoice_html(invoice_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> str:
    invoice = _invoice_query(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    rows = "".join(
        f"<tr><td>{i.name}</td><td>{i.hsn_code}</td><td>{i.quantity}</td><td>{i.gst_rate}%</td><td>₹{i.total_value:.2f}</td></tr>"
        for i in invoice.items
    )
    return f"""
    <html><head><style>
    @page {{ size: A4; margin: 1.5cm; }}
    body {{ font-family: Arial; }}
    .row {{ display:flex; justify-content:space-between; }}
    table {{ width:100%; border-collapse: collapse; margin-top: 10px; }}
    th, td {{ border:1px solid #555; padding:6px; font-size:12px; }}
    </style></head><body>
    <h2>GST INVOICE</h2>
    <div class='row'><div><strong>{invoice.seller.name}</strong><br/>{invoice.seller.address}<br/>GSTIN: {invoice.seller.gstin}</div>
    <div><strong>{invoice.buyer.name}</strong><br/>{invoice.buyer.address}<br/>GSTIN: {invoice.buyer.gstin or 'N/A'}</div></div>
    <p><strong>Invoice No:</strong> {invoice.invoice_number} | <strong>Status:</strong> {invoice.status}</p>
    <table><tr><th>Item</th><th>HSN</th><th>Qty</th><th>GST</th><th>Total</th></tr>{rows}</table>
    <p>Taxable: ₹{invoice.total_taxable:.2f} | CGST: ₹{invoice.total_cgst:.2f} | SGST: ₹{invoice.total_sgst:.2f} | IGST: ₹{invoice.total_igst:.2f}</p>
    <h3>Grand Total: ₹{invoice.grand_total:.2f}</h3>
    <p>{invoice.grand_total_words}</p>
    </body></html>
    """
