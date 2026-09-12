# Decision Contract

**Status:** Phase 0.3 deliverable. Normative.
**Scope:** Defines *what* the system must output and *under which rules*. It does not define *how* the code is organized — that is `architecture.md` (Phase 0.4).
**Sources:** `DNA.md` (specification) and `docs/data-profile.md` (observed dataset, 0.1).
**Consumers:** the planner, the deterministic verifier, the explanation builder, and the pre-submission validator.

Confidence is marked per rule:

- `[SPEC]` — stated directly in DNA.md. Non-negotiable.
- `[DERIVED]` — proven by exact reconciliation against the 25-row calibration set or the profile counts.
- `[ASSUMED]` — a working decision that the sample cannot settle. Every one of these is listed again in §13.

---

## 1. Output schema

One row per row of `requests.csv`. 250 rows. Header, verbatim and in this order:

```csv
request_id,amount_safe_to_pay,affordability_status,recommended_payment_method,payment_plan,earliest_date_for_full_payment,spending_changes_needed,decision_explanation
```

| Field | Type | Format | Empty allowed |
|---|---|---|---|
| `request_id` | string | as supplied in `requests.csv` | no |
| `amount_safe_to_pay` | number | plain numeric, no separators, no currency code | no |
| `affordability_status` | enum | 4 values, §6 | no |
| `recommended_payment_method` | enum | 5 values, §6 | no |
| `payment_plan` | string | §7 grammar, or `none` | no |
| `earliest_date_for_full_payment` | date | `YYYY-MM-DD` | **yes** — §6.3 |
| `spending_changes_needed` | string | §8 grammar, or `none` | no |
| `decision_explanation` | string | §11 template output | no |

Hard invariants, enforced by the validator before any file is written:

- `0 <= amount_safe_to_pay <= requested_amount` `[SPEC]`
- All monetary output is in the user's `home_currency` `[SPEC]`
- `affordable_now` ⟹ `earliest_date_for_full_payment == request_date` `[SPEC]`
- Row count is exactly 250 and `request_id` set matches `requests.csv` exactly `[SPEC]`

---

## 2. Forecast window and the safety test

**Window.** `request_date` through `request_date + 90 days`, inclusive. `[SPEC]`

**The safety test.** A candidate plan is *safe* if and only if, for every day in the window, the projected running balance is `>= minimum_balance_to_keep`, with the candidate's own payments applied on their scheduled dates, all protected and essential obligations applied on theirs, and confirmed income credited on its. `[SPEC]`

**Additional conditions for a plan to be recommendable** `[SPEC]`:

1. Every payment in the plan is itself affordable on its own date.
2. The plan completes the **full** `requested_amount` on or before `desired_completion_date`.
3. Protected expense categories are never sacrificed to make the plan work.

**Balance is derived, never stored.** `current_available_balance` is the opening value at `request_date`; every subsequent day is computed from it. `[SPEC]`

---

## 3. Cash-flow inclusion rules

`financial_events.csv` carries 25,342 rows across 8 `event_type` values, 6 `status` values, and 3 `direction` values. The inclusion decision is made on `(status, direction, event_type)`.

### 3.1 Inclusion matrix

| `status` | Rows | `direction` | Treatment |
|---|---|---|---|
| `settled` | 25,148 | debit / credit | **Include.** Historical fact; also the substrate for recurrence reconstruction (§4) |
| `scheduled` | 70 | debit / credit | **Include.** These are the "confirmed future payments" and the "next confirmed salary" `[ASSUMED-1]` |
| `pending` | 71 | **debit** | **Include** as an encumbrance on its effective date `[ASSUMED-2]` |
| `pending` | 71 | **credit** | **Exclude.** Named explicitly in DNA.md `[SPEC]` |
| `cancelled` | 22 | any | **Exclude** `[SPEC]` |
| `failed` | 21 | any | **Exclude** `[SPEC]` |
| `unrealized` | 10 | `non_cash` | **Exclude** `[SPEC]` |

**Note on `unrealized`.** The profile shows `unrealized` (10) = `non_cash` (10) = `investment_valuation` (10). These are the same 10 rows. A single exclusion rule on `status == 'unrealized'` removes all of them; no separate `non_cash` or `investment_valuation` handling is required. `[DERIVED]`

### 3.2 Sign convention

`amount` is **strictly positive everywhere** (min 2.0, max 48,830,000.0, zero negatives). Direction is carried solely by the `direction` column. `[DERIVED]`

```
debit    → balance decreases
credit   → balance increases
non_cash → excluded entirely, never touches the balance
```

Code must never infer direction from sign.

### 3.3 Date to use

`settlement_date` where present (null on 10 rows only), otherwise `event_date`. `[ASSUMED-3]`

### 3.4 Duplicates

DNA.md orders that duplicate records be ignored, but `financial_events.csv` has **no duplicate flag column**. Detection must therefore be derived. Rule: two rows are duplicates when they share `(user_id, description, category, amount, currency, event_date, direction)` and differ only in `event_id`. Keep the lowest `event_id`; drop the rest. `[ASSUMED-4]`

This section is **conditional**. If the duplicate scan (verification 3) returns zero collisions, this logic is removed from the build entirely rather than carried as dead code.

### 3.5 Blank amounts

Exactly 16 rows have a null `amount`, and all 16 map 1:1 to a row in `images.csv`. A blank amount is **never** zero. `[SPEC]`

The 16 blocked events: `event_253`, `event_1442`, `event_1545`, `event_1700`, `event_1786`, `event_3051`, `event_3231`, `event_4535`, `event_5170`, `event_6033`, `event_6859`, `event_7307`, `event_7941`, `event_9421`, `event_9806`, `event_10521`.

Until Phase 0.2 supplies these values, any forecast touching one of these 16 users is **incomplete and must not be scored as final**. The engine flags the request rather than silently proceeding on a partial balance.

---

## 4. Recurrence reconstruction

**This is the highest-risk deterministic component in the build.**

`financial_events.csv` has **no `is_recurring` column and no recurrence-interval column**. `request_payment_options.csv` has `payment_frequency_days`, but that governs *request financing*, not the user's existing obligations. Recurrence must be reconstructed from history. `[DERIVED]`

Requirements on the reconstruction:

1. Group candidate series by `(user_id, description, category, direction)`. `description` has only 164 distinct values across 25,342 rows, so it is a stable series key. `[DERIVED]`
2. Infer the interval from the spacing of `event_date` within each group. Monthly cadence is expected to dominate; do not hardcode 30 days.
3. Project the series forward across the 90-day window from the last observed occurrence.
4. Amount for the projected occurrence: the most recent settled amount in the series. `[ASSUMED-5]`
5. A series must be distinguished from one-time purchases, transfers, refunds, and unusual events. `[SPEC]`

**Signals available for recurring-ness:**

- `event_type` of `subscription` (2,488) or `debt_payment` (567) is strong evidence.
- `event_type` of `income` (1,696) with `category == 'salary'` (1,690) is the salary series.
- `flexibility != 'fixed'` (4,204 rows) implies the event is a controllable commitment — i.e. recurring — since a one-off purchase has nothing to reduce or stop.
- `event_type` of `refund` (22), `investment_sale` (5), `investment_purchase` (29) are one-time by nature.

**Non-recurring by definition:** `refund`, `investment_valuation`, `investment_sale`, `investment_purchase`.

---

## 5. Currency normalization

All output is in `home_currency`. `[SPEC]`

- 140 events carry `currency != home_currency`.
- All 140 resolve to an **exact dated rate** on `(rate_date == event_date, from_currency, to_currency)`. Zero gaps. `[DERIVED]`

**Rule:** exact-date lookup only. Do **not** implement rate interpolation, nearest-date fallback, or inverse-pair derivation — the data proves none is needed, and each would be a silent-error surface. If a lookup misses, that is a bug or a data change: fail loudly. `[DERIVED]`

Available directed pairs: `USD→INR`, `USD→IDR`, `USD→EUR`, `EUR→USD`, `EUR→ZAR`. Rates are directed; `from` and `to` are not interchangeable.

---

## 6. Status ↔ method legality

### 6.1 Eligibility gates

A payment method is *eligible* only if it clears every gate below. Gates are hard filters applied **before** ranking.

| Method | Gates |
|---|---|
| `full_payment` | `'full_payment' ∈ payment_methods_user_will_consider` `[SPEC]` |
| `partial_payment` | `'partial_payment' ∈ methods` **and** `allows_partial_payment == true` **and** `0 < amount_safe_to_pay < requested_amount` **and** `earliest_date_for_full_payment <= desired_completion_date` `[SPEC]` |
| `installments` | `'installments' ∈ methods` **and** at least one option exists in `request_payment_options.csv` **and** `number_of_payments <= max_installment_months` `[ASSUMED-6]` |
| `wait` | `'full_payment' ∈ methods` **and** full payment becomes safe later within the window `[SPEC]` |
| `not_recommended` | fallback when no eligible method is safe `[SPEC]` |

**Structural consequences from the profile** `[DERIVED]`:

- 112 of 275 users exclude `full_payment`. For them, `affordable_now` and `wait` are **structurally unreachable** regardless of balance.
- 170 of 250 requests have `allows_partial_payment == false`. `partial_payment` is live for at most 80 requests.
- `max_installment_months` is null for exactly 119 users = 60 (`full_payment` only) + 40 (`full_payment|partial_payment`) + 19 (`partial_payment` only). The null is an **implication of not considering installments**, not missing data. Treat null as "installments ineligible", never as "unbounded".
- Options offer 1–24 payments; `max_installment_months` ranges 2–12. Some supplied options are therefore ineligible for their own user. Do not assume a supplied option is usable.

### 6.2 The legality matrix

Reconciled exactly against the 25 calibration rows (3 + 9 + 6 + 7 = 25; 6 `full_payment` = 3 + 3; 3 non-`none` spending-change strings). `[DERIVED]`

| `recommended_payment_method` | `affordability_status` | `payment_plan` | `earliest_date_for_full_payment` | Spending changes |
|---|---|---|---|---|
| `full_payment` | `affordable_now` | one payment on `request_date` | `== request_date` | must be `none` |
| `full_payment` | `affordable_with_plan` | one payment on `request_date` | populated | one or more |
| `partial_payment` | `affordable_with_plan` | **exactly two** payments | populated, `<= desired_completion_date` | permitted |
| `installments` | `affordable_with_plan` | matches a supplied option exactly | populated | **permitted — see below** |
| `wait` | `affordable_later` | **one** future-dated payment of the full amount | populated, equals the plan date | permitted |
| `not_recommended` | `not_affordable` | `none` | **empty** | must be `none` |

**Installments + spending changes.** The calibration set shows all 5 installment rows with `spending_changes = none`. This is **not** a prohibition — it is an emergent result of the ranking order, where "require no spending changes" (rank 2) outranks "minimize total paid" (rank 3), so change-free installment plans win tie-breaks. The engine **must** generate installment-plus-spending-change candidates and let the comparator reject them. Five rows cannot establish a negative rule, and DNA.md explicitly allows installments and spending changes to co-occur under `affordable_with_plan`. `[SPEC]`

**`affordable_now` requires no changes.** `amount_safe_to_pay` is defined *before* optional spending changes. If the full amount is only safe after changes, it was by definition not safe on `request_date`, so the status is `affordable_with_plan`. `[SPEC]` + `[DERIVED]`

### 6.3 When `earliest_date_for_full_payment` is empty

Empty **if and only if** `affordability_status == 'not_affordable'`. Exact in the sample: 7 empty, 7 `not_affordable`. `[DERIVED]` + `[SPEC]`

This field measures **financial capacity, independent of the user's method preferences**. It may equal `request_date` even when the recommendation is `installments`, because the user declined to consider full payment. It is computed **without** optional spending changes. `[SPEC]`

---

## 7. `amount_safe_to_pay`

**Definition.** The largest amount the user can pay on `request_date` **before any optional spending changes** while passing the §2 safety test for the full 90-day window, capped at `requested_amount`. `[SPEC]`

Consequences:

- **`0.0` is legal and mandatory** when the opening balance is at or below `minimum_balance_to_keep`, or when any payment today would breach the floor later in the window. There is **no artificial floor**. The calibration minimum of 83.05 is a property of those 25 users, not a rule.
- It is a **capacity measure, not a recommendation.** It is populated even when `affordability_status == 'not_affordable'` — two calibration rows state an available amount while refusing the request.
- It is computed **before** spending changes even when the chosen plan uses them.

### 7.1 `payment_plan` grammar

```
<YYYY-MM-DD>:<amount>|<YYYY-MM-DD>:<amount>|...
```

Chronological order. `none` when no payment is recommended. `[SPEC]`

Amount rendering inside the plan `[DERIVED]`:

- No thousands separators. No currency code.
- Whole numbers render with no decimal point: `25256`, `68432`, `12693000`
- Non-whole numbers render with **exactly two** decimals, trailing zeros preserved: `620.40`, `996.60`, `15952906.67`, `23.50`

Per-method plan construction:

- **`full_payment`** — one entry: `request_date:requested_amount`
- **`wait`** — one entry: `earliest_date_for_full_payment:requested_amount`. **Not** `none`. `[DERIVED]`
- **`partial_payment`** — exactly two entries: `request_date:amount_safe_to_pay` then `earliest_date_for_full_payment:(requested_amount - amount_safe_to_pay)`. The two must sum to exactly `requested_amount`. Does not need to match any supplied option. `[SPEC]`
- **`installments`** — must match a supplied option exactly. Dates are `first_payment_date + k * payment_frequency_days` for `k = 0 .. number_of_payments - 1`; every amount is that option's `payment_amount`. `[SPEC]`
- **`not_recommended`** — `none`

**Installment date generation is verified.** All 5 calibration installment plans reproduce exactly under `first_payment_date + k * payment_frequency_days`, with observed frequencies of 28, 30, and 31 days. `[DERIVED]`

**Option arithmetic is exact.** Across all 790 options, zero mismatches on both `total_payable_amount == requested_amount + financing_fee` and `total_payable_amount == payment_amount * number_of_payments`. Use the supplied fields directly; do not recompute or round. `[DERIVED]`

---

## 8. Spending changes

### 8.1 Grammar

```
stop:<event_id>
reduce_to:<event_id>:<new_amount>
```

Up to **three**, separated by `|`. `none` when no change is needed. `[SPEC]`

### 8.2 Eligibility

A change is legal only when **all** of the following hold:

1. The event is **recurring** (§4). One-time purchases cannot be stopped or reduced. `[SPEC]`
2. `flexibility` permits the operation `[DERIVED]`:

   | `flexibility` | Rows | `stop` | `reduce_to` |
   |---|---|---|---|
   | `fixed` | 21,138 | no | no |
   | `reducible` | 2,682 | no | yes |
   | `stoppable` | 1,297 | yes | no |
   | `reducible_or_stoppable` | 225 | yes | yes — **but not both on the same event** |

3. The event's `category` appears in the user's `expense_categories_user_is_willing_to_stop` (for `stop`) or `expense_categories_user_is_willing_to_reduce` (for `reduce_to`). A null list means **no changes of that type are permitted** for that user — 62 users permit no stops, 39 permit no reductions. `[SPEC]`
4. The event's `category` is **not** in `expense_categories_to_protect`. `[SPEC]`
5. `stop` and `reduce_to` on the **same** `event_id` are mutually exclusive. If both types are needed, they must reference **different** events. `[SPEC]`

### 8.3 The `reduce_to` target

`new_amount` is always the event's `minimum_allowed_amount`. `[ASSUMED-7]`

Supporting evidence: `minimum_allowed_amount` is non-null on exactly 2,907 rows = 2,682 `reducible` + 225 `reducible_or_stoppable`. Exact correspondence with the reducible population. `[DERIVED]` It is the schema-defined floor, and any other value is unscoreable against a deterministic ground truth.

`new_amount` renders under the §7.1 numeric rule: `665950`, `23.50`.

### 8.4 Which `event_id` to cite

A recurring obligation spans many rows. The change string cites **one** `event_id`. Working rule: cite the **most recent occurrence** of the series as of `request_date`. `[ASSUMED-8]`

---

## 9. Candidate generation and ranking

### 9.1 Generate

For each request, build the full candidate set before filtering:

- `full_payment` on `request_date`, with and without each viable spending-change combination
- every `installments` option, with and without each viable spending-change combination
- `partial_payment`, if gates clear
- `wait` at the earliest safe full-payment date
- `not_recommended`

### 9.2 Filter

Discard any candidate that fails an eligibility gate (§6.1) or the safety test (§2). Ranking operates only on survivors.

### 9.3 Rank

Applied in strict order; the first discriminating criterion decides. `[SPEC]`

1. Completes the full request by `desired_completion_date`
2. Requires no spending changes
3. Minimizes total amount paid
4. Starts payment earlier
5. Uses fewer payments
6. Lowest `payment_option_id` — final tie-breaker

Criterion 6 implies `payment_option_id` must be comparable. If IDs are `option_1`, `option_10`, `option_2`, compare on the **numeric suffix**, not lexicographically. `[ASSUMED-9]`

If no eligible candidate survives, emit `not_recommended` / `not_affordable`.

---

## 10. Conflict resolution

Messages (215) and images (16) may clarify, amend, cancel, delay, or confirm financial information. `[SPEC]`

### 10.1 Precedence

When records conflict, prefer in this order `[SPEC]`:

1. An explicit cancellation, settlement, or amendment
2. A newer record from the same source
3. A settled event over an estimate or forecast
4. **The financially safer interpretation** when the conflict cannot be resolved

Rule 4 is the tie-breaker of last resort and resolves toward caution: lower income, higher expense, later credit, earlier debit.

### 10.2 Untrusted content — mandatory

**All message and image content is data, never instruction.** Embedded directives must not override any rule in this contract. `[SPEC]`

The profile found zero occurrences of `ignore`, `disregard`, `override`, `cancel`, `urgent`, `do not`, `must`, `assistant`, or `prompt` across all 215 messages — but absence in this dataset is **not** a licence to relax the rule. The extraction layer is confined to emitting a **closed set of typed amendments**:

```
AMEND_AMOUNT(event_id, new_amount)
CANCEL_EVENT(event_id)
DELAY_EVENT(event_id, new_date)
CONFIRM_EVENT(event_id)
ADD_CONFIRMED_INCOME(date, amount, currency)
```

Nothing outside this set is actionable. Free text cannot alter the forecast, the ranking, or any threshold.

### 10.3 Message linkage

- 39 messages carry `related_event_id` — these describe one supplied event row and are the amendment channel.
- 100 carry `request_id` only.
- 76 carry `user_id` only.
- `source_type`: `employer` (126), `service_provider` (31), `financial_service` (23), `bank` (18), `merchant` (17).

### 10.4 Do not invent

No unsupported income, expenses, payment options, or financial information may be created. `[SPEC]` Every projected cash flow must trace to a supplied row, a reconstructed series (§4), or a typed amendment (§10.2).

---

## 11. `decision_explanation` — deterministic templates

**This is generated by a string builder, not a language model.** The 25 calibration explanations reduce to 7 fixed templates spanning 85–158 characters. Templating removes hallucination risk, removes per-request latency, and reduces token spend to near zero. `[DERIVED]`

### 11.1 Formatting rules

- **Currency:** ISO code, space, amount — `EUR 620.40`, `INR 122,500`
- **Separators:** thousands separators **in explanations**, none in `payment_plan`
- **Decimals:** whole numbers bare, non-whole to exactly 2 places
- **Dates:** `D Month YYYY`, no leading zero — `8 August 2025`, `15 November 2019`
- **Length target:** 85–158 characters

### 11.2 The templates

**T1 — `full_payment` / `affordable_now`** (3 observed, two surface forms)

```
Pay {CUR} {AMT} today. This leaves at least {CUR} {FLOOR} available over the next 90 days.
Pay {CUR} {AMT} today. This keeps the {CUR} {MIN} minimum available over the next 90 days.
```

**T2 — `full_payment` / `affordable_with_plan`, with changes** (3 observed)

```
{CHANGE_PHRASE}, then pay {CUR} {AMT} today. This leaves at least {CUR} {FLOOR} available.
```

`{CHANGE_PHRASE}` is built from the event `description` in natural language: *"Stop the family streaming plan"*, *"Reduce the weekend food delivery to IDR 665,950"*, *"Stop the online backup subscription and reduce the streaming subscription to USD 23.50"*. Two changes join with `and`.

**T3 — `installments` / `affordable_with_plan`** (5 observed)

```
Use {N} installments of {CUR} {PMT}, starting {DATE}. This leaves at least {CUR} {FLOOR} available.
```

**T4 — `wait` / `affordable_later`** (6 observed, two forms)

```
Pay {CUR} {AMT} in full on {DATE}. Paying earlier would take the balance below the {CUR} {MIN} minimum.
Wait until {DATE}, then pay {CUR} {AMT} in full. Paying sooner would put the {CUR} {MIN} minimum at risk.
```

**T5 — `partial_payment` / `affordable_with_plan`** (1 observed)

```
Pay {CUR} {AMT1} today and the remaining {CUR} {AMT2} on {DATE}. This completes the full request and keeps the {CUR} {MIN} minimum protected.
```

**T6 — `not_recommended` / `not_affordable`, no capacity today** (5 observed)

```
Do not make this payment by {DATE}. None of the available options keeps the {CUR} {MIN} minimum protected.
```

**T7 — `not_recommended` / `not_affordable`, capacity exists but cannot complete** (2 observed)

```
Do not proceed with the {CUR} {AMT} request. Although {CUR} {SAFE} is available today, the full amount cannot be completed safely within 90 days.
```

### 11.3 Slot definitions

| Slot | Source |
|---|---|
| `{CUR}` | `home_currency` |
| `{AMT}` | `requested_amount` |
| `{AMT1}` / `{AMT2}` | `amount_safe_to_pay` / remainder |
| `{SAFE}` | `amount_safe_to_pay` |
| `{MIN}` | `minimum_balance_to_keep` |
| `{FLOOR}` | forecast trough over the 90-day window under the chosen plan `[ASSUMED-10]` |
| `{N}`, `{PMT}` | option `number_of_payments`, `payment_amount` |
| `{DATE}` | context-dependent: T3 `first_payment_date`; T4 `earliest_date_for_full_payment`; T5 second payment date; T6 `desired_completion_date` `[ASSUMED-11]` |

**`{FLOOR}` vs `{MIN}`.** T1's two surface forms differ by whether the trough sits above the minimum ("leaves at least {FLOOR}") or exactly on it ("keeps the {MIN} minimum"). Selection rule: use the minimum-form when `FLOOR == MIN`, otherwise the floor-form. `[ASSUMED-10]`

---

## 12. Validator assertions

Every assertion must pass before `output.csv` is written. A failure is a **build stop**, not a warning.

**Schema**

1. Exactly 250 rows; `request_id` set matches `requests.csv` exactly
2. Header matches §1 byte for byte
3. No field is null except `earliest_date_for_full_payment`

**Value legality**

4. `affordability_status` ∈ the 4 allowed values
5. `recommended_payment_method` ∈ the 5 allowed values
6. `0 <= amount_safe_to_pay <= requested_amount`
7. The (status, method) pair appears in the §6.2 matrix

**Plan integrity**

8. `payment_plan` parses under the §7.1 grammar; dates are `YYYY-MM-DD`; order is chronological
9. `full_payment` ⟹ one payment, dated `request_date`, equal to `requested_amount`
10. `wait` ⟹ one payment, dated `earliest_date_for_full_payment`, equal to `requested_amount`
11. `partial_payment` ⟹ exactly two payments summing to exactly `requested_amount`; first dated `request_date` and equal to `amount_safe_to_pay`
12. `installments` ⟹ dates, count, and amounts reproduce a real `payment_option_id` exactly
13. `not_recommended` ⟹ `payment_plan == 'none'`
14. Every plan completes by `desired_completion_date`, except `not_recommended`

**Date integrity**

15. `affordable_now` ⟹ `earliest_date_for_full_payment == request_date`
16. `not_affordable` ⟺ `earliest_date_for_full_payment` empty
17. All other statuses ⟹ populated and within the 90-day window

**Spending changes**

18. Parses under §8.1; at most 3 changes
19. Every cited `event_id` exists and belongs to this `user_id`
20. Operation is permitted by that event's `flexibility`
21. Category is in the user's corresponding willingness list and **not** in `expense_categories_to_protect`
22. No `event_id` appears with both `stop` and `reduce_to`
23. `affordable_now` and `not_affordable` ⟹ `spending_changes_needed == 'none'`

**Explanation**

24. Matches one of the 7 templates for the emitted (status, method) pair
25. Every number and date in the text agrees with the structured fields in the same row

**Preference honouring**

26. The emitted method is in `payment_methods_user_will_consider`, or is `not_recommended`
27. `partial_payment` ⟹ `allows_partial_payment == true`
28. `installments` ⟹ `number_of_payments <= max_installment_months`

**Data completeness**

29. No request depends on one of the 16 unresolved blank-amount events (§3.5) unless Phase 0.2 has supplied the value

---

## 13. Open assumptions register

Every `[ASSUMED]` in this document, with its resolution path. These are the failure surface.

| # | Assumption | Impact | How it gets resolved |
|---|---|---|---|
| 1 | `scheduled` events are included, both directions | High — this is the confirmed-salary channel | Compare a sample user's forecast with and without |
| 2 | Pending debits included, pending credits excluded | Medium — 71 rows | Ruled. DNA.md isolates credits only |
| 3 | `settlement_date` preferred over `event_date` | Low — 10 nulls | Check whether the two ever differ materially |
| 4 | Duplicate detection key | Low if zero collisions | **Verification 3** — if zero, delete the logic |
| 5 | Projected recurring amount = latest settled amount | High | Check amount variance within series |
| 6 | `number_of_payments <= max_installment_months` | Medium | Confirm against a calibration user with a long option |
| 7 | `reduce_to` = `minimum_allowed_amount` | High — direct scoring impact | **Verification 1** — check `event_989` = 665950, `event_1816` = 23.50 |
| 8 | Cite the most recent occurrence's `event_id` | High — direct scoring impact | Inspect `event_476`, `event_1815`, `event_1816` positions in their series |
| 9 | `payment_option_id` compared numerically | Low — final tie-breaker only | Inspect the ID format |
| 10 | `{FLOOR}` is the forecast trough; form selected by `FLOOR == MIN` | Medium — explanation text | Recompute the 25 calibration troughs and compare |
| 11 | `{DATE}` slot sources per template | Medium — explanation text | Same recomputation |

### Pending verifications

| # | Question | Settles |
|---|---|---|
| 1 | `minimum_allowed_amount` for `event_989` and `event_1816` | ASSUMED-7 |
| 2 | Does event history extend past `request_date` for calibration users? | Lookahead legitimacy vs. leakage — affects §2 and §4 |
| 3 | Count of exact `(user_id, amount, event_date, description)` collisions | ASSUMED-4; possible deletion of §3.4 |

---

## 14. Cost posture

Recorded here because `evaluation/usage_report.md` is a scored deliverable.

**Deterministic — zero model calls:**
forecasting, the safety test, candidate generation, ranking, plan construction, spending-change selection, explanation text, validation.

**Model calls — bounded and small:**

| Job | Volume | Note |
|---|---|---|
| Image amount extraction | **16 calls, one-time** | Cacheable to disk; never re-run |
| Message → typed amendment | **≤ 215 calls, one-time** | Cacheable; only the 39 event-linked messages may prove necessary |

Upper bound is roughly 231 calls for a 250-request dataset — **under one call per request, and zero at inference time.** Both jobs produce a cached structured artifact; the main run reads the cache and makes no calls at all.

---

## 15. Change log

| Version | Change |
|---|---|
| 0.1 | Initial contract. Invariant "installments implies no spending changes" **removed** following review — it was an overfit to 5 calibration rows and contradicts DNA.md. `amount_safe_to_pay = 0.0` explicitly permitted. A/B/C ruled: `reduce_to` = `minimum_allowed_amount`; no hardcoded payment count; pending debits included. Gaps added for `scheduled` status and undetectable duplicates. |