"""Exact-date foreign exchange conversion and verification.

Rules:
  - Exact-date lookup only on (rate_date, from_currency, to_currency).
  - No interpolation, no nearest-date fallback, no reciprocal calculation.
  - A missing rate raises immediately.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date
from decimal import Decimal

from models import ExchangeRate, FinancialEvent, FinancialProfile


class FXTable:
    """Exact-date directed exchange rate lookup table."""

    def __init__(self, rates: Sequence[ExchangeRate]) -> None:
        self._rates: dict[tuple[date, str, str], Decimal] = {
            (r.rate_date, r.from_currency, r.to_currency): r.rate for r in rates
        }

    def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        on_date: date,
    ) -> Decimal:
        """Convert amount from from_currency to to_currency on on_date.

        Raises:
            KeyError: If exact directed rate on on_date is missing.
        """
        if from_currency == to_currency:
            return amount

        key = (on_date, from_currency, to_currency)
        if key not in self._rates:
            raise KeyError(
                f"Missing exact FX rate on {on_date} for {from_currency} -> {to_currency} (amount {amount})"
            )

        return amount * self._rates[key]

    def has_rate(self, from_currency: str, to_currency: str, on_date: date) -> bool:
        """Check if an exact rate exists."""
        if from_currency == to_currency:
            return True
        return (on_date, from_currency, to_currency) in self._rates


def build_fx_table(rates: Sequence[ExchangeRate]) -> FXTable:
    """Construct an FXTable from exchange rate records."""
    return FXTable(rates)


def verify_all_events_resolve(
    events: Sequence[FinancialEvent],
    profiles: Mapping[str, FinancialProfile],
    fx: FXTable,
) -> int:
    """Verify that every foreign-currency event in events resolves to home_currency.

    Returns:
        The count of resolved foreign currency events (must be exactly 140).

    Raises:
        ValueError: If fewer or more than 140 foreign currency events are encountered.
        KeyError: If any event fails to resolve.
    """
    foreign_count = 0
    for event in events:
        profile = profiles[event.user_id]
        if event.currency != profile.home_currency:
            # Must resolve on event_date without error
            fx.convert(
                amount=event.amount,
                from_currency=event.currency,
                to_currency=profile.home_currency,
                on_date=event.event_date,
            )
            foreign_count += 1

    if foreign_count != 140:
        raise ValueError(
            f"Expected exactly 140 foreign currency events, resolved {foreign_count}"
        )

    return foreign_count
