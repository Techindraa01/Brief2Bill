"""Totals computation helpers."""

from __future__ import annotations

from typing import Iterable, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - avoid circular imports at runtime
    from ..models.document_models import DocDraft, Item, Totals


_INDIAN_SCALE = [
    (10000000, "Crore"),
    (100000, "Lakh"),
    (1000, "Thousand"),
    (100, "Hundred"),
]

_ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
]
_TEENS = [
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
_TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
]


def _two_digit_words(value: int) -> str:
    if value < 10:
        return _ONES[value]
    if value < 20:
        return _TEENS[value - 10]
    tens = _TENS[value // 10]
    ones = _ONES[value % 10]
    return f"{tens} {ones}".strip()


def number_to_words_indian(amount: float) -> str:
    if amount == 0:
        return "Zero Rupees Only"

    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))

    parts: list[str] = []
    remaining = rupees

    for divider, label in _INDIAN_SCALE:
        current = remaining // divider
        if current:
            if divider == 100:
                parts.append(f"{_ONES[current]} {label}")
            else:
                parts.append(f"{_two_digit_words(current)} {label}")
            remaining %= divider

    if remaining:
        parts.append(_two_digit_words(remaining))

    words = " ".join(part for part in parts if part).strip()
    if not words:
        words = "Zero"
    words += " Rupees"

    if paise:
        words += f" and {_two_digit_words(paise)} Paise"

    return words + " Only"


def compute_line(item: "Item") -> tuple[float, float]:
    quantity = float(item.qty)
    unit_price = float(item.unit_price)
    discount = float(item.discount or 0)
    tax_rate = float(item.tax_rate or 0)

    line_total = max(quantity * unit_price - discount, 0.0)
    line_tax = line_total * (tax_rate / 100.0)
    return round(line_total, 2), round(line_tax, 2)


def aggregate_totals(items: Iterable["Item"]) -> tuple[float, float, float]:
    subtotal = 0.0
    discount_total = 0.0
    tax_total = 0.0

    for item in items:
        line_total, line_tax = compute_line(item)
        subtotal += line_total
        discount_total += float(item.discount or 0)
        tax_total += line_tax

    return round(subtotal, 2), round(discount_total, 2), round(tax_total, 2)


def compute_totals(draft: "DocDraft") -> "Totals":
    from ..models.document_models import Totals  # local import to avoid circular dependency
    subtotal, discount_total, tax_total = aggregate_totals(draft.items)
    shipping = float(draft.totals.shipping if draft.totals else 0.0)
    preliminary_total = subtotal - discount_total + tax_total + shipping
    rounded = round(preliminary_total)
    round_off = round(rounded - preliminary_total, 2)
    grand_total = round(preliminary_total + round_off, 2)
    amount_words = number_to_words_indian(grand_total)

    return Totals(
        subtotal=subtotal,
        discount_total=discount_total,
        tax_total=tax_total,
        shipping=shipping,
        round_off=round_off,
        grand_total=grand_total,
        amount_in_words=amount_words,
    )


def recompute_totals_from_dict(draft_dict: dict) -> dict:
    from ..models.document_models import DocDraft as DraftModel

    draft = DraftModel.model_validate(draft_dict)
    draft_dict.update(draft.model_dump())
    return draft_dict
