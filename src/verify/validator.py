"""Pre-submission validator enforcing all contract §12 assertions.

Architecture §4.11 deliverable.
Runs in-pipeline before output.csv is written.
Every assertion failure is a build stop naming request_id and assertion number.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
import re
from typing import Sequence

from explain.formatting import format_plan_amount
from models import (
    AffordabilityStatus,
    FinancialEvent,
    FinancialProfile,
    OutputRow,
    PaymentMethod,
    Request,
    RequestPaymentOption,
)


class ValidationError(Exception):
    """Raised when any contract assertion fails."""


VALID_STATUSES: set[str] = {
    AffordabilityStatus.AFFORDABLE_NOW.value,
    AffordabilityStatus.AFFORDABLE_WITH_PLAN.value,
    AffordabilityStatus.AFFORDABLE_LATER.value,
    AffordabilityStatus.NOT_AFFORDABLE.value,
}

VALID_METHODS: set[str] = {
    PaymentMethod.FULL_PAYMENT.value,
    PaymentMethod.PARTIAL_PAYMENT.value,
    PaymentMethod.INSTALLMENTS.value,
    PaymentMethod.WAIT.value,
    PaymentMethod.NOT_RECOMMENDED.value,
}

VALID_PAIRS: set[tuple[str, str]] = {
    (AffordabilityStatus.AFFORDABLE_NOW.value, PaymentMethod.FULL_PAYMENT.value),
    (AffordabilityStatus.AFFORDABLE_WITH_PLAN.value, PaymentMethod.FULL_PAYMENT.value),
    (AffordabilityStatus.AFFORDABLE_WITH_PLAN.value, PaymentMethod.INSTALLMENTS.value),
    (AffordabilityStatus.AFFORDABLE_WITH_PLAN.value, PaymentMethod.PARTIAL_PAYMENT.value),
    (AffordabilityStatus.AFFORDABLE_LATER.value, PaymentMethod.WAIT.value),
    (AffordabilityStatus.NOT_AFFORDABLE.value, PaymentMethod.NOT_RECOMMENDED.value),
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate_output_rows(
    output_rows: Sequence[OutputRow],
    requests: Sequence[Request],
    profiles: dict[str, FinancialProfile],
    events: Sequence[FinancialEvent],
    options_by_request: dict[str, list[RequestPaymentOption]],
) -> None:
    """Validate all output rows against contract §12 assertions before writing output.csv.

    Raises ValidationError on the first violating row naming request_id and assertion number.
    """
    # Assertion 1: Exactly 250 rows; request_id set matches requests.csv exactly
    if len(output_rows) != len(requests):
        raise ValidationError(
            f"Assertion 1 failed: expected {len(requests)} rows, got {len(output_rows)}"
        )
    for expected_req, actual_row in zip(requests, output_rows):
        if expected_req.request_id != actual_row.request_id:
            raise ValidationError(
                f"Assertion 1 failed on {actual_row.request_id}: expected {expected_req.request_id}"
            )

    requests_by_id = {r.request_id: r for r in requests}
    events_by_id = {e.event_id: e for e in events}

    for r in output_rows:
        rid = r.request_id
        req = requests_by_id[rid]
        profile = profiles[req.user_id]
        options = options_by_request.get(rid, [])

        # Assertion 3: No field is null except earliest_date_for_full_payment
        if r.amount_safe_to_pay is None or r.amount_safe_to_pay == "":
            raise ValidationError(f"Assertion 3 failed on {rid}: amount_safe_to_pay is empty/null")
        if r.affordability_status is None or r.affordability_status == "":
            raise ValidationError(f"Assertion 3 failed on {rid}: affordability_status is empty/null")
        if r.recommended_payment_method is None or r.recommended_payment_method == "":
            raise ValidationError(f"Assertion 3 failed on {rid}: recommended_payment_method is empty/null")
        if r.payment_plan is None or r.payment_plan == "":
            raise ValidationError(f"Assertion 3 failed on {rid}: payment_plan is empty/null")
        if r.spending_changes_needed is None or r.spending_changes_needed == "":
            raise ValidationError(f"Assertion 3 failed on {rid}: spending_changes_needed is empty/null")
        if r.decision_explanation is None or r.decision_explanation == "":
            raise ValidationError(f"Assertion 3 failed on {rid}: decision_explanation is empty/null")

        status_str = r.affordability_status
        method_str = r.recommended_payment_method
        safe_str = r.amount_safe_to_pay
        plan_str = r.payment_plan
        earliest_str = r.earliest_date_for_full_payment or ""
        changes_str = r.spending_changes_needed
        expl_str = r.decision_explanation

        # Assertion 4: affordability_status in 4 allowed values
        if status_str not in VALID_STATUSES:
            raise ValidationError(f"Assertion 4 failed on {rid}: invalid status {status_str}")

        # Assertion 5: recommended_payment_method in 5 allowed values
        if method_str not in VALID_METHODS:
            raise ValidationError(f"Assertion 5 failed on {rid}: invalid method {method_str}")

        # Assertion 6: 0 <= amount_safe_to_pay <= requested_amount
        try:
            safe_amt = Decimal(safe_str)
        except Exception as e:
            raise ValidationError(f"Assertion 6 failed on {rid}: cannot parse amount_safe_to_pay: {e}")
        if not (Decimal("0") <= safe_amt <= req.requested_amount):
            raise ValidationError(
                f"Assertion 6 failed on {rid}: safe amount {safe_amt} outside [0, {req.requested_amount}]"
            )

        # Assertion 7: (status, method) appears in §6.2 matrix
        if (status_str, method_str) not in VALID_PAIRS:
            raise ValidationError(
                f"Assertion 7 failed on {rid}: illegal pair ({status_str}, {method_str})"
            )

        # Assertion 8: payment_plan parses under §7.1; chronological
        if plan_str != "none":
            items = plan_str.split("|")
            prev_dt: date | None = None
            for item in items:
                parts = item.split(":")
                if len(parts) != 2 or not DATE_RE.match(parts[0]):
                    raise ValidationError(f"Assertion 8 failed on {rid}: malformed plan item '{item}'")
                try:
                    curr_dt = date.fromisoformat(parts[0])
                    _ = Decimal(parts[1])
                except Exception as e:
                    raise ValidationError(f"Assertion 8 failed on {rid}: invalid date/amount in '{item}': {e}")
                if prev_dt is not None and curr_dt < prev_dt:
                    raise ValidationError(
                        f"Assertion 8 failed on {rid}: plan dates out of chronological order"
                    )
                prev_dt = curr_dt

        # Assertion 9: full_payment => one payment, dated request_date, equal to requested_amount
        if method_str == PaymentMethod.FULL_PAYMENT.value:
            items = plan_str.split("|")
            if len(items) != 1:
                raise ValidationError(
                    f"Assertion 9 failed on {rid}: full_payment plan must have exactly 1 payment"
                )
            p_date_str, p_amt_str = items[0].split(":")
            if date.fromisoformat(p_date_str) != req.request_date or Decimal(p_amt_str) != req.requested_amount:
                raise ValidationError(
                    f"Assertion 9 failed on {rid}: full_payment plan {items[0]} does not match request"
                )

        # Assertion 10: wait => one payment, dated earliest_date_for_full_payment, equal to requested_amount
        if method_str == PaymentMethod.WAIT.value:
            items = plan_str.split("|")
            if len(items) != 1:
                raise ValidationError(f"Assertion 10 failed on {rid}: wait plan must have exactly 1 payment")
            p_date_str, p_amt_str = items[0].split(":")
            if p_date_str != earliest_str or Decimal(p_amt_str) != req.requested_amount:
                raise ValidationError(
                    f"Assertion 10 failed on {rid}: wait plan {items[0]} does not match earliest date {earliest_str}"
                )

        # Assertion 11: partial_payment => exactly two payments summing to requested_amount; 1st on request_date equal to safe_amount
        if method_str == PaymentMethod.PARTIAL_PAYMENT.value:
            items = plan_str.split("|")
            if len(items) != 2:
                raise ValidationError(
                    f"Assertion 11 failed on {rid}: partial_payment plan must have exactly 2 payments"
                )
            dt1, amt1 = items[0].split(":")
            dt2, amt2 = items[1].split(":")
            if date.fromisoformat(dt1) != req.request_date or Decimal(amt1) != safe_amt:
                raise ValidationError(
                    f"Assertion 11 failed on {rid}: first partial payment does not match request_date/safe_amount"
                )
            if Decimal(amt1) + Decimal(amt2) != req.requested_amount:
                raise ValidationError(
                    f"Assertion 11 failed on {rid}: partial payments sum {Decimal(amt1)+Decimal(amt2)} != {req.requested_amount}"
                )

        # Assertion 12: installments => reproduces supplied option exactly
        if method_str == PaymentMethod.INSTALLMENTS.value:
            items = plan_str.split("|")
            matched_option = False
            for opt in options:
                if opt.payment_method != PaymentMethod.INSTALLMENTS:
                    continue
                if len(items) != opt.number_of_payments:
                    continue
                freq = opt.payment_frequency_days or 30
                expected_plan_parts = [
                    f"{(opt.first_payment_date + timedelta(days=k * freq)).isoformat()}:{format_plan_amount(opt.payment_amount)}"
                    for k in range(opt.number_of_payments)
                ]
                if plan_str == "|".join(expected_plan_parts):
                    matched_option = True
                    break
            if not matched_option:
                raise ValidationError(
                    f"Assertion 12 failed on {rid}: installments plan {plan_str} does not match any supplied option"
                )

        # Assertion 13: not_recommended => payment_plan == 'none'
        if method_str == PaymentMethod.NOT_RECOMMENDED.value:
            if plan_str != "none":
                raise ValidationError(
                    f"Assertion 13 failed on {rid}: not_recommended must have plan 'none', got {plan_str}"
                )

        # Assertion 14: Every plan completes by desired_completion_date, except not_recommended
        if method_str != PaymentMethod.NOT_RECOMMENDED.value:
            items = plan_str.split("|")
            last_dt = date.fromisoformat(items[-1].split(":")[0])
            if last_dt > req.desired_completion_date:
                raise ValidationError(
                    f"Assertion 14 failed on {rid}: plan finishes on {last_dt} past desired {req.desired_completion_date}"
                )

        # Assertion 15: affordable_now => earliest_date_for_full_payment == request_date
        if status_str == AffordabilityStatus.AFFORDABLE_NOW.value:
            if earliest_str != req.request_date.isoformat():
                raise ValidationError(
                    f"Assertion 15 failed on {rid}: affordable_now requires earliest_date == {req.request_date}"
                )

        # Assertion 16 (Revised): not_affordable => earliest_date empty
        if status_str == AffordabilityStatus.NOT_AFFORDABLE.value:
            if earliest_str != "":
                raise ValidationError(
                    f"Assertion 16 failed on {rid}: not_affordable requires empty earliest_date, got '{earliest_str}'"
                )

        # Assertion 17 (Revised): All other statuses => populated and within 90 days, unless plan depends on spending changes
        if status_str != AffordabilityStatus.NOT_AFFORDABLE.value:
            if earliest_str == "":
                if changes_str == "none":
                    raise ValidationError(
                        f"Assertion 17 failed on {rid}: {status_str} without spending changes cannot have empty earliest_date"
                    )
            else:
                edt = date.fromisoformat(earliest_str)
                if not (req.request_date <= edt <= req.request_date + timedelta(days=90)):
                    raise ValidationError(
                        f"Assertion 17 failed on {rid}: earliest_date {edt} outside [ {req.request_date}, {req.request_date+timedelta(days=90)} ]"
                    )

        # Assertion 18: spending_changes_needed parses under §8.1; at most 3 changes
        if changes_str != "none":
            c_items = changes_str.split("|")
            if len(c_items) > 3:
                raise ValidationError(f"Assertion 18 failed on {rid}: more than 3 spending changes ({len(c_items)})")
            for c_item in c_items:
                c_parts = c_item.split(":")
                if c_parts[0] == "stop" and len(c_parts) == 2:
                    pass
                elif c_parts[0] == "reduce_to" and len(c_parts) == 3:
                    try:
                        _ = Decimal(c_parts[2])
                    except Exception as e:
                        raise ValidationError(f"Assertion 18 failed on {rid}: invalid reduce_to amount in {c_item}: {e}")
                else:
                    raise ValidationError(f"Assertion 18 failed on {rid}: malformed spending change '{c_item}'")

        # Assertion 19: Every cited event_id exists and belongs to this user_id
        if changes_str != "none":
            for c_item in changes_str.split("|"):
                eid = c_item.split(":")[1]
                ev = events_by_id.get(eid)
                if ev is None or ev.user_id != req.user_id:
                    raise ValidationError(
                        f"Assertion 19 failed on {rid}: cited event {eid} does not exist or belong to {req.user_id}"
                    )

        # Assertion 20: Operation permitted by event flexibility
        if changes_str != "none":
            for c_item in changes_str.split("|"):
                c_parts = c_item.split(":")
                act, eid = c_parts[0], c_parts[1]
                ev = events_by_id[eid]
                flx = ev.flexibility.value
                if act == "stop" and flx not in ("stoppable", "reducible_or_stoppable"):
                    raise ValidationError(f"Assertion 20 failed on {rid}: stop not permitted on flexibility {flx}")
                if act == "reduce_to" and flx not in ("reducible", "reducible_or_stoppable"):
                    raise ValidationError(f"Assertion 20 failed on {rid}: reduce_to not permitted on flexibility {flx}")

        # Assertion 21: Category in willingness list and NOT in expense_categories_to_protect
        if changes_str != "none":
            for c_item in changes_str.split("|"):
                c_parts = c_item.split(":")
                act, eid = c_parts[0], c_parts[1]
                ev = events_by_id[eid]
                if ev.category in profile.expense_categories_to_protect:
                    raise ValidationError(
                        f"Assertion 21 failed on {rid}: {ev.category} is protected for {req.user_id}"
                    )
                if act == "stop" and ev.category not in profile.expense_categories_user_is_willing_to_stop:
                    raise ValidationError(
                        f"Assertion 21 failed on {rid}: {ev.category} not in willingness-to-stop list"
                    )
                if act == "reduce_to" and ev.category not in profile.expense_categories_user_is_willing_to_reduce:
                    raise ValidationError(
                        f"Assertion 21 failed on {rid}: {ev.category} not in willingness-to-reduce list"
                    )

        # Assertion 22: No event_id appears with both stop and reduce_to
        if changes_str != "none":
            cited_eids = [it.split(":")[1] for it in changes_str.split("|")]
            if len(cited_eids) != len(set(cited_eids)):
                raise ValidationError(f"Assertion 22 failed on {rid}: duplicate cited event_id in {changes_str}")

        # Assertion 23: affordable_now & not_affordable have spending_changes_needed == 'none'
        if status_str in (AffordabilityStatus.AFFORDABLE_NOW.value, AffordabilityStatus.NOT_AFFORDABLE.value):
            if changes_str != "none":
                raise ValidationError(
                    f"Assertion 23 failed on {rid}: {status_str} must have changes 'none', got {changes_str}"
                )

        # Assertion 24: Explanation matches contract template structure
        if method_str == PaymentMethod.FULL_PAYMENT.value and status_str == AffordabilityStatus.AFFORDABLE_NOW.value:
            if not (expl_str.startswith("Pay ") and "over the next 90 days" in expl_str):
                raise ValidationError(f"Assertion 24 failed on {rid}: explanation does not match T1")
        elif method_str == PaymentMethod.FULL_PAYMENT.value and status_str == AffordabilityStatus.AFFORDABLE_WITH_PLAN.value:
            if not ("then pay " in expl_str and "leaves at least " in expl_str):
                raise ValidationError(f"Assertion 24 failed on {rid}: explanation does not match T2")
        elif method_str == PaymentMethod.INSTALLMENTS.value:
            if not (expl_str.startswith("Use ") and "installments of " in expl_str):
                raise ValidationError(f"Assertion 24 failed on {rid}: explanation does not match T3")
        elif method_str == PaymentMethod.WAIT.value:
            if not (expl_str.startswith("Pay ") and "in full on " in expl_str and "Paying earlier" in expl_str):
                raise ValidationError(f"Assertion 24 failed on {rid}: explanation does not match T4")
        elif method_str == PaymentMethod.PARTIAL_PAYMENT.value:
            if not (expl_str.startswith("Pay ") and "today and the remaining" in expl_str):
                raise ValidationError(f"Assertion 24 failed on {rid}: explanation does not match T5")
        elif method_str == PaymentMethod.NOT_RECOMMENDED.value:
            if not (expl_str.startswith("Do not make this payment by ") or expl_str.startswith("Do not proceed with the ")):
                raise ValidationError(f"Assertion 24 failed on {rid}: explanation does not match T6/T7")

        # Assertion 25: Numbers and dates in explanation agree with structured fields
        if method_str == PaymentMethod.WAIT.value:
            if earliest_str:
                edt = date.fromisoformat(earliest_str)
                edt_text = f"{edt.day} {edt.strftime('%B %Y')}"
                if edt_text not in expl_str:
                    raise ValidationError(
                        f"Assertion 25 failed on {rid}: explanation date does not match earliest_date {earliest_str}"
                    )
        elif method_str == PaymentMethod.NOT_RECOMMENDED.value:
            ddt = req.desired_completion_date
            ddt_text = f"{ddt.day} {ddt.strftime('%B %Y')}"
            if "proceed" not in expl_str and ddt_text not in expl_str:
                raise ValidationError(
                    f"Assertion 25 failed on {rid}: T6 explanation date does not match desired_date {ddt}"
                )

        # Assertion 26 (Revised): Method in payment_methods_user_will_consider (wait gated on full_payment per §6.1)
        if method_str != PaymentMethod.NOT_RECOMMENDED.value:
            required_consideration = (
                PaymentMethod.FULL_PAYMENT
                if method_str == PaymentMethod.WAIT.value
                else PaymentMethod(method_str)
            )
            if required_consideration not in profile.payment_methods_user_will_consider:
                raise ValidationError(
                    f"Assertion 26 failed on {rid}: user does not consider {required_consideration.value} for {method_str}"
                )

        # Assertion 27: partial_payment => allows_partial_payment == true
        if method_str == PaymentMethod.PARTIAL_PAYMENT.value:
            if not req.allows_partial_payment:
                raise ValidationError(
                    f"Assertion 27 failed on {rid}: partial_payment recommended when allows_partial_payment is False"
                )

        # Assertion 28: installments => number_of_payments <= max_installment_months
        if method_str == PaymentMethod.INSTALLMENTS.value:
            if profile.max_installment_months is not None:
                num_pmts = len(plan_str.split("|"))
                if num_pmts > profile.max_installment_months:
                    raise ValidationError(
                        f"Assertion 28 failed on {rid}: installments count {num_pmts} > max {profile.max_installment_months}"
                    )
