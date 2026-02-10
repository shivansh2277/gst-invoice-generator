"""Unit tests for deterministic tax calculations."""

from app.services.tax_service import compute_line, compute_totals


def test_compute_line_with_discount_and_rounding():
    result = compute_line(quantity=3, unit_price=199.99, discount=10.00, gst_rate=18)
    assert result.taxable_value == 589.97
    assert result.tax_amount == 106.19
    assert result.total_value == 696.16


def test_compute_totals_intrastate_split():
    lines = [
        compute_line(2, 100.0, 0.0, 18),
        compute_line(1, 100.0, 0.0, 5),
    ]
    totals = compute_totals(lines, intra_state=True)
    assert totals.total_taxable == 300.00
    assert totals.total_tax == 41.00
    assert totals.total_cgst == 20.50
    assert totals.total_sgst == 20.50
    assert totals.total_igst == 0.00
    assert totals.grand_total == 341.00


def test_compute_totals_interstate_split():
    lines = [compute_line(5, 50, 0, 12)]
    totals = compute_totals(lines, intra_state=False)
    assert totals.total_taxable == 250.00
    assert totals.total_tax == 30.00
    assert totals.total_igst == 30.00
    assert totals.total_cgst == 0.00
    assert totals.total_sgst == 0.00
