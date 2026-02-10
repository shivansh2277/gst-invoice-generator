"""Convert number into words for invoice totals."""

from decimal import Decimal

ONES = [
    "Zero",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Eleven",
    "Twelve",
    "Thirteen",
    "Fourteen",
    "Fifteen",
    "Sixteen",
    "Seventeen",
    "Eighteen",
    "Nineteen",
]
TENS = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]


def two_digits(n: int) -> str:
    if n < 20:
        return ONES[n]
    return f"{TENS[n // 10]} {ONES[n % 10]}".strip()


def integer_to_words(n: int) -> str:
    if n < 100:
        return two_digits(n)
    if n < 1000:
        return f"{ONES[n // 100]} Hundred {integer_to_words(n % 100)}".strip()
    if n < 100000:
        return f"{integer_to_words(n // 1000)} Thousand {integer_to_words(n % 1000)}".strip()
    if n < 10000000:
        return f"{integer_to_words(n // 100000)} Lakh {integer_to_words(n % 100000)}".strip()
    return f"{integer_to_words(n // 10000000)} Crore {integer_to_words(n % 10000000)}".strip()


def amount_to_words(amount: float) -> str:
    """Convert amount to Indian currency words."""
    value = Decimal(str(round(amount, 2)))
    rupees = int(value)
    paise = int((value - rupees) * 100)
    text = f"{integer_to_words(rupees)} Rupees"
    if paise:
        text += f" and {integer_to_words(paise)} Paise"
    return text + " Only"
