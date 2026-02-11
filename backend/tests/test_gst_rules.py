from app.services.gst_rules import resolve_tax_rule


def test_intra_state_rule():
    rule = resolve_tax_rule("07", "07", False, False, False)
    assert rule.supply_type == "intra"
    assert rule.tax_mode == "cgst_sgst"
    assert rule.apply_tax is True


def test_inter_state_rule():
    rule = resolve_tax_rule("07", "29", False, False, False)
    assert rule.supply_type == "inter"
    assert rule.tax_mode == "igst"


def test_export_zero_rated_rule():
    rule = resolve_tax_rule("07", "00", True, False, False)
    assert rule.supply_type == "export"
    assert rule.apply_tax is False


def test_composition_no_tax_rule_and_reverse_charge():
    rule = resolve_tax_rule("07", "29", False, True, True)
    assert rule.apply_tax is False
    assert rule.tax_shifted_to_recipient is True
