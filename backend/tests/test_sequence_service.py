from datetime import datetime

from app.services.sequence_service import get_financial_year


def test_financial_year_before_april():
    assert get_financial_year(datetime(2026, 2, 1)) == "2025-26"


def test_financial_year_after_april():
    assert get_financial_year(datetime(2026, 4, 1)) == "2026-27"
