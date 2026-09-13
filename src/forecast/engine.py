"""forecast/engine.py — Day-resolution balance curve forecast engine.

Pure function, per docs/architecture.md §4.5:
  project(opening_balance, start, horizon_days, flows) -> BalanceCurve

BalanceCurve exposes trough(), trough_date(), and balance_on(date).
No affordability logic. It projects; it does not judge.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Sequence

from models import Direction, Flow


@dataclass(frozen=True)
class BalanceCurve:
    """Projected daily balance curve across a forward window."""

    opening_balance: Decimal
    start: date
    horizon_days: int
    daily_balances: dict[date, Decimal]
    _trough: Decimal
    _trough_date: date

    def trough(self) -> Decimal:
        """Return the minimum running balance across the forecast window."""
        return self._trough

    def trough_date(self) -> date:
        """Return the date on which the trough balance occurs (first occurrence if tied)."""
        return self._trough_date

    def balance_on(self, d: date) -> Decimal:
        """Return the projected balance at the end of date d."""
        if d not in self.daily_balances:
            raise KeyError(
                f"Date {d} outside forecast window [{self.start}, {self.start + timedelta(days=self.horizon_days)}]"
            )
        return self.daily_balances[d]


def project(
    opening_balance: Decimal,
    start: date,
    horizon_days: int,
    flows: Sequence[Flow],
) -> BalanceCurve:
    """Project running balances day-by-day across [start, start + horizon_days] inclusive.

    Pure function: deterministic, side-effect free. Balance is derived from flows,
    never stored or carried.
    """
    window_end = start + timedelta(days=horizon_days)
    daily_delta: dict[date, Decimal] = defaultdict(Decimal)

    for f in flows:
        if start <= f.date <= window_end:
            if f.direction == Direction.CREDIT:
                daily_delta[f.date] += f.amount
            elif f.direction == Direction.DEBIT:
                daily_delta[f.date] -= f.amount

    running = opening_balance
    trough: Decimal | None = None
    trough_date = start
    daily_balances: dict[date, Decimal] = {}

    for day_offset in range(horizon_days + 1):
        dt = start + timedelta(days=day_offset)
        running += daily_delta.get(dt, Decimal("0"))
        daily_balances[dt] = running
        if trough is None or running < trough:
            trough = running
            trough_date = dt

    assert trough is not None
    return BalanceCurve(
        opening_balance=opening_balance,
        start=start,
        horizon_days=horizon_days,
        daily_balances=daily_balances,
        _trough=trough,
        _trough_date=trough_date,
    )
