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


def q(value: float | Decimal) -> Decimal:
    """Quantize value to 2 decimals using GST-friendly half-up rounding."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def compute_line(quantity: float, unit_price: float, discount: float, gst_rate: float, apply_tax: bool = True) -> TaxLineResult:
    """Compute values for one line item with line-level rounding."""
    base = q(quantity) * q(unit_price)
    discounted = max(q(0), q(base - q(discount)))
    tax = q(discounted * q(gst_rate) / Decimal("100")) if apply_tax else q(0)
    total = q(discounted + tax)
    return TaxLineResult(float(discounted), float(tax), float(total))


def split_tax(total_tax: float, tax_mode: str) -> tuple[float, float, float]:
    """Split tax into CGST/SGST or IGST based on mode."""
    if tax_mode == "cgst_sgst":
        cgst = q(total_tax / 2)
        sgst = q(q(total_tax) - cgst)
        return float(cgst), float(sgst), 0.0
    if tax_mode == "igst":
        return 0.0, 0.0, float(q(total_tax))
    return 0.0, 0.0, 0.0


def compute_totals(lines: list[TaxLineResult], tax_mode: str) -> TaxTotals:
    """Recompute invoice totals from rounded lines to avoid drift."""
    taxable = q(sum(q(line.taxable_value) for line in lines))
    tax = q(sum(q(line.tax_amount) for line in lines))
    cgst, sgst, igst = split_tax(float(tax), tax_mode)
    grand = q(taxable + tax)
    return TaxTotals(
        total_taxable=float(taxable),
        total_cgst=float(q(cgst)),
        total_sgst=float(q(sgst)),
        total_igst=float(q(igst)),
        total_tax=float(tax),
        grand_total=float(grand),
    )
