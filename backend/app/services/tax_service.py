"""Deterministic tax computation logic."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class TaxLineResult:
    taxable_value: float
    tax_amount: float
    total_value: float


@dataclass
class TaxTotals:
    total_taxable: float
    total_cgst: float
    total_sgst: float
    total_igst: float
    total_tax: float
    grand_total: float


def q(value: float) -> Decimal:
    """Quantize value to 2 decimals using GST-friendly half-up rounding."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_line(quantity: float, unit_price: float, discount: float, gst_rate: float) -> TaxLineResult:
    """Compute values for one line item."""
    base = q(quantity) * q(unit_price)
    discounted = max(q(0), base - q(discount))
    tax = q(discounted * q(gst_rate) / Decimal("100"))
    total = q(discounted + tax)
    return TaxLineResult(float(discounted), float(tax), float(total))


def split_tax(total_tax: float, intra_state: bool) -> tuple[float, float, float]:
    """Split tax into CGST/SGST or IGST."""
    if intra_state:
        cgst = q(total_tax / 2)
        sgst = q(total_tax - float(cgst))
        return float(cgst), float(sgst), 0.0
    return 0.0, 0.0, float(q(total_tax))


def compute_totals(lines: list[TaxLineResult], intra_state: bool) -> TaxTotals:
    """Compute invoice totals from lines."""
    taxable = q(sum(line.taxable_value for line in lines))
    tax = q(sum(line.tax_amount for line in lines))
    cgst, sgst, igst = split_tax(float(tax), intra_state)
    grand = q(float(taxable) + float(tax))
    return TaxTotals(
        total_taxable=float(taxable),
        total_cgst=float(q(cgst)),
        total_sgst=float(q(sgst)),
        total_igst=float(q(igst)),
        total_tax=float(tax),
        grand_total=float(grand),
    )
