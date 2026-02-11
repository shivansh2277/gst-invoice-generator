"""Invoice status lock guards."""


def assert_editable(status: str) -> None:
    """Raise ValueError when attempting to edit final invoice."""
    if status == "FINAL":
        raise ValueError("Invoice is locked after finalization")
