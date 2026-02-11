import pytest

from app.services.lock_service import assert_editable


def test_draft_is_editable():
    assert_editable("DRAFT")


def test_final_is_locked():
    with pytest.raises(ValueError):
        assert_editable("FINAL")
