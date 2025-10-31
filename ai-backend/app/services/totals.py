"""Totals computation service with Indian numbering"""
from typing import Dict, Any, List


def number_to_words_indian(num: float) -> str:
    """Convert number to words using Indian numbering system"""
    if num == 0:
        return "Zero Rupees Only"

    # Handle decimals
    rupees = int(num)
    paise = int(round((num - rupees) * 100))

    # Indian number words
    ones = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    teens = ["Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen",
             "Sixteen", "Seventeen", "Eighteen", "Nineteen"]

    def convert_below_hundred(n: int) -> str:
        if n == 0:
            return ""
        elif n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        else:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 != 0 else "")

    def convert_below_thousand(n: int) -> str:
        if n == 0:
            return ""
        elif n < 100:
            return convert_below_hundred(n)
        else:
            return ones[n // 100] + " Hundred" + (" " + convert_below_hundred(n % 100) if n % 100 != 0 else "")

    # Indian numbering: crore, lakh, thousand, hundred
    crore = rupees // 10000000
    lakh = (rupees % 10000000) // 100000
    thousand = (rupees % 100000) // 1000
    hundred = rupees % 1000

    result = []

    if crore > 0:
        result.append(convert_below_hundred(crore) + " Crore")
    if lakh > 0:
        result.append(convert_below_hundred(lakh) + " Lakh")
    if thousand > 0:
        result.append(convert_below_hundred(thousand) + " Thousand")
    if hundred > 0:
        result.append(convert_below_thousand(hundred))

    words = " ".join(result) + " Rupees"

    if paise > 0:
        words += " and " + convert_below_hundred(paise) + " Paise"

    return words + " Only"


def compute_line_totals(item: Dict[str, Any]) -> Dict[str, Any]:
    """Compute line_total and line_tax for a single item"""
    qty = float(item.get("qty", 0))
    unit_price = float(item.get("unit_price", 0))
    discount = float(item.get("discount", 0))
    tax_rate = float(item.get("tax_rate", 0))

    line_total = (qty * unit_price) - discount
    line_tax = line_total * (tax_rate / 100)

    item["line_total"] = round(line_total, 2)
    item["line_tax"] = round(line_tax, 2)

    return item


def compute_totals(items: List[Dict[str, Any]], currency: str = "INR") -> Dict[str, Any]:
    """Compute totals from line items"""
    subtotal = 0.0
    discount_total = 0.0
    tax_total = 0.0

    for item in items:
        subtotal += float(item.get("line_total", 0))
        discount_total += float(item.get("discount", 0))
        tax_total += float(item.get("line_tax", 0))

    shipping = 0.0  # Can be passed as parameter if needed

    grand_total = subtotal + tax_total + shipping
    round_off = round(grand_total) - grand_total
    grand_total = round(grand_total)

    amount_in_words = number_to_words_indian(grand_total)

    return {
        "subtotal": round(subtotal, 2),
        "discount_total": round(discount_total, 2),
        "tax_total": round(tax_total, 2),
        "shipping": round(shipping, 2),
        "round_off": round(round_off, 2),
        "grand_total": grand_total,
        "currency": currency,
        "amount_in_words": amount_in_words
    }


def recompute_draft_totals(draft: Dict[str, Any]) -> Dict[str, Any]:
    """Recompute all totals for a draft"""
    items = draft.get("items", [])

    # Recompute each line item
    for i, item in enumerate(items):
        items[i] = compute_line_totals(item)
        items[i]["sno"] = i + 1  # Ensure serial numbers

    # Recompute totals
    currency = draft.get("totals", {}).get("currency", "INR")
    draft["totals"] = compute_totals(items, currency)
    draft["items"] = items

    return draft
