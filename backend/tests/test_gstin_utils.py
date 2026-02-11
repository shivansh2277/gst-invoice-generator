from app.utils.gst import is_valid_gstin


def test_valid_gstin():
    assert is_valid_gstin("07ABCDE1234F1Z5") is True


def test_invalid_pan_segment():
    assert is_valid_gstin("07AB1DE1234F1Z5") is False


def test_invalid_pattern():
    assert is_valid_gstin("07ABCDE1234F115") is False
