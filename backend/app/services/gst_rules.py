"""GST tax rule resolver."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GSTRule:
    supply_type: str
    apply_tax: bool
    tax_mode: str
    reverse_charge: bool
    tax_shifted_to_recipient: bool


def resolve_tax_rule(
    seller_state: str,
    buyer_state: str,
    export_flag: bool,
    reverse_charge_flag: bool,
    composition_flag: bool,
) -> GSTRule:
    """Resolve GST behavior based on parties and flags."""
    if composition_flag:
        return GSTRule(
            supply_type="intra" if seller_state == buyer_state else "inter",
            apply_tax=False,
            tax_mode="none",
            reverse_charge=reverse_charge_flag,
            tax_shifted_to_recipient=reverse_charge_flag,
        )
    if export_flag:
        return GSTRule(
            supply_type="export",
            apply_tax=False,
            tax_mode="zero_rated",
            reverse_charge=reverse_charge_flag,
            tax_shifted_to_recipient=reverse_charge_flag,
        )
    intra = seller_state == buyer_state
    return GSTRule(
        supply_type="intra" if intra else "inter",
        apply_tax=True,
        tax_mode="cgst_sgst" if intra else "igst",
        reverse_charge=reverse_charge_flag,
        tax_shifted_to_recipient=reverse_charge_flag,
    )
