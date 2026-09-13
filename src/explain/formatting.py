"""Formatting utilities for payment plans and decision explanations.

Governed by docs/decision_contract.md §7.1 and §11.1.
Two distinct contexts:
  - payment_plan: no thousands separators, no currency code (e.g. '15952906.67')
  - decision_explanation: thousands separators, ISO prefix (e.g. 'IDR 15,952,906.67')
Shared:
  - Whole numbers bare (e.g. '25256' / 'ZAR 25,256')
  - Non-whole to exactly 2 decimal places with trailing zeros kept (e.g. '23.50' / 'USD 23.50')
  - Dates in explanations: D Month YYYY, no leading zero (e.g. '8 August 2025')
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, ROUND_DOWN


def format_plan_amount(amt: Decimal) -> str:
    """Format numeric amount for payment_plan and amount_safe_to_pay (§7.1).

    No separators, no currency prefix. Whole numbers bare, non-whole to 2dp.
    """
    if amt == amt.to_integral_value():
        return str(int(amt))
    return f"{amt.quantize(Decimal('0.01'), rounding=ROUND_DOWN):.2f}"


def format_explanation_amount(amt: Decimal, currency: str) -> str:
    """Format currency amount for decision_explanation (§11.1).

    Thousands separators, ISO prefix. Whole numbers bare, non-whole to 2dp.
    Example: 'IDR 15,952,906.67', 'INR 122,500', 'USD 23.50'.
    """
    if amt == amt.to_integral_value():
        return f"{currency} {int(amt):,}"
    q = amt.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    int_part = int(q)
    dec_part = str(q).split(".")[1]
    return f"{currency} {int_part:,}.{dec_part}"


def format_explanation_date(dt: date) -> str:
    """Format date for decision_explanation (§11.1).

    Format: D Month YYYY, no leading zero on day.
    Example: '8 August 2025', '15 November 2019'.
    """
    return f"{dt.day} {dt.strftime('%B %Y')}"
