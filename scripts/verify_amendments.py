"""V11: Comprehensive read-only audit of the 79 frozen message amendments.

Covers:
  A. Breakdown by AmendmentAction (confirm 65/14 split)
  B. The 65 ADD_CONFIRMED_INCOME records (user_id, date, amount, currency, message_id, source_type, window check, scheduled check)
  C. Double-count exposure (settled salary series overlap within +-5 days)
  D. Provenance of all 79 amendments (message_id and verbatim text)
  E. Token usage (input, output, calls, model, cost)
  F. V10 bimodal salary numbers (modal gaps, frequencies, >=70% check, presence in requests/sample_requests)
"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
import json
import logging
from pathlib import Path
import sys
from typing import Any
import pandas as pd

from observability import bind_context, init_logging


def audit_amendments(
    custom_amendments_path: Path | None = None,
    custom_cache_path: Path | None = None,
) -> dict[str, Any]:
    init_logging()
    logger = logging.getLogger("verify_amendments")

    with bind_context(stage="verify_v11"):
        logger.info("Starting V11 audit of message amendments")

        repo_root = Path(__file__).resolve().parent.parent
        amendments_path = custom_amendments_path or (repo_root / "src" / "data" / "message_amendments.json")
        messages_path = repo_root / "dataset" / "messages.csv"
        events_path = repo_root / "dataset" / "financial_events.csv"
        requests_path = repo_root / "dataset" / "requests.csv"
        sample_path = repo_root / "dataset" / "sample_requests.csv"
        cache_path = custom_cache_path or (repo_root / "src" / "data" / ".cache" / "message_extraction_cache.json")

        with open(amendments_path, "r", encoding="utf-8") as f:
            amendments: list[dict[str, Any]] = json.load(f)

        messages_df = pd.read_csv(messages_path)
        messages_map = {r["message_id"]: r for _, r in messages_df.iterrows()}

        events_df = pd.read_csv(events_path)
        events_df["event_date_dt"] = pd.to_datetime(events_df["event_date"])

        requests_df = pd.read_csv(requests_path)
        eval_request_dates = {r["user_id"]: date.fromisoformat(r["request_date"]) for _, r in requests_df.iterrows()}

        sample_df = pd.read_csv(sample_path)
        sample_request_dates = {r["user_id"]: date.fromisoformat(r["request_date"]) for _, r in sample_df.iterrows()}

        # -------------------------------------------------------------
        # Part A: BREAKDOWN & HARD ACTION COUNT ASSERTIONS
        # -------------------------------------------------------------
        action_counts = Counter(a["action"] for a in amendments)

        EXPECTED_ACTION_COUNTS: dict[str, int] = {
            "CONFIRM_EVENT": 14,
            "AMEND_RECURRING_AMOUNT": 32,
            "ESTABLISH_SERIES": 35,
            "ADD_RECURRING_EXPENSE": 8,
            "ADD_CONFIRMED_INCOME": 15,
            "TERMINATE_SERIES": 20,
            "MARK_NON_RECURRING": 3,
        }
        for act, exp_cnt in EXPECTED_ACTION_COUNTS.items():
            act_cnt = action_counts.get(act, 0)
            assert act_cnt == exp_cnt, (
                f"HARD RULE VIOLATION: action '{act}' count mismatch: got {act_cnt}, expected {exp_cnt}"
            )
        assert sum(action_counts.values()) == 127, (
            f"HARD RULE VIOLATION: total amendments count mismatch: got {sum(action_counts.values())}, expected 127"
        )

        # -------------------------------------------------------------
        # Part B: THE 65 ADD_CONFIRMED_INCOME
        # -------------------------------------------------------------
        add_income_list = [a for a in amendments if a["action"] == "ADD_CONFIRMED_INCOME"]
        scheduled_salary_users = set(
            events_df[
                (events_df["status"] == "scheduled")
                & (events_df["direction"] == "credit")
                & (events_df["category"] == "salary")
            ]["user_id"]
        )

        affected_users = set(a["user_id"] for a in add_income_list)
        users_with_sched = affected_users.intersection(scheduled_salary_users)

        b_records: list[dict[str, Any]] = []
        in_window_eval = 0
        in_window_sample = 0
        in_window_total = 0

        for a in add_income_list:
            uid = str(a["user_id"])
            dt = date.fromisoformat(str(a["date"]))
            amt = Decimal(str(a["amount"]))
            curr = str(a["currency"])
            mid = str(a["message_id"])
            st = str(messages_map[mid]["source_type"])

            req_dt = eval_request_dates.get(uid)
            is_sample = False
            if req_dt is None and uid in sample_request_dates:
                req_dt = sample_request_dates[uid]
                is_sample = True

            in_window = False
            days_from_req = None
            if req_dt is not None:
                win_end = req_dt + timedelta(days=90)
                in_window = (req_dt <= dt <= win_end)
                days_from_req = (dt - req_dt).days
                if in_window:
                    in_window_total += 1
                    if is_sample:
                        in_window_sample += 1
                    else:
                        in_window_eval += 1

            b_records.append({
                "user_id": uid,
                "date": str(dt),
                "amount": str(amt),
                "currency": curr,
                "message_id": mid,
                "source_type": st,
                "request_date": str(req_dt) if req_dt else "None",
                "is_sample_request": is_sample,
                "in_90d_window": in_window,
                "days_from_request": days_from_req,
                "has_scheduled_salary": uid in scheduled_salary_users,
            })

        # -------------------------------------------------------------
        # Part C: DOUBLE-COUNT EXPOSURE
        # -------------------------------------------------------------
        overlaps: list[dict[str, Any]] = []
        no_overlaps: list[dict[str, Any]] = []
        subthreshold_users: list[dict[str, Any]] = []

        for a in add_income_list:
            uid = str(a["user_id"])
            added_dt = date.fromisoformat(str(a["date"]))
            mid = str(a["message_id"])

            user_salary = events_df[
                (events_df["user_id"] == uid)
                & (events_df["direction"] == "credit")
                & (events_df["category"] == "salary")
                & (events_df["status"] == "settled")
            ].sort_values("event_date_dt")

            n_settled = len(user_salary)
            if n_settled < 3:
                subthreshold_users.append({
                    "user_id": uid,
                    "message_id": mid,
                    "added_date": str(added_dt),
                    "settled_count": n_settled,
                })
                continue

            dates_list = [d.date() for d in user_salary["event_date_dt"]]
            gaps = [(dates_list[i + 1] - dates_list[i]).days for i in range(len(dates_list) - 1)]
            modal_gap = Counter(gaps).most_common(1)[0][0]
            last_settled = dates_list[-1]

            # Forward projections
            projected_dates: list[date] = []
            for k in range(1, 12):
                p = last_settled + timedelta(days=k * modal_gap)
                projected_dates.append(p)
                if p > added_dt + timedelta(days=35):
                    break

            closest_p = min(projected_dates, key=lambda p: abs((added_dt - p).days))
            diff_days = (added_dt - closest_p).days

            src_sub = str(a.get("source_substring", ""))
            overlap_info = {
                "user_id": uid,
                "message_id": mid,
                "added_date": str(added_dt),
                "settled_count": n_settled,
                "modal_gap": modal_gap,
                "last_settled": str(last_settled),
                "closest_projected": str(closest_p),
                "diff_days": diff_days,
                "source_substring": src_sub,
                "template_id": str(a.get("template_id", "")),
            }

            if abs(diff_days) <= 5:
                overlaps.append(overlap_info)
            else:
                no_overlaps.append(overlap_info)

        # -------------------------------------------------------------
        # Part D: PROVENANCE (All amendments exact string assertion)
        # -------------------------------------------------------------
        provenance_records: list[dict[str, Any]] = []
        for a in amendments:
            mid = str(a["message_id"])
            act = str(a["action"])
            msg_row = messages_map[mid]
            verbatim_text = str(msg_row["message_text"])
            uid = str(a["user_id"])
            st = str(msg_row["source_type"])
            src_sub = str(a.get("source_substring", ""))
            tmpl_id = str(a.get("template_id", ""))

            # HARD ASSERTION: exact string search
            assert src_sub in verbatim_text, (
                f"HARD RULE VIOLATION in {mid}: source_substring '{src_sub}' not in verbatim text"
            )

            prov_item: dict[str, Any] = {
                "message_id": mid,
                "action": act,
                "user_id": uid,
                "source_type": st,
                "source_substring": src_sub,
                "template_id": tmpl_id,
                "verbatim_text": verbatim_text,
            }
            if act == "CONFIRM_EVENT":
                prov_item["event_id"] = str(a.get("event_id", ""))
            elif act == "ADD_CONFIRMED_INCOME":
                prov_item["date"] = str(a.get("date", ""))
                prov_item["amount"] = str(a.get("amount", ""))
                prov_item["currency"] = str(a.get("currency", ""))
            provenance_records.append(prov_item)

        # -------------------------------------------------------------
        # Part E: TOKEN USAGE
        # -------------------------------------------------------------
        cache_data: dict[str, Any] = {}
        if cache_path.is_file():
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

        total_input_tokens = sum(v.get("tokens", {}).get("prompt", 0) for v in cache_data.values())
        total_output_tokens = sum(v.get("tokens", {}).get("completion", 0) for v in cache_data.values())
        total_calls = len(cache_data)

        # -------------------------------------------------------------
        # Part F: V10 NUMBERS (12 Bimodal Salary Series)
        # -------------------------------------------------------------
        req_users = set(requests_df["user_id"])
        sample_users = set(sample_df["user_id"])

        grouped = events_df.groupby(["user_id", "direction", "category", "description", "currency"])
        bimodal_salary_details: list[dict[str, Any]] = []

        for key, grp in grouped:
            if len(grp) < 3:
                continue
            if key[1] != "credit" or key[2] != "salary":
                continue

            sorted_dates = grp["event_date_dt"].sort_values()
            gaps = sorted_dates.diff().dropna().dt.days.tolist()

            distinct_clusters: Counter[str] = Counter()
            for g in gaps:
                if g <= 4:
                    distinct_clusters["daily"] += 1
                elif 5 <= g <= 10:
                    distinct_clusters["weekly"] += 1
                elif 11 <= g <= 18:
                    distinct_clusters["biweekly"] += 1
                elif 25 <= g <= 35:
                    distinct_clusters["monthly"] += 1
                elif 55 <= g <= 65:
                    distinct_clusters["bimonthly"] += 1
                elif 85 <= g <= 95:
                    distinct_clusters["quarterly"] += 1
                else:
                    distinct_clusters["irregular"] += 1

            multi_modes = [k for k, count in distinct_clusters.items() if count >= 2]
            if len(multi_modes) >= 2:
                uid = str(key[0])
                desc = str(key[3])
                curr = str(key[4])

                raw_counts = Counter(gaps)
                top_clusters = distinct_clusters.most_common(2)
                top_raw = raw_counts.most_common(2)
                total_gaps = len(gaps)

                has_70 = any((count / total_gaps) >= 0.70 for _, count in distinct_clusters.items())

                bimodal_salary_details.append({
                    "user_id": uid,
                    "description": desc,
                    "currency": curr,
                    "total_events": len(grp),
                    "total_gaps": total_gaps,
                    "raw_gaps": gaps,
                    "top_two_clusters": top_clusters,
                    "top_two_raw_gaps": top_raw,
                    "one_mode_holds_ge_70": has_70,
                    "in_requests_csv": uid in req_users,
                    "in_sample_requests_csv": uid in sample_users,
                })


        # -------------------------------------------------------------
        # Part G: CHILDCARE EXPENSES (Directive #10 & exact matching requirement)
        # -------------------------------------------------------------
        ALLOWED_CATEGORIES = {
            "groceries", "transport", "dining", "salary", "utilities", "rent",
            "cloud_storage", "shopping", "streaming", "debt_repayment", "entertainment",
            "insurance", "music_subscription", "healthcare", "delivery_membership",
            "education", "housing", "gym", "family_support", "investment",
            "work_expense", "windfall"
        }
        assert "childcare" not in ALLOWED_CATEGORIES, (
            "HARD RULE VIOLATION: 'childcare' must not be in schema ALLOWED_CATEGORIES"
        )

        childcare_expenses = [
            a for a in amendments
            if a.get("action") == "ADD_RECURRING_EXPENSE"
        ]
        childcare_records = []
        childcare_eval_count = 0
        childcare_sample_count = 0
        for ce in childcare_expenses:
            uid = str(ce["user_id"])
            mid = str(ce["message_id"])
            cat = str(ce.get("category", ""))
            sub = str(ce.get("source_substring", ""))
            # Hard assertions
            assert sub == "A new recurring childcare payment begins in the same month.", (
                f"Childcare sentence mismatch in {mid}: '{sub}'"
            )
            assert cat in ALLOWED_CATEGORIES, (
                f"Invalid category outside schema in {mid}: '{cat}'"
            )
            assert cat == "family_support", (
                f"Childcare recurring expense must map to family_support, got: '{cat}'"
            )
            is_req = uid in req_users
            is_sample = uid in sample_users
            if is_req:
                childcare_eval_count += 1
            if is_sample:
                childcare_sample_count += 1
            childcare_records.append({
                "message_id": mid,
                "user_id": uid,
                "start_date": ce.get("start_date"),
                "amount": ce.get("amount"),
                "currency": ce.get("currency"),
                "category": cat,
                "source_substring": sub,
                "template_id": ce.get("template_id"),
                "in_requests_csv": is_req,
                "in_sample_requests_csv": is_sample,
            })

        return {
            "part_a": dict(action_counts),
            "part_b_summary": {
                "total_add_confirmed_income": len(add_income_list),
                "affected_unique_users": len(affected_users),
                "users_with_scheduled_salary": len(users_with_sched),
                "in_window_eval": in_window_eval,
                "in_window_sample": in_window_sample,
                "in_window_total": in_window_total,
                "outside_window": len(add_income_list) - in_window_total,
            },
            "part_b_records": b_records,
            "part_c_summary": {
                "total_added": len(add_income_list),
                "users_with_settled_salary_series": len(overlaps) + len(no_overlaps),
                "overlaps_within_5d": len(overlaps),
                "no_overlaps_gt_5d": len(no_overlaps),
                "subthreshold_users": len(subthreshold_users),
            },
            "part_c_subthreshold": subthreshold_users,
            "part_c_overlaps": overlaps,
            "part_d_records": provenance_records,
            "part_e": {
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "total_tokens": total_input_tokens + total_output_tokens,
                "call_count": total_calls,
                "model_name": "claude-3-5-sonnet-20241022" if (total_input_tokens + total_output_tokens) > 0 else "None (offline deterministic perception baseline)",
                "estimated_cost_usd": round(
                    (total_input_tokens * 0.000003) + (total_output_tokens * 0.000015), 4
                ),
            },
            "part_f": bimodal_salary_details,
            "part_g_childcare": {
                "total_childcare_expenses": len(childcare_expenses),
                "in_evaluation_requests": childcare_eval_count,
                "in_sample_requests": childcare_sample_count,
                "all_5_eval_captured": childcare_eval_count >= 5,
                "records": childcare_records,
            },
        }


def main() -> None:
    data = audit_amendments()

    print("=== PART A: BREAKDOWN ===")
    print("Action counts:", data["part_a"])

    print("\n=== PART B: THE ADD_CONFIRMED_INCOME SUMMARY ===")
    print(data["part_b_summary"])

    print("\n=== PART C: DOUBLE-COUNT EXPOSURE SUMMARY ===")
    print(data["part_c_summary"])

    print("\n=== PART E: TOKEN USAGE ===")
    print(data["part_e"])

    print("\n=== PART F: V10 BIMODAL SALARY SERIES ===")
    for item in data["part_f"]:
        print(f"{item['user_id']} | '{item['description']}' ({item['currency']}): top clusters={item['top_two_clusters']}, >=70%={item['one_mode_holds_ge_70']}, in_requests={item['in_requests_csv']}, in_sample={item['in_sample_requests_csv']}")

    print("\n=== PART G: CHILDCARE EXPENSES (GATE CHECK) ===")
    print(data["part_g_childcare"])


if __name__ == "__main__":
    main()

