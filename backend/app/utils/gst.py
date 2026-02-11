"""GST related validation helpers."""

import re

GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$")
PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")


def is_valid_gstin(gstin: str) -> bool:
    """Return True if GSTIN follows strict format including PAN segment format."""
    normalized = (gstin or "").upper()
    if not GSTIN_REGEX.match(normalized):
        return False
    pan = normalized[2:12]
    return bool(PAN_REGEX.match(pan))


def state_code_from_gstin(gstin: str) -> str:
    """Extract state code prefix from GSTIN."""
    return gstin[:2]
