# Milestones

Progress record for the Buy or Wait build. One row per sub-phase.

**"Done" means the gate passed and a human confirmed it.** Code existing is not
done. Agent 3 demonstrates; the human signs off.

Status values: `not started` · `in progress` · `blocked` · `gate failed` · `passed`

---

## Phase 0 — Design (complete)

| Sub-phase | Deliverable | Gate | Status | Signed off |
|---|---|---|---|---|
| 0.1 | `docs/data-profile.md` | All 9 CSVs profiled; enums and joins verified | passed | Deman |
| 0.2 | `docs/image-extraction.md` | 16 amounts extracted and human-verified | passed | Deman |
| 0.3 | `docs/decision-contract.md` | Rules, 33 assertions, assumption register | passed | Deman |
| 0.4 | `docs/architecture.md` | Modules, pipeline, build order | passed | Deman |

---

## Phase 1.0 — Scaffold

| Sub-phase | Deliverable | Gate | Command | Status | Signed off |
|---|---|---|---|---|---|
| 1.0a | `pyproject.toml` complete | Deps declared; `uv sync` clean | `uv sync` | passed | |
| 1.0b | `src/observability/` | ERROR→file, INFO/WARN→console, DEBUG opt-in; every record carries stage + request_id | `uv run python -m observability.selftest` | passed | |
| 1.0c | mypy strict gate | Clean on all existing source | `uv run mypy --strict src/` | passed | |


---

## Phase 1.1 — Verifications

Seven read-only queries. Each closes an entry in `decision-contract.md` §13.
Each has a default if unresolved — none can block the build.

| # | Question | Closes | Result | Status | Signed off |
|---|---|---|---|---|---|
| V1 | `minimum_allowed_amount` for `event_989`, `event_1816` | ASSUMED-7 | `event_989=665950.0`, `event_1816=23.5` | passed | |
| V2 | Does event history extend past `request_date`? | Lookahead legitimacy | 0 settled past request_date; 42 scheduled credits past request_date | passed | |
| V3 | Exact duplicate collision count | ASSUMED-4 | 0 collisions on (user_id, amount, event_date, description) | passed | |
| V4 | Breakdown of all 70 `scheduled` rows | ASSUMED-1 — **priority** | 47 credits (all salary), 23 debits (11 util, 5 edu, 5 ins, 1 rent, 1 health); 2 null amounts (events 1442, 6859) | passed | |
| V5 | Series keys with bimodal `event_date` gaps | §4.1 key sufficiency | 231 of 4,510 series >= 3 events (5.1%) have bimodal gaps | passed | |
| V6 | Series position of the 4 cited spending-change events | ASSUMED-8 | All 4 cited events are latest (reverse index 1 of N, latest metadata-bearing) | passed | |
| V7 | `request_text` audit — amounts, dates, method language | §4.13 | 100% amounts match requested_amount (inc. IDR dot format); 0 text conflicts | passed | |
| V8 | Composition of bimodal series keys | §4.1 bimodal nature | 231 series: 219 debit (109 transport, 80 groceries, 30 dining), 12 credit (salary); 9 reducible, 222 fixed | passed | |
| V9 | Distribution & composition of sub-threshold series (< 3 events) | Recurrence handling | 3,492 series: 1,893 count=1, 1,599 count=2; event_989 is count=2; 289 count=2 are reducible | passed | |
| V10 | Bimodal salary series composition & message linkage | Recurrence / gig income | 12 series (11 users), 0 scheduled rows, 9 service_provider messages | passed | |


**V4 is the priority.** It is the only open item that can produce a dangerous
wrong answer rather than an inaccurate one.

---

## Phase 1–7 — Build

From `architecture.md` §7. Each phase gates the next.

| Phase | Builds | Gate | Status | Signed off |
|---|---|---|---|---|
| 1 | `models.py`, `dataio/loaders.py`, `state/fx.py` | All 9 CSVs load; 16 amounts merge; all 140 FX events resolve | passed | |
| 2 | `llm/extract_messages.py` → frozen JSON; `state/amendments.py` | Amendments apply cleanly; nothing outside the typed set | passed | |
| 3 | `state/recurrence.py` | Diagnostic report hand-reviewed for 5 users; V5 clean | not started | |
| 4 | `forecast/engine.py`, `verify/safety.py` | `amount_safe_to_pay` matches on requests 03, 16, 17 | not started | |
| 5 | `planner/*` | Full 25-row calibration run; accuracy measured per field | not started | |
| 6 | `explain/*`, `io/writer.py` | All 25 explanations reproduce exactly | not started | |
| 7 | `verify/validator.py`, `evaluation/usage_report.md` | All 33 assertions pass on all 250 rows | not started | |

**Phase 3 is the one to slow down on.** Recurrence is inferred rather than
supplied, and every downstream number depends on it.

---

## Decision log

Choices made during the build that are not in the design documents. Append only.

| Date | Decision | Rationale | Made by |
|---|---|---|---|
| | | | |

---

## Blocked items

| Item | Blocked on | Raised | Resolved |
|---|---|---|---|
| | | | |