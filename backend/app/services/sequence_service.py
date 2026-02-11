"""Invoice number sequence service."""

from datetime import datetime
from typing import Any


def get_financial_year(now: datetime | None = None) -> str:
    """Return financial year as YYYY-YY."""
    today = now or datetime.utcnow()
    start_year = today.year if today.month >= 4 else today.year - 1
    end_short = str((start_year + 1) % 100).zfill(2)
    return f"{start_year}-{end_short}"


def next_invoice_number(db: Any, state_code: str) -> str:
    """Atomically increment sequence and return invoice number FY/STATE/SEQ."""
    from app.models.models import InvoiceSequence

    fy = get_financial_year()
    seq = (
        db.query(InvoiceSequence)
        .filter(InvoiceSequence.financial_year == fy, InvoiceSequence.state_code == state_code)
        .with_for_update()
        .first()
    )
    if not seq:
        seq = InvoiceSequence(financial_year=fy, state_code=state_code, current_value=0)
        db.add(seq)
        db.flush()
    seq.current_value += 1
    db.flush()
    return f"{fy}/{state_code}/{seq.current_value:06d}"
