"""src/planner/candidates.py — Candidate payment plan generation and grammar formatting.

Per docs/architecture.md §4.6 and docs/decision-contract.md §6, §7.1:
Generates the FULL candidate set before any filtering:
  - full_payment on request_date, with and without each viable spending-change combination
  - every installments option, with and without each viable spending-change combination
  - partial_payment if gates clear
  - wait at earliest_date_for_full_payment
  - not_recommended

Installment dates: first_payment_date + k * payment_frequency_days.
Generation is deliberately over-inclusive. Filtering is the filter's job.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Sequence

from models import (
    Candidate,
    FinancialProfile,
    Payment,
    PaymentMethod,
    Request,
    RequestPaymentOption,
    SpendingChange,
)
from planner.spending import format_plan_amount


def format_payment_plan(candidate: Candidate) -> str:
    """Format candidate payments into the contract §7.1 payment_plan grammar.

    Grammar: <YYYY-MM-DD>:<amount>|<YYYY-MM-DD>:<amount>|...
    'none' when no payment is recommended.
    """
    if candidate.method == PaymentMethod.NOT_RECOMMENDED or not candidate.payments:
        return "none"
    return "|".join(f"{p.date}:{format_plan_amount(p.amount)}" for p in candidate.payments)


def generate_candidates(
    request: Request,
    profile: FinancialProfile,
    options: Sequence[RequestPaymentOption],
    viable_spending_combinations: Sequence[tuple[SpendingChange, ...]],
    amount_safe_to_pay: Decimal,
    earliest_date_for_full_payment: date | None,
) -> tuple[Candidate, ...]:
    """Generate the full, over-inclusive candidate set for evaluation.

    Candidate generation is deliberately over-inclusive; filtering and ranking
    determine the survivors and the optimal recommendation.
    """
    candidates: list[Candidate] = []

    # 1. full_payment on request_date (without and with each spending-change combination)
    full_pmt = Payment(date=request.request_date, amount=request.requested_amount)
    candidates.append(
        Candidate(
            method=PaymentMethod.FULL_PAYMENT,
            payments=(full_pmt,),
            spending_changes=(),
            payment_option_id=None,
            total_paid=request.requested_amount,
        )
    )
    for sc_combo in viable_spending_combinations:
        candidates.append(
            Candidate(
                method=PaymentMethod.FULL_PAYMENT,
                payments=(full_pmt,),
                spending_changes=sc_combo,
                payment_option_id=None,
                total_paid=request.requested_amount,
            )
        )

    # 2. Every installments option (without and with each spending-change combination)
    req_options = [
        o
        for o in options
        if o.request_id == request.request_id and o.payment_method == PaymentMethod.INSTALLMENTS
    ]
    for o in req_options:
        freq = o.payment_frequency_days or 0
        payments = tuple(
            Payment(
                date=o.first_payment_date + timedelta(days=k * freq),
                amount=o.payment_amount,
            )
            for k in range(o.number_of_payments)
        )
        # Without changes
        candidates.append(
            Candidate(
                method=PaymentMethod.INSTALLMENTS,
                payments=payments,
                spending_changes=(),
                payment_option_id=o.payment_option_id,
                total_paid=o.total_payable_amount,
            )
        )
        # With each viable combination
        for sc_combo in viable_spending_combinations:
            candidates.append(
                Candidate(
                    method=PaymentMethod.INSTALLMENTS,
                    payments=payments,
                    spending_changes=sc_combo,
                    payment_option_id=o.payment_option_id,
                    total_paid=o.total_payable_amount,
                )
            )

    # 3. partial_payment if gates clear (§6.1)
    if (
        PaymentMethod.PARTIAL_PAYMENT in profile.payment_methods_user_will_consider
        and request.allows_partial_payment is True
        and Decimal("0") < amount_safe_to_pay < request.requested_amount
        and earliest_date_for_full_payment is not None
        and earliest_date_for_full_payment <= request.desired_completion_date
    ):
        p1 = Payment(date=request.request_date, amount=amount_safe_to_pay)
        p2 = Payment(
            date=earliest_date_for_full_payment,
            amount=request.requested_amount - amount_safe_to_pay,
        )
        candidates.append(
            Candidate(
                method=PaymentMethod.PARTIAL_PAYMENT,
                payments=(p1, p2),
                spending_changes=(),
                payment_option_id=None,
                total_paid=request.requested_amount,
            )
        )

    # 4. wait at earliest_date_for_full_payment
    if earliest_date_for_full_payment is not None:
        candidates.append(
            Candidate(
                method=PaymentMethod.WAIT,
                payments=(
                    Payment(
                        date=earliest_date_for_full_payment,
                        amount=request.requested_amount,
                    ),
                ),
                spending_changes=(),
                payment_option_id=None,
                total_paid=request.requested_amount,
            )
        )

    # 5. not_recommended fallback
    candidates.append(
        Candidate(
            method=PaymentMethod.NOT_RECOMMENDED,
            payments=(),
            spending_changes=(),
            payment_option_id=None,
            total_paid=Decimal("0"),
        )
    )

    return tuple(candidates)
