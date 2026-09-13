# Verification Results

Results of the seven Phase 1.1 verification queries settling open entries in `docs/decision_contract.md` §13.
Read-only analysis across `dataset/*.csv`. Zero editorial interpretation.

---

## 1. V4 — Full Breakdown of All 70 Scheduled Rows

### Question
Full breakdown of all 70 scheduled rows (`ASSUMED-1` — the phantom-liquidity risk).

### Query Used
```python
df = pd.read_csv("dataset/financial_events.csv")
scheduled = df[df["status"] == "scheduled"]
# Count direction, direction x category, null amounts, users, currencies, and itemize all credits and debits
```
Script: `scripts/verify_scheduled.py`

### Raw Result
- **Total scheduled rows**: 70
- **Unique users involved**: 66
- **Null amounts**: 2
  - `event_1442` (user `user_16`, debit, rent, `"Outstanding rent balance"`)
  - `event_6859` (user `user_73`, debit, healthcare, `"Hospital bill payable"`)
- **Date range**: 2023-01-19 to 2026-07-15
- **Direction counts**:
  - `credit`: 47
  - `debit`: 23
- **Direction x Category counts**:
  - `credit` | `salary`: 47
  - `debit` | `utilities`: 11
  - `debit` | `education`: 5
  - `debit` | `insurance`: 5
  - `debit` | `healthcare`: 1
  - `debit` | `rent`: 1
- **Currency counts**:
  - `USD`: 21
  - `INR`: 15
  - `EUR`: 13
  - `ZAR`: 13
  - `IDR`: 8
- **Scheduled credits detail (all 47 have category `salary` and description `'Next confirmed salary'`)**:
  - `event_103`: `user_01`, `2024-03-15`, `23320.0 ZAR`, `Next confirmed salary`
  - `event_1161`: `user_13`, `2024-03-15`, `1343.54 EUR`, `Next confirmed salary`
  - `event_1546`: `user_17`, `2026-03-15`, `206000.0 INR`, `Next confirmed salary`
  - `event_1858`: `user_21`, `2026-04-15`, `2256.0 USD`, `Next confirmed salary`
  - `event_2288`: `user_25`, `2024-03-15`, `1800.0 USD`, `Next confirmed salary`
  - `event_2831`: `user_31`, `2024-09-15`, `19972800.0 IDR`, `Next confirmed salary`
  - `event_3611`: `user_39`, `2026-04-15`, `3048.0 USD`, `Next confirmed salary`
  - `event_3833`: `user_41`, `2025-11-15`, `2688.0 USD`, `Next confirmed salary`
  - `event_4292`: `user_46`, `2024-12-15`, `145000.0 INR`, `Next confirmed salary`
  - `event_5253`: `user_56`, `2025-02-15`, `2388.0 USD`, `Next confirmed salary`
  - `event_5911`: `user_63`, `2026-07-15`, `2280.0 USD`, `Next confirmed salary`
  - `event_6291`: `user_67`, `2024-09-15`, `2047.68 USD`, `Next confirmed salary`
  - `event_7427`: `user_79`, `2024-09-15`, `1428.0 USD`, `Next confirmed salary`
  - `event_8125`: `user_86`, `2025-08-23`, `124000.0 INR`, `Next confirmed salary`
  - `event_8404`: `user_89`, `2025-11-15`, `15200000.0 IDR`, `Next confirmed salary`
  - `event_8981`: `user_96`, `2026-01-15`, `80000.0 INR`, `Next confirmed salary`
  - `event_9039`: `user_97`, `2024-03-15`, `35420.0 ZAR`, `Next confirmed salary`
  - `event_9233`: `user_99`, `2026-07-15`, `56980.0 ZAR`, `Next confirmed salary`
  - `event_9338`: `user_100`, `2024-06-15`, `42680.0 ZAR`, `Next confirmed salary`
  - `event_10164`: `user_109`, `2024-03-15`, `2604.0 USD`, `Next confirmed salary`
  - `event_10803`: `user_116`, `2025-02-15`, `124000.0 INR`, `Next confirmed salary`
  - `event_11234`: `user_121`, `2024-03-15`, `1056.0 USD`, `Next confirmed salary`
  - `event_11482`: `user_124`, `2024-06-15`, `2629.0 EUR`, `Next confirmed salary`
  - `event_12383`: `user_134`, `2025-08-15`, `24510000.0 IDR`, `Next confirmed salary`
  - `event_12539`: `user_136`, `2024-06-15`, `1548.0 USD`, `Next confirmed salary`
  - `event_12810`: `user_139`, `2024-09-15`, `1824.0 USD`, `Next confirmed salary`
  - `event_13494`: `user_146`, `2025-08-15`, `168000.0 INR`, `Next confirmed salary`
  - `event_13748`: `user_149`, `2025-11-15`, `52360.0 ZAR`, `Next confirmed salary`
  - `event_16693`: `user_181`, `2024-03-15`, `2580.0 USD`, `Next confirmed salary`
  - `event_17580`: `user_190`, `2024-12-15`, `2849.0 EUR`, `Next confirmed salary`
  - `event_17735`: `user_192`, `2026-04-15`, `813.6 USD`, `Next confirmed salary`
  - `event_18095`: `user_196`, `2024-06-15`, `814.0 EUR`, `Next confirmed salary`
  - `event_18931`: `user_205`, `2024-03-15`, `18240000.0 IDR`, `Next confirmed salary`
  - `event_19078`: `user_207`, `2026-07-15`, `21120.0 ZAR`, `Next confirmed salary`
  - `event_19265`: `user_209`, `2025-11-15`, `21120.0 ZAR`, `Next confirmed salary`
  - `event_19433`: `user_211`, `2024-09-15`, `1884.96 EUR`, `Next confirmed salary`
  - `event_20046`: `user_217`, `2024-03-15`, `35420.0 ZAR`, `Next confirmed salary`
  - `event_20130`: `user_218`, `2025-08-15`, `48640000.0 IDR`, `Next confirmed salary`
  - `event_20512`: `user_223`, `2024-09-15`, `1309.0 EUR`, `Next confirmed salary`
  - `event_21310`: `user_231`, `2026-01-15`, `44000.0 ZAR`, `Next confirmed salary`
  - `event_22031`: `user_239`, `2025-05-15`, `1020.0 USD`, `Next confirmed salary`
  - `event_22363`: `user_243`, `2026-07-15`, `23980.0 ZAR`, `Next confirmed salary`
  - `event_22463`: `user_244`, `2024-06-15`, `56760.0 ZAR`, `Next confirmed salary`
  - `event_23674`: `user_257`, `2025-11-15`, `1793.0 EUR`, `Next confirmed salary`
  - `event_23798`: `user_258`, `2026-01-15`, `572.88 USD`, `Next confirmed salary`
  - `event_23980`: `user_260`, `2025-02-15`, `1848.0 USD`, `Next confirmed salary`
  - `event_24891`: `user_270`, `2026-07-15`, `1071.36 USD`, `Next confirmed salary`
- **Scheduled debits detail (23 rows)**:
  - `event_357`: `user_04`, `2024-06-04`, `1704300.0 IDR`, `education`, `Scheduled school fee`
  - `event_1442`: `user_16`, `2023-08-11`, `null INR`, `rent`, `Outstanding rent balance`
  - `event_2166`: `user_24`, `2026-01-04`, `1830.0 INR`, `insurance`, `Scheduled insurance payment`
  - `event_4114`: `user_44`, `2025-02-04`, `4830.0 INR`, `utilities`, `Scheduled utility debit`
  - `event_5169`: `user_55`, `2026-06-08`, `13800.0 INR`, `utilities`, `Scheduled bill payment retry`
  - `event_6034`: `user_64`, `2024-06-04`, `2240.0 INR`, `education`, `Scheduled school fee`
  - `event_6859`: `user_73`, `2023-01-19`, `null INR`, `healthcare`, `Hospital bill payable`
  - `event_7942`: `user_84`, `2026-04-04`, `6080.0 INR`, `insurance`, `Scheduled insurance payment`
  - `event_8576`: `user_91`, `2024-09-03`, `166.0 EUR`, `utilities`, `Scheduled bill payment retry`
  - `event_9681`: `user_104`, `2025-02-04`, `1964.6 ZAR`, `utilities`, `Scheduled utility debit`
  - `event_11481`: `user_124`, `2024-06-04`, `60.0 EUR`, `education`, `Scheduled school fee`
  - `event_12809`: `user_139`, `2024-09-04`, `82.0 USD`, `utilities`, `Scheduled bill payment retry`
  - `event_13307`: `user_144`, `2026-07-04`, `51.0 USD`, `insurance`, `Scheduled insurance payment`
  - `event_15106`: `user_164`, `2025-02-04`, `1335700.0 IDR`, `utilities`, `Scheduled utility debit`
  - `event_16691`: `user_181`, `2024-03-03`, `129.0 USD`, `utilities`, `Scheduled bill payment retry`
  - `event_17019`: `user_184`, `2024-06-04`, `4820.0 INR`, `education`, `Scheduled school fee`
  - `event_18828`: `user_204`, `2026-01-04`, `77.0 EUR`, `insurance`, `Scheduled insurance payment`
  - `event_20616`: `user_224`, `2025-02-04`, `1806900.0 IDR`, `utilities`, `Scheduled utility debit`
  - `event_21102`: `user_229`, `2024-03-04`, `73.0 EUR`, `utilities`, `Scheduled bill payment retry`
  - `event_22462`: `user_244`, `2024-06-04`, `3517.8 ZAR`, `education`, `Scheduled school fee`
  - `event_23307`: `user_253`, `2024-03-07`, `192.0 EUR`, `utilities`, `Scheduled bill payment retry`
  - `event_23856`: `user_259`, `2024-09-04`, `42.0 EUR`, `utilities`, `Scheduled bill payment retry`
  - `event_24353`: `user_264`, `2026-04-04`, `5080.0 INR`, `insurance`, `Scheduled insurance payment`

---

## 2. V1 — `minimum_allowed_amount` for `event_989` and `event_1816`

### Question
`minimum_allowed_amount` for `event_989`, `event_1816` (`ASSUMED-7`).

### Query Used
```python
df = pd.read_csv("dataset/financial_events.csv")
targets = df[df["event_id"].isin(["event_989", "event_1816"])]
```
Script: `scripts/verify_reduce_target.py`

### Raw Result
- **`event_989`**:
  - `user_id`: `user_11`
  - `event_date`: `2025-04-23`
  - `amount`: `1163530.49`
  - `currency`: `IDR`
  - `direction`: `debit`
  - `category`: `dining`
  - `description`: `'Weekend food delivery'`
  - `flexibility`: `reducible`
  - `minimum_allowed_amount`: `665950.0`
- **`event_1816`**:
  - `user_id`: `user_21`
  - `event_date`: `2026-03-09`
  - `amount`: `47.0`
  - `currency`: `USD`
  - `direction`: `debit`
  - `category`: `streaming`
  - `description`: `'Streaming subscription'`
  - `flexibility`: `reducible_or_stoppable`
  - `minimum_allowed_amount`: `23.5`
- **Dataset-wide counts**:
  - Total rows with non-null `minimum_allowed_amount`: 2,907
  - Flexibility breakdown for non-null `minimum_allowed_amount`:
    - `reducible`: 2,682
    - `reducible_or_stoppable`: 225

---

## 3. V6 — Series Position of the 4 Cited Spending-Change Events

### Question
Series position of `event_476`, `event_989`, `event_1815`, `event_1816` (`ASSUMED-8`).

### Query Used
```python
# Group by (user_id, direction, category, description, currency), sort by event_date, settlement_date, event_id
# Find 1-based chronological index and reverse index (1 = latest)
```
Script: `scripts/verify_event_citation.py`

### Raw Result
- **`event_476`** (`user_06`, `debit`, `streaming`, `'Family streaming plan'`):
  - `total_series_events`: 5
  - `chronological_index`: 5 of 5
  - `reverse_index`: 1 (latest overall: `True`)
  - `total_metadata_bearing_events`: 5
  - `is_latest_metadata_bearing`: `True`
- **`event_989`** (`user_11`, `debit`, `dining`, `'Weekend food delivery'`):
  - `total_series_events`: 2
  - `chronological_index`: 2 of 2
  - `reverse_index`: 1 (latest overall: `True`)
  - `total_metadata_bearing_events`: 2
  - `is_latest_metadata_bearing`: `True`
- **`event_1815`** (`user_21`, `debit`, `cloud_storage`, `'Online backup subscription'`):
  - `total_series_events`: 5
  - `chronological_index`: 5 of 5
  - `reverse_index`: 1 (latest overall: `True`)
  - `total_metadata_bearing_events`: 5
  - `is_latest_metadata_bearing`: `True`
- **`event_1816`** (`user_21`, `debit`, `streaming`, `'Streaming subscription'`):
  - `total_series_events`: 5
  - `chronological_index`: 5 of 5
  - `reverse_index`: 1 (latest overall: `True`)
  - `total_metadata_bearing_events`: 5
  - `is_latest_metadata_bearing`: `True`

---

## 4. V5 — Count of Series Keys with Bimodal `event_date` Gaps

### Question
Count of series keys with bimodal `event_date` gaps (`§4.1` key sufficiency).

### Query Used
```python
# Group by (user_id, direction, category, description, currency) for series >= 3 events.
# Calculate diffs of sorted event_date in days. Check for >= 2 distinct clusters with >= 2 occurrences each.
```
Script: `scripts/verify_series_keys.py`

### Raw Result
- **Total series defined by key**: 8,002
- **Series with >= 3 events**: 4,510
- **Series with < 3 events**: 3,492
- **Median cadence distribution (series >= 3)**:
  - `monthly (~30d)`: 2,290
  - `other (21.0d)`: 237
  - `biweekly (~14d)`: 228
  - `other (35.0d)`: 215
  - `other (42.0d)`: 166
  - `other (49.0d)`: 106
  - `other (20.0d)`: 96
  - `other (56.0d)`: 89
  - `other (63.0d)`: 84
  - `weekly (~7d)`: 50
  - Other cadences: 949
- **Count of series keys with bimodal event_date gaps**: 231 of 4,510 (5.1%)

---

## 5. V3 — Exact Duplicate Collision Count

### Question
Exact `(user_id, amount, event_date, description)` collision count (`ASSUMED-4`; possible deletion of `§3.4`).

### Query Used
```python
df = pd.read_csv("dataset/financial_events.csv")
# Count duplicates on subset=['user_id', 'amount', 'event_date', 'description']
```
Script: `scripts/verify_duplicates.py`

### Raw Result
- **Total events inspected**: 25,342
- **Collision groups on `(user_id, amount, event_date, description)`**: 0
- **Total colliding rows on 4-field key**: 0
- **Collision groups on `(user_id, amount, event_date, description, direction, currency)`**: 0
- **Total colliding rows on 6-field key**: 0

---

## 6. V2 — Event History Lookahead Past `request_date`

### Question
Does event history extend past `request_date`? (Lookahead legitimacy vs leakage).

### Query Used
```python
# Join requests.csv and sample_requests.csv with financial_events.csv on user_id
# Count events where event_date > request_date and settlement_date > request_date
```
Script: `scripts/verify_lookahead.py`

### Raw Result
- **Evaluation Requests (`requests.csv`, 250 requests)**:
  - Total request-event pairs: 23,054
  - Events with `event_date > request_date`: 42
    - Status breakdown: `scheduled`: 42
    - Direction breakdown: `credit`: 42
    - Settled events with `event_date > request_date`: 0
  - Events with `settlement_date > request_date`: 124
    - Status breakdown: `scheduled`: 62, `pending`: 62
    - Direction breakdown: `debit`: 75, `credit`: 49
    - Settled events with `settlement_date > request_date`: 0
  - Events with `event_date == request_date`: 19
- **Calibration Requests (`sample_requests.csv`, 25 requests)**:
  - Total request-event pairs: 2,288
  - Events with `event_date > request_date`: 5
    - Status breakdown: `scheduled`: 5
    - Direction breakdown: `credit`: 5
    - Settled events with `event_date > request_date`: 0
  - Events with `settlement_date > request_date`: 17
    - Status breakdown: `pending`: 9, `scheduled`: 8
    - Direction breakdown: `debit`: 11, `credit`: 6
    - Settled events with `settlement_date > request_date`: 0
  - Events with `event_date == request_date`: 2

---

## 7. V7 — `request_text` Audit

### Question
`request_text` audit — amounts, dates, method language (`§4.13`).

### Query Used
```python
# Audit numeric amounts, date mentions, and payment method keywords across request_text in requests.csv and sample_requests.csv
```
Script: `scripts/verify_request_text.py`

### Raw Result
- **Evaluation Requests (`requests.csv`, 250 rows)**:
  - Total requests audited: 250
  - Requests containing numeric amounts: 250 (100.0%)
  - Requests with numeric amounts differing from `requested_amount`: 1
    - Note on the 1 differing instance: `request_43` text contains `"IDR 43.339.000"` (Indonesian period thousands separator), which matches `requested_amount = 43339000.0` exactly.
  - Requests mentioning dates/months: 126 (50.4%)
  - Method keyword occurrences in text:
    - `full_payment`: 110 (44.0%)
    - `wait`: 55 (22.0%)
    - `installment`: 13 (5.2%)
    - `partial_payment`: 4 (1.6%)
- **Calibration Requests (`sample_requests.csv`, 25 rows)**:
  - Total requests audited: 25
  - Requests containing numeric amounts: 25 (100.0%)
  - Requests with numeric amounts differing from `requested_amount`: 0
  - Requests mentioning dates/months: 12 (48.0%)
  - Method keyword occurrences in text:
    - `full_payment`: 9 (36.0%)
    - `wait`: 4 (16.0%)
    - `installment`: 1 (4.0%)

---

## 8. V8 — Composition Analysis of Bimodal Series Keys

### Question
What is the composition and nature of the 231 bimodal series identified in V5? Audits category, direction, subscription/salary status, and flexibility across bimodal series.

### Query Used
```python
# From the 231 series keys with bimodal event_date gaps (>= 2 modes with >= 2 occurrences):
# Aggregate total events, direction, category, flexibility, subscription/salary status, and mode cluster pairs.
```
Script: `scripts/verify_bimodal_composition.py`

### Raw Result
- **Total bimodal series**: 231
- **Total events in bimodal series**: 1,541
- **Direction breakdown**:
  - `debit`: 219
  - `credit`: 12
- **Direction x Category breakdown**:
  - `debit` | `transport`: 109
  - `debit` | `groceries`: 80
  - `debit` | `dining`: 30
  - `credit` | `salary`: 12
- **Mode cluster pairs across bimodal series**:
  - `irregular + weekly`: 79
  - `monthly + weekly`: 38
  - `biweekly + irregular`: 27
  - `irregular + monthly`: 26
  - `biweekly + weekly`: 18
  - `biweekly + monthly`: 16
  - `irregular + monthly + weekly`: 10
  - `biweekly + irregular + weekly`: 8
  - `biweekly + monthly + weekly`: 4
  - `bimonthly + weekly`: 2
  - `bimonthly + biweekly`: 2
  - `biweekly + irregular + monthly`: 1
- **Flexibility representation**:
  - `fixed`: 222
  - `reducible`: 9
- **Series with `event_type == 'subscription'` or `category == 'salary'`**: 12 of 231 (5.2%, all 12 are `credit` | `salary`)
- **Series with any controllable event (`flexibility != 'fixed'`)**: 9 of 231 (3.9%, all 9 are `reducible` `debit` | `dining`)

---

## 9. V9 — Distribution and Composition of Sub-Threshold Series Keys (< 3 events)

### Question
What is the distribution and composition of the 3,492 sub-threshold series (< 3 events)? Audits count == 1 vs count == 2, gap distributions, flexibility, subscription/salary status, and cross-references cited spending-change events.

### Query Used
```python
# Group by (user_id, direction, category, description, currency).
# Partition into count == 1 vs count == 2.
# Measure gap distributions, flexibility, category, and cross-reference cited events from sample_requests.csv.
```
Script: `scripts/verify_subthreshold_series.py`

### Raw Result
- **Total series keys**: 8,002
- **Series with >= 3 events**: 4,510
- **Total sub-threshold series (< 3 events)**: 3,492
  - `Count == 1`: 1,893
  - `Count == 2`: 1,599
- **Count == 2 gap distribution (days between the 2 events)**:
  - `Min`: 5
  - `Median`: 56.0
  - `Mean`: 62.2
  - `Max`: 170
  - `other gap`: 952
  - `25-35d (~monthly)`: 224
  - `55-65d (~bimonthly)`: 194
  - `11-18d (~biweekly)`: 117
  - `5-10d (~weekly)`: 70
  - `85-95d (~quarterly)`: 42
- **Count == 2 composition**:
  - Series with `event_type == 'subscription'` or `category == 'salary'`: 92 of 1,599
  - Series with controllable events (`flexibility != 'fixed'`): 289 of 1,599
  - Flexibility breakdown: `fixed`: 1,310, `reducible`: 289
  - Top categories: `groceries`: 546, `transport`: 482, `dining`: 479, `salary`: 92
- **Count == 1 composition**:
  - Series with `event_type == 'subscription'` or `category == 'salary'`: 180 of 1,893
  - Series with controllable events (`flexibility != 'fixed'`): 389 of 1,893
  - Top categories: `dining`: 598, `transport`: 456, `groceries`: 433, `salary`: 180, `shopping`: 100
- **Cross-reference with cited spending-change events**:
  - Total cited spending-change events checked: 4
  - Cited events in series >= 3: 3 (`event_476`, `event_1815`, `event_1816`)
  - Cited events in sub-threshold series (< 3): 1 (`event_989`: series size = 2, key = `('user_11', 'debit', 'dining', 'Weekend food delivery', 'IDR')`)

---

## 10. V10 — Bimodal Salary Series and Message Linkage Analysis

### Question
What is the exact composition, gap structure, message linkage, and forward schedule status of the 12 bimodal credit/salary series identified in V5/V8?

### Query Used
```python
# From all credit | salary series with >= 3 events:
# Identify series with >= 2 modal gap clusters with count >= 2.
# Audit user IDs, descriptions, currencies, gap cluster pairs, forward scheduled salary rows, and linked messages.
```
Script: `scripts/verify_bimodal_salary.py`

### Raw Result
- **Total bimodal salary series**: 12
- **Unique users involved**: 11 (`user_10`, `user_123`, `user_159`, `user_199`, `user_203`, `user_215`, `user_251`, `user_27`, `user_47`, `user_51`, `user_59`)
  - `user_123` has 2 distinct bimodal salary series (`Delivery platform payout` and `Driver platform payout`)
- **Description breakdown**:
  - `Delivery platform payout`: 5
  - `Driver platform payout`: 4
  - `Weekly app earnings`: 2
  - `Task marketplace payout`: 1
- **Currency breakdown**:
  - `IDR`: 5
  - `ZAR`: 3
  - `INR`: 2
  - `EUR`: 2
- **Mode pair combinations**:
  - `biweekly + irregular + weekly`: 4
  - `biweekly + weekly`: 3
  - `irregular + weekly`: 2
  - `biweekly + irregular`: 1
  - `irregular + monthly`: 1
  - `monthly + weekly`: 1
- **Forward scheduled salary rows for these users**: 0
- **Total messages linked to these users in `messages.csv`**: 9
- **Message source_type distribution**:
  - `service_provider`: 9
  - Note: All 9 messages explicitly confirm gig platform payouts are pending and unwithdrawable until payout is closed.

---

## 11. V11 — Comprehensive Audit of the 79 Frozen Message Amendments

### Question
Audit the 79 frozen message amendments before forecast code is built: breakdown, income linkage, double-count exposure, verbatim provenance, token usage, and bimodal salary properties.

### A. Breakdown by AmendmentAction Type
- **Total Amendments**: 79
- `ADD_CONFIRMED_INCOME`: 65
- `CONFIRM_EVENT`: 14
- **Confirmation of Split**: Exactly 65 `ADD_CONFIRMED_INCOME` and 14 `CONFIRM_EVENT` (65/14 split confirmed).

### B. The 65 `ADD_CONFIRMED_INCOME` Records
- **Total Added Income Records**: 65
- **Unique Users Affected**: 65
- **Affected Users with an Existing Scheduled Salary Row (from V4's 47)**: 0 (0.0%)
- **Records Falling Inside Request 90-Day Forecast Window**: 65 of 65 (100.0%)
  - In Evaluation Requests window (`requests.csv`): 62
  - In Calibration Requests window (`sample_requests.csv`): 3
- **Records Falling Outside Request 90-Day Window**: 0

| # | `user_id` | `date` | `amount` | `currency` | `message_id` | `source_type` | `request_date` | In 90d Window? | Days from Req |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `user_02` | `2025-08-15` | 42750000 | `IDR` | `message_01` | `employer` | `2025-08-05` | True | +10d |
| 2 | `user_14` | `2025-08-15` | 2717 | `EUR` | `message_10` | `employer` | `2025-08-04` | True | +11d |
| 3 | `user_15` | `2026-01-15` | 1661 | `EUR` | `message_11` | `employer` | `2026-01-06` | True | +9d |
| 4 | `user_26` | `2025-08-15` | 30780000 | `IDR` | `message_18` | `service_provider` | `2025-08-03` | True | +12d |
| 5 | `user_32` | `2025-02-15` | 54120 | `ZAR` | `message_22` | `employer` | `2025-02-05` | True | +10d |
| 6 | `user_34` | `2024-12-15` | 196000 | `INR` | `message_24` | `service_provider` | `2024-12-04` | True | +11d |
| 7 | `user_36` | `2026-07-15` | 2988 | `USD` | `message_26` | `employer` | `2026-07-03` | True | +12d |
| 8 | `user_40` | `2024-06-15` | 1760 | `EUR` | `message_29` | `employer` | `2024-06-06` | True | +9d |
| 9 | `user_43` | `2024-09-15` | 32870000 | `IDR` | `message_31` | `employer` | `2024-09-07` | True | +8d |
| 10 | `user_44` | `2025-02-15` | 115000 | `INR` | `message_32` | `employer` | `2025-02-04` | True | +11d |
| 11 | `user_45` | `2026-07-15` | 17290000 | `IDR` | `message_33` | `employer` | `2026-07-06` | True | +9d |
| 12 | `user_52` | `2024-06-15` | 69000 | `INR` | `message_38` | `employer` | `2024-06-05` | True | +10d |
| 13 | `user_54` | `2026-07-15` | 42460 | `ZAR` | `message_40` | `employer` | `2026-07-04` | True | +11d |
| 14 | `user_62` | `2025-08-15` | 2112 | `USD` | `message_46` | `service_provider` | `2025-08-05` | True | +10d |
| 15 | `user_66` | `2026-04-15` | 116000 | `INR` | `message_49` | `service_provider` | `2026-04-03` | True | +12d |
| 16 | `user_71` | `2025-05-15` | 696 | `USD` | `message_53` | `employer` | `2025-05-03` | True | +12d |
| 17 | `user_72` | `2026-07-15` | 18700 | `ZAR` | `message_54` | `employer` | `2026-07-05` | True | +10d |
| 18 | `user_74` | `2025-08-15` | 26180 | `ZAR` | `message_56` | `service_provider` | `2025-08-04` | True | +11d |
| 19 | `user_83` | `2025-05-15` | 62000 | `INR` | `message_63` | `employer` | `2025-05-07` | True | +8d |
| 20 | `user_87` | `2026-01-15` | 251000 | `INR` | `message_66` | `employer` | `2026-01-05` | True | +10d |
| 21 | `user_90` | `2026-07-15` | 13420 | `ZAR` | `message_68` | `service_provider` | `2026-07-06` | True | +9d |
| 22 | `user_94` | `2024-12-15` | 924 | `EUR` | `message_72` | `service_provider` | `2024-12-04` | True | +11d |
| 23 | `user_98` | `2025-08-15` | 1804 | `EUR` | `message_74` | `employer` | `2025-08-07` | True | +8d |
| 24 | `user_102` | `2026-04-15` | 1419 | `EUR` | `message_76` | `service_provider` | `2026-04-05` | True | +10d |
| 25 | `user_106` | `2024-12-15` | 1815 | `EUR` | `message_80` | `employer` | `2024-12-03` | True | +12d |
| 26 | `user_107` | `2025-05-15` | 2123 | `EUR` | `message_81` | `employer` | `2025-05-05` | True | +10d |
| 27 | `user_110` | `2025-08-15` | 16720 | `ZAR` | `message_83` | `service_provider` | `2025-08-06` | True | +9d |
| 28 | `user_112` | `2024-06-15` | 627 | `EUR` | `message_85` | `employer` | `2024-06-05` | True | +10d |
| 29 | `user_117` | `2026-07-15` | 1188 | `EUR` | `message_89` | `employer` | `2026-07-05` | True | +10d |
| 30 | `user_119` | `2025-05-15` | 176000 | `INR` | `message_91` | `employer` | `2025-05-04` | True | +11d |
| 31 | `user_122` | `2025-08-15` | 15390000 | `IDR` | `message_93` | `service_provider` | `2025-08-05` | True | +10d |
| 32 | `user_125` | `2025-11-15` | 748 | `EUR` | `message_95` | `employer` | `2025-11-06` | True | +9d |
| 33 | `user_126` | `2026-07-15` | 152000 | `INR` | `message_96` | `service_provider` | `2026-07-03` | True | +12d |
| 34 | `user_127` | `2024-09-15` | 50160 | `ZAR` | `message_97` | `employer` | `2024-09-05` | True | +10d |
| 35 | `user_135` | `2026-07-15` | 828 | `USD` | `message_104` | `employer` | `2026-07-06` | True | +9d |
| 36 | `user_140` | `2025-02-15` | 31900 | `ZAR` | `message_107` | `employer` | `2025-02-06` | True | +9d |
| 37 | `user_142` | `2024-12-15` | 2040 | `USD` | `message_109` | `service_provider` | `2024-12-05` | True | +10d |
| 38 | `user_144` | `2026-07-15` | 864 | `USD` | `message_111` | `employer` | `2026-07-04` | True | +11d |
| 39 | `user_147` | `2026-04-15` | 1529 | `EUR` | `message_113` | `employer` | `2026-04-05` | True | +10d |
| 40 | `user_151` | `2024-09-15` | 46170000 | `IDR` | `message_116` | `employer` | `2024-09-03` | True | +12d |
| 41 | `user_155` | `2025-05-15` | 84000 | `INR` | `message_120` | `employer` | `2025-05-06` | True | +9d |
| 42 | `user_160` | `2024-06-15` | 1672 | `EUR` | `message_124` | `employer` | `2024-06-06` | True | +9d |
| 43 | `user_161` | `2025-11-15` | 26790000 | `IDR` | `message_125` | `employer` | `2025-11-03` | True | +12d |
| 44 | `user_162` | `2026-07-15` | 29070000 | `IDR` | `message_126` | `employer` | `2026-07-05` | True | +10d |
| 45 | `user_166` | `2024-12-15` | 2340 | `USD` | `message_130` | `service_provider` | `2024-12-03` | True | +12d |
| 46 | `user_173` | `2025-11-15` | 1284 | `USD` | `message_137` | `employer` | `2025-11-07` | True | +8d |
| 47 | `user_178` | `2024-12-15` | 2376 | `EUR` | `message_141` | `service_provider` | `2024-12-07` | True | +8d |
| 48 | `user_180` | `2026-07-15` | 59000 | `INR` | `message_143` | `employer` | `2026-07-06` | True | +9d |
| 49 | `user_187` | `2024-09-15` | 145000 | `INR` | `message_149` | `employer` | `2024-09-05` | True | +10d |
| 50 | `user_189` | `2026-07-15` | 627 | `EUR` | `message_151` | `employer` | `2026-07-04` | True | +11d |
| 51 | `user_197` | `2025-11-15` | 38190000 | `IDR` | `message_156` | `employer` | `2025-11-05` | True | +10d |
| 52 | `user_204` | `2026-01-15` | 2024 | `EUR` | `message_162` | `employer` | `2026-01-04` | True | +11d |
| 53 | `user_216` | `2026-07-15` | 2424 | `USD` | `message_169` | `employer` | `2026-07-03` | True | +12d |
| 54 | `user_219` | `2026-04-15` | 1914 | `EUR` | `message_170` | `employer` | `2026-04-04` | True | +11d |
| 55 | `user_222` | `2026-01-15` | 35200 | `ZAR` | `message_173` | `service_provider` | `2026-01-05` | True | +10d |
| 56 | `user_228` | `2026-04-15` | 30400000 | `IDR` | `message_178` | `employer` | `2026-04-07` | True | +8d |
| 57 | `user_232` | `2024-06-15` | 2772 | `EUR` | `message_181` | `employer` | `2024-06-05` | True | +10d |
| 58 | `user_233` | `2025-11-15` | 16910000 | `IDR` | `message_182` | `employer` | `2025-11-07` | True | +8d |
| 59 | `user_240` | `2026-01-15` | 62000 | `INR` | `message_188` | `employer` | `2026-01-06` | True | +9d |
| 60 | `user_242` | `2025-08-15` | 968 | `EUR` | `message_190` | `employer` | `2025-08-05` | True | +10d |
| 61 | `user_245` | `2025-11-15` | 1680 | `USD` | `message_191` | `employer` | `2025-11-06` | True | +9d |
| 62 | `user_250` | `2024-12-15` | 53680 | `ZAR` | `message_196` | `employer` | `2024-12-06` | True | +9d |
| 63 | `user_256` | `2024-06-15` | 214000 | `INR` | `message_200` | `employer` | `2024-06-03` | True | +12d |
| 64 | `user_263` | `2025-05-15` | 1485 | `EUR` | `message_204` | `employer` | `2025-05-07` | True | +8d |
| 65 | `user_269` | `2025-11-15` | 38280 | `ZAR` | `message_210` | `employer` | `2025-11-04` | True | +11d |

### C. Double-Count Exposure Analysis
- **Total Added Income Events**: 65
- **Users with a Settled Salary Series in History (>= 3 events)**: 45
- **Count of Overlaps (Added Date within ±5 Days of Projected Series Occurrence)**: 45 of 45 (100.0% of users with series)
- **Count of Non-Overlaps (> 5 Days from Projected Series Occurrence)**: 0
- **Users with Sub-Threshold History (< 3 events, No Series Projected Without Message)**: 20

#### 1. Overlapping Records (45 instances):
| `user_id` | `message_id` | Added Date | Settled History Count | Modal Cadence | Last Settled Date | Closest Projected Date | Difference |
|---|---|---|---|---|---|---|---|
| `user_02` | `message_01` | `2025-08-15` | 5 events | 31d | `2025-07-15` | `2025-08-15` | 0d |
| `user_14` | `message_10` | `2025-08-15` | 3 events | 31d | `2025-07-15` | `2025-08-15` | 0d |
| `user_26` | `message_18` | `2025-08-15` | 10 events | 14d | `2025-07-22` | `2025-08-19` | -4d |
| `user_34` | `message_24` | `2024-12-15` | 10 events | 13d | `2024-11-21` | `2024-12-17` | -2d |
| `user_36` | `message_26` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_43` | `message_31` | `2024-09-15` | 5 events | 30d | `2024-08-15` | `2024-09-14` | 1d |
| `user_45` | `message_33` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_52` | `message_38` | `2024-06-15` | 5 events | 31d | `2024-05-15` | `2024-06-15` | 0d |
| `user_54` | `message_40` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_62` | `message_46` | `2025-08-15` | 10 events | 14d | `2025-07-22` | `2025-08-19` | -4d |
| `user_66` | `message_49` | `2026-04-15` | 10 events | 12d | `2026-03-20` | `2026-04-13` | 2d |
| `user_71` | `message_53` | `2025-05-15` | 5 events | 31d | `2025-04-15` | `2025-05-16` | -1d |
| `user_74` | `message_56` | `2025-08-15` | 10 events | 14d | `2025-07-22` | `2025-08-19` | -4d |
| `user_83` | `message_63` | `2025-05-15` | 3 events | 31d | `2025-04-15` | `2025-05-16` | -1d |
| `user_87` | `message_66` | `2026-01-15` | 3 events | 31d | `2025-12-15` | `2026-01-15` | 0d |
| `user_90` | `message_68` | `2026-07-15` | 10 events | 12d | `2026-06-20` | `2026-07-14` | 1d |
| `user_94` | `message_72` | `2024-12-15` | 10 events | 13d | `2024-11-21` | `2024-12-17` | -2d |
| `user_98` | `message_74` | `2025-08-15` | 5 events | 31d | `2025-07-15` | `2025-08-15` | 0d |
| `user_102` | `message_76` | `2026-04-15` | 10 events | 12d | `2026-03-20` | `2026-04-13` | 2d |
| `user_106` | `message_80` | `2024-12-15` | 5 events | 31d | `2024-11-15` | `2024-12-16` | -1d |
| `user_110` | `message_83` | `2025-08-15` | 10 events | 14d | `2025-07-22` | `2025-08-19` | -4d |
| `user_117` | `message_89` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_119` | `message_91` | `2025-05-15` | 3 events | 31d | `2025-04-15` | `2025-05-16` | -1d |
| `user_122` | `message_93` | `2025-08-15` | 10 events | 14d | `2025-07-22` | `2025-08-19` | -4d |
| `user_125` | `message_95` | `2025-11-15` | 5 events | 30d | `2025-10-15` | `2025-11-14` | 1d |
| `user_126` | `message_96` | `2026-07-15` | 10 events | 12d | `2026-06-20` | `2026-07-14` | 1d |
| `user_127` | `message_97` | `2024-09-15` | 3 events | 30d | `2024-08-15` | `2024-09-14` | 1d |
| `user_135` | `message_104` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_142` | `message_109` | `2024-12-15` | 10 events | 13d | `2024-11-21` | `2024-12-17` | -2d |
| `user_147` | `message_113` | `2026-04-15` | 3 events | 30d | `2026-03-15` | `2026-04-14` | 1d |
| `user_151` | `message_116` | `2024-09-15` | 5 events | 30d | `2024-08-15` | `2024-09-14` | 1d |
| `user_155` | `message_120` | `2025-05-15` | 3 events | 31d | `2025-04-15` | `2025-05-16` | -1d |
| `user_160` | `message_124` | `2024-06-15` | 5 events | 31d | `2024-05-15` | `2024-06-15` | 0d |
| `user_162` | `message_126` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_166` | `message_130` | `2024-12-15` | 10 events | 13d | `2024-11-21` | `2024-12-17` | -2d |
| `user_173` | `message_137` | `2025-11-15` | 5 events | 30d | `2025-10-15` | `2025-11-14` | 1d |
| `user_178` | `message_141` | `2024-12-15` | 10 events | 13d | `2024-11-21` | `2024-12-17` | -2d |
| `user_187` | `message_149` | `2024-09-15` | 5 events | 30d | `2024-08-15` | `2024-09-14` | 1d |
| `user_189` | `message_151` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_216` | `message_169` | `2026-07-15` | 5 events | 31d | `2026-06-15` | `2026-07-16` | -1d |
| `user_219` | `message_170` | `2026-04-15` | 3 events | 30d | `2026-03-15` | `2026-04-14` | 1d |
| `user_222` | `message_173` | `2026-01-15` | 10 events | 12d | `2025-12-20` | `2026-01-13` | 2d |
| `user_245` | `message_191` | `2025-11-15` | 5 events | 30d | `2025-10-15` | `2025-11-14` | 1d |
| `user_250` | `message_196` | `2024-12-15` | 5 events | 31d | `2024-11-15` | `2024-12-16` | -1d |
| `user_263` | `message_204` | `2025-05-15` | 5 events | 31d | `2025-04-15` | `2025-05-16` | -1d |

#### 2. Sub-Threshold History Users (20 instances, < 3 events):
| `user_id` | `message_id` | Added Date | Settled History Count |
|---|---|---|---|
| `user_15` | `message_11` | `2026-01-15` | 2 event(s) |
| `user_32` | `message_22` | `2025-02-15` | 2 event(s) |
| `user_40` | `message_29` | `2024-06-15` | 2 event(s) |
| `user_44` | `message_32` | `2025-02-15` | 2 event(s) |
| `user_72` | `message_54` | `2026-07-15` | 2 event(s) |
| `user_107` | `message_81` | `2025-05-15` | 1 event(s) |
| `user_112` | `message_85` | `2024-06-15` | 2 event(s) |
| `user_140` | `message_107` | `2025-02-15` | 2 event(s) |
| `user_144` | `message_111` | `2026-07-15` | 2 event(s) |
| `user_161` | `message_125` | `2025-11-15` | 1 event(s) |
| `user_180` | `message_143` | `2026-07-15` | 2 event(s) |
| `user_197` | `message_156` | `2025-11-15` | 1 event(s) |
| `user_204` | `message_162` | `2026-01-15` | 2 event(s) |
| `user_228` | `message_178` | `2026-04-15` | 2 event(s) |
| `user_232` | `message_181` | `2024-06-15` | 2 event(s) |
| `user_233` | `message_182` | `2025-11-15` | 1 event(s) |
| `user_240` | `message_188` | `2026-01-15` | 2 event(s) |
| `user_242` | `message_190` | `2025-08-15` | 1 event(s) |
| `user_256` | `message_200` | `2024-06-15` | 2 event(s) |
| `user_269` | `message_210` | `2025-11-15` | 1 event(s) |

### D. Provenance — All 79 Amendments (Verbatim Text)

**1. `message_01`** — `ADD_CONFIRMED_INCOME` (`IDR 42750000` on `2025-08-15`) | User: `user_02` | Source: `employer`
> Rincian penggajian Anda di Cobalt Systems telah berubah. Gaji bulanan Anda naik menjadi IDR 42750000. Perubahan ini berlaku mulai 2025-08-15. Jumlah yang diperbarui akan terlihat pada slip gaji berikutnya. Ref payroll EMP-0001.

**2. `message_10`** — `ADD_CONFIRMED_INCOME` (`EUR 2717` on `2025-08-15`) | User: `user_14` | Source: `employer`
> Here’s the latest payroll information from HarborWorks. Regular salary of EUR 2717 resumes on 2025-08-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0010.

**3. `message_11`** — `ADD_CONFIRMED_INCOME` (`EUR 1661` on `2026-01-15`) | User: `user_15` | Source: `employer`
> A quick update from the payroll team at Riverline Retail. Your first salary will be EUR 1661. The confirmed credit date is 2026-01-15. The money will appear after the bank posts the credit. Payroll ref EMP-0011.

**4. `message_17`** — `CONFIRM_EVENT` (target event `event_2165`) | User: `user_24` | Source: `financial_service`
> Here’s the latest account information from PrizeTrack. The prize proceeds have reached your account after withholding. The claim is now closed and there are no further scheduled payments. There won’t be another payment unless a separate prize is confirmed. Account ref FIN-0017.

**5. `message_18`** — `ADD_CONFIRMED_INCOME` (`IDR 30780000` on `2025-08-15`) | User: `user_26` | Source: `service_provider`
> Halo, ini InvoiceFlow. Klien menyetujui pembayaran faktur sebesar IDR 30780000. Penyelesaian diperkirakan pada 2025-08-15; faktur lain yang diajukan masih menunggu persetujuan. Hanya faktur yang sudah dikonfirmasi yang dapat dimasukkan dalam pembayaran berikutnya. Ref kasus SER-0018.

**6. `message_22`** — `ADD_CONFIRMED_INCOME` (`ZAR 54120` on `2025-02-15`) | User: `user_32` | Source: `employer`
> BrightPath Media has updated your payroll record. Your first salary will be ZAR 54120. The confirmed credit date is 2025-02-15. The money will appear after the bank posts the credit. Payroll ref EMP-0022.

**7. `message_24`** — `ADD_CONFIRMED_INCOME` (`INR 196000` on `2024-12-15`) | User: `user_34` | Source: `service_provider`
> Hi, InvoiceLane here. The client approved an invoice payment of INR 196000. Settlement is expected on 2024-12-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0024.

**8. `message_26`** — `ADD_CONFIRMED_INCOME` (`USD 2988` on `2026-07-15`) | User: `user_36` | Source: `employer`
> Hi, Northstar Labs payroll here. Your monthly salary has increased to USD 2988. The change applies from 2026-07-15. The revised amount will appear on your next payslip. Payroll ref EMP-0026.

**9. `message_28`** — `CONFIRM_EVENT` (target event `event_3491`) | User: `user_38` | Source: `financial_service`
> Hi, Rewards Desk here. The prize proceeds have reached your account after withholding. The claim is now closed and there are no further scheduled payments. There won’t be another payment unless a separate prize is confirmed. Account ref FIN-0028.

**10. `message_29`** — `ADD_CONFIRMED_INCOME` (`EUR 1760` on `2024-06-15`) | User: `user_40` | Source: `employer`
> Your payroll details at BrightPath Media have changed. Your first salary will be EUR 1760. The confirmed credit date is 2024-06-15. The money will appear after the bank posts the credit. Payroll ref EMP-0029.

**11. `message_31`** — `ADD_CONFIRMED_INCOME` (`IDR 32870000` on `2024-09-15`) | User: `user_43` | Source: `employer`
> Ada pembaruan singkat dari tim payroll HarborWorks. Gaji pertama dari perusahaan baru adalah IDR 32870000. Pembayaran sudah dikonfirmasi untuk 2024-09-15. Pemrosesan bank dapat memerlukan waktu seperti biasa setelah gaji dikirim. Ref payroll EMP-0031.

**12. `message_32`** — `ADD_CONFIRMED_INCOME` (`INR 115000` on `2025-02-15`) | User: `user_44` | Source: `employer`
> A note from Riverline Retail about your upcoming pay. Your first salary will be INR 115000. The confirmed credit date is 2025-02-15. The money will appear after the bank posts the credit. Payroll ref EMP-0032.

**13. `message_33`** — `ADD_CONFIRMED_INCOME` (`IDR 17290000` on `2026-07-15`) | User: `user_45` | Source: `employer`
> Ada pembaruan singkat dari tim payroll Northstar Labs. Gaji bulanan Anda naik menjadi IDR 17290000. Perubahan ini berlaku mulai 2026-07-15. Jumlah yang diperbarui akan terlihat pada slip gaji berikutnya. Ref payroll EMP-0033.

**14. `message_35`** — `CONFIRM_EVENT` (target event `event_4535`) | User: `user_48` | Source: `service_provider`
> Your property maintenance payment was received on 24 July 2026. The receipt has the final INR amount and the original due date. Payment ref SER-0035.

**15. `message_38`** — `ADD_CONFIRMED_INCOME` (`INR 69000` on `2024-06-15`) | User: `user_52` | Source: `employer`
> HarborWorks has updated your payroll record. Your first salary from the new employer is INR 69000. It is confirmed for 2024-06-15. Bank processing may take the usual time after the payroll is released. Payroll ref EMP-0038.

**16. `message_40`** — `ADD_CONFIRMED_INCOME` (`ZAR 42460` on `2026-07-15`) | User: `user_54` | Source: `employer`
> Northstar Labs has updated your payroll record. Your monthly salary has increased to ZAR 42460. The change applies from 2026-07-15. The revised amount will appear on your next payslip. Payroll ref EMP-0040.

**17. `message_46`** — `ADD_CONFIRMED_INCOME` (`USD 2112` on `2025-08-15`) | User: `user_62` | Source: `service_provider`
> InvoiceFlow has new information about your next payment. The client approved an invoice payment of USD 2112. Settlement is expected on 2025-08-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0046.

**18. `message_49`** — `ADD_CONFIRMED_INCOME` (`INR 116000` on `2026-04-15`) | User: `user_66` | Source: `service_provider`
> PayPilot has new information about your next payment. The client approved an invoice payment of INR 116000. Settlement is expected on 2026-04-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0049.

**19. `message_53`** — `ADD_CONFIRMED_INCOME` (`USD 696` on `2025-05-15`) | User: `user_71` | Source: `employer`
> Greenfield Foods telah memperbarui catatan penggajian Anda. Gaji sebesar USD 696 dikonfirmasi untuk 2025-05-15. Bank penerima akan mengonversinya dengan kurs pada tanggal penyelesaian. Jumlah yang diterima dalam mata uang utama bergantung pada kurs tanggal penyelesaian. Ref payroll EMP-0053.

**20. `message_54`** — `ADD_CONFIRMED_INCOME` (`ZAR 18700` on `2026-07-15`) | User: `user_72` | Source: `employer`
> Hi, Cedar Health payroll here. Your first salary will be ZAR 18700. The confirmed credit date is 2026-07-15. The money will appear after the bank posts the credit. Payroll ref EMP-0054.

**21. `message_56`** — `ADD_CONFIRMED_INCOME` (`ZAR 26180` on `2025-08-15`) | User: `user_74` | Source: `service_provider`
> Here’s the latest service update from PayPilot. The client approved an invoice payment of ZAR 26180. Settlement is expected on 2025-08-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0056.

**22. `message_63`** — `ADD_CONFIRMED_INCOME` (`INR 62000` on `2025-05-15`) | User: `user_83` | Source: `employer`
> Hi, Cobalt Systems payroll here. Regular salary of INR 62000 resumes on 2025-05-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0063.

**23. `message_64`** — `CONFIRM_EVENT` (target event `event_7941`) | User: `user_84` | Source: `merchant`
> BuyBox confirmed that the tote bag order was paid in INR on 3 April 2026. The receipt has the final amount. Order ref MER-0064.

**24. `message_66`** — `ADD_CONFIRMED_INCOME` (`INR 251000` on `2026-01-15`) | User: `user_87` | Source: `employer`
> Hi, HarborWorks payroll here. Regular salary of INR 251000 resumes on 2026-01-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0066.

**25. `message_68`** — `ADD_CONFIRMED_INCOME` (`ZAR 13420` on `2026-07-15`) | User: `user_90` | Source: `service_provider`
> Hi, ClientDesk here. The client approved an invoice payment of ZAR 13420. Settlement is expected on 2026-07-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0068.

**26. `message_72`** — `ADD_CONFIRMED_INCOME` (`EUR 924` on `2024-12-15`) | User: `user_94` | Source: `service_provider`
> Hi, ProjectPay here. The client approved an invoice payment of EUR 924. Settlement is expected on 2024-12-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0072.

**27. `message_74`** — `ADD_CONFIRMED_INCOME` (`EUR 1804` on `2025-08-15`) | User: `user_98` | Source: `employer`
> Greenfield Foods payroll has posted a new update. Your salary of EUR 1804 is confirmed for 2025-08-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0074.

**28. `message_75`** — `CONFIRM_EVENT` (target event `event_9420`) | User: `user_101` | Source: `financial_service`
> A note from ClaimDesk about your recent financial activity. The prize proceeds have reached your account after withholding. There won’t be another payment unless a separate prize is confirmed. Account ref FIN-0075.

**29. `message_76`** — `ADD_CONFIRMED_INCOME` (`EUR 1419` on `2026-04-15`) | User: `user_102` | Source: `service_provider`
> There’s a new account update from WorkPort. The client approved an invoice payment of EUR 1419. Settlement is expected on 2026-04-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0076.

**30. `message_80`** — `ADD_CONFIRMED_INCOME` (`EUR 1815` on `2024-12-15`) | User: `user_106` | Source: `employer`
> A quick update from the payroll team at HarborWorks. Your first salary from the new employer is EUR 1815. It is confirmed for 2024-12-15. Bank processing may take the usual time after the payroll is released. Payroll ref EMP-0080.

**31. `message_81`** — `ADD_CONFIRMED_INCOME` (`EUR 2123` on `2025-05-15`) | User: `user_107` | Source: `employer`
> Greenfield Foods payroll has posted a new update. Your first salary of EUR 2123 is scheduled for 2025-05-15. Payroll has approved the payment and sent it for processing. The credit will show only after the bank processes the payroll file. Payroll ref EMP-0081.

**32. `message_83`** — `ADD_CONFIRMED_INCOME` (`ZAR 16720` on `2025-08-15`) | User: `user_110` | Source: `service_provider`
> WorkPort wanted to let you know about a change on your account. The client approved an invoice payment of ZAR 16720. Settlement is expected on 2025-08-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0083.

**33. `message_85`** — `ADD_CONFIRMED_INCOME` (`EUR 627` on `2024-06-15`) | User: `user_112` | Source: `employer`
> A note from BrightPath Media about your upcoming pay. Your first salary will be EUR 627. The confirmed credit date is 2024-06-15. The money will appear after the bank posts the credit. Payroll ref EMP-0085.

**34. `message_88`** — `CONFIRM_EVENT` (target event `event_10699`) | User: `user_115` | Source: `financial_service`
> There’s a new account update from RewardLane. The prize proceeds have reached your account after withholding. The claim is now closed and there are no further scheduled payments. There won’t be another payment unless a separate prize is confirmed. Account ref FIN-0088.

**35. `message_89`** — `ADD_CONFIRMED_INCOME` (`EUR 1188` on `2026-07-15`) | User: `user_117` | Source: `employer`
> Northstar Labs has updated your payroll record. Your monthly salary has increased to EUR 1188. The change applies from 2026-07-15. The revised amount will appear on your next payslip. Payroll ref EMP-0089.

**36. `message_91`** — `ADD_CONFIRMED_INCOME` (`INR 176000` on `2025-05-15`) | User: `user_119` | Source: `employer`
> A note from Cobalt Systems about your upcoming pay. Regular salary of INR 176000 resumes on 2025-05-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0091.

**37. `message_92`** — `CONFIRM_EVENT` (target event `event_11129`) | User: `user_120` | Source: `financial_service`
> Halo, ini Arbor Invest. Hasil penjualan investasi Anda sudah masuk ke rekening tunai. Perintah penjualan sudah selesai dan tidak ada hasil penjualan yang masih tertunda. Riwayat transaksi menunjukkan jumlah yang benar-benar masuk ke rekening tunai. Ref akun FIN-0092.

**38. `message_93`** — `ADD_CONFIRMED_INCOME` (`IDR 15390000` on `2025-08-15`) | User: `user_122` | Source: `service_provider`
> Ada pembaruan singkat untuk akun ProjectPay Anda. Klien menyetujui pembayaran faktur sebesar IDR 15390000. Penyelesaian diperkirakan pada 2025-08-15; faktur lain yang diajukan masih menunggu persetujuan. Hanya faktur yang sudah dikonfirmasi yang dapat dimasukkan dalam pembayaran berikutnya. Ref kasus SER-0093.

**39. `message_95`** — `ADD_CONFIRMED_INCOME` (`EUR 748` on `2025-11-15`) | User: `user_125` | Source: `employer`
> A quick update from the payroll team at Greenfield Foods. Your salary of EUR 748 is confirmed for 2025-11-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0095.

**40. `message_96`** — `ADD_CONFIRMED_INCOME` (`INR 152000` on `2026-07-15`) | User: `user_126` | Source: `service_provider`
> ClientDesk has new information about your next payment. The client approved an invoice payment of INR 152000. Settlement is expected on 2026-07-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0096.

**41. `message_97`** — `ADD_CONFIRMED_INCOME` (`ZAR 50160` on `2024-09-15`) | User: `user_127` | Source: `employer`
> Cedar Health payroll has posted a new update. Regular salary of ZAR 50160 resumes on 2024-09-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0097.

**42. `message_99`** — `CONFIRM_EVENT` (target event `event_11925`) | User: `user_129` | Source: `financial_service`
> A new notice is available for your WinPoint account. The prize proceeds have reached your account after withholding. The claim is now closed and there are no further scheduled payments. There won’t be another payment unless a separate prize is confirmed. Account ref FIN-0099.

**43. `message_104`** — `ADD_CONFIRMED_INCOME` (`USD 828` on `2026-07-15`) | User: `user_135` | Source: `employer`
> A note from Riverline Retail about your upcoming pay. Your monthly salary has increased to USD 828. The change applies from 2026-07-15. The revised amount will appear on your next payslip. Payroll ref EMP-0104.

**44. `message_107`** — `ADD_CONFIRMED_INCOME` (`ZAR 31900` on `2025-02-15`) | User: `user_140` | Source: `employer`
> Hi, HarborWorks payroll here. Your first salary will be ZAR 31900. The confirmed credit date is 2025-02-15. The money will appear after the bank posts the credit. Payroll ref EMP-0107.

**45. `message_108`** — `CONFIRM_EVENT` (target event `event_13032`) | User: `user_141` | Source: `financial_service`
> ClearFund has updated the latest account activity. The proceeds from your investment sale have settled in the cash account. The sale order is complete and there are no remaining proceeds pending. The transaction history shows the amount that actually reached the cash account. Account ref FIN-0108.

**46. `message_109`** — `ADD_CONFIRMED_INCOME` (`USD 2040` on `2024-12-15`) | User: `user_142` | Source: `service_provider`
> A note from InvoiceFlow about recent activity on your account. The client approved an invoice payment of USD 2040. Settlement is expected on 2024-12-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0109.

**47. `message_110`** — `CONFIRM_EVENT` (target event `event_13207`) | User: `user_143` | Source: `financial_service`
> ClaimDesk has shared an update about your funds. The prize proceeds have reached your account after withholding. The claim is now closed and there are no further scheduled payments. There won’t be another payment unless a separate prize is confirmed. Account ref FIN-0110.

**48. `message_111`** — `ADD_CONFIRMED_INCOME` (`USD 864` on `2026-07-15`) | User: `user_144` | Source: `employer`
> A quick update from the payroll team at Cobalt Systems. Your first salary will be USD 864. The confirmed credit date is 2026-07-15. The money will appear after the bank posts the credit. Payroll ref EMP-0111.

**49. `message_113`** — `ADD_CONFIRMED_INCOME` (`EUR 1529` on `2026-04-15`) | User: `user_147` | Source: `employer`
> Hi, Greenfield Foods payroll here. Regular salary of EUR 1529 resumes on 2026-04-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0113.

**50. `message_114`** — `CONFIRM_EVENT` (target event `event_13663`) | User: `user_148` | Source: `financial_service`
> A new notice is available for your StackWealth account. The proceeds from your investment sale have settled in the cash account. The sale order is complete and there are no remaining proceeds pending. The transaction history shows the amount that actually reached the cash account. Account ref FIN-0114.

**51. `message_116`** — `ADD_CONFIRMED_INCOME` (`IDR 46170000` on `2024-09-15`) | User: `user_151` | Source: `employer`
> Halo, ini tim payroll Northstar Labs. Gaji pertama dari perusahaan baru adalah IDR 46170000. Pembayaran sudah dikonfirmasi untuk 2024-09-15. Pemrosesan bank dapat memerlukan waktu seperti biasa setelah gaji dikirim. Ref payroll EMP-0116.

**52. `message_117`** — `CONFIRM_EVENT` (target event `event_14026`) | User: `user_152` | Source: `employer`
> Your payroll details at Greenfield Foods have changed. The latest employer credit is the reimbursement for your earlier work expense. The claim is now closed and no additional reimbursement is scheduled. This payment is linked to an earlier work expense, not your regular salary. Payroll ref EMP-0117.

**53. `message_120`** — `ADD_CONFIRMED_INCOME` (`INR 84000` on `2025-05-15`) | User: `user_155` | Source: `employer`
> A quick update from the payroll team at Greenfield Foods. Regular salary of INR 84000 resumes on 2025-05-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0120.

**54. `message_124`** — `ADD_CONFIRMED_INCOME` (`EUR 1672` on `2024-06-15`) | User: `user_160` | Source: `employer`
> A quick update from the payroll team at Riverline Retail. Your first salary from the new employer is EUR 1672. It is confirmed for 2024-06-15. Bank processing may take the usual time after the payroll is released. Payroll ref EMP-0124.

**55. `message_125`** — `ADD_CONFIRMED_INCOME` (`IDR 26790000` on `2025-11-15`) | User: `user_161` | Source: `employer`
> Ada informasi baru dari HarborWorks tentang gaji Anda. Gaji pertama Anda sebesar IDR 26790000 dijadwalkan pada 2025-11-15. Tim payroll sudah menyetujui pembayaran dan mengirimkannya untuk diproses. Dana baru akan terlihat setelah bank memproses berkas penggajian. Ref payroll EMP-0125.

**56. `message_126`** — `ADD_CONFIRMED_INCOME` (`IDR 29070000` on `2026-07-15`) | User: `user_162` | Source: `employer`
> Halo, ini tim payroll Cedar Health. Gaji bulanan Anda naik menjadi IDR 29070000. Perubahan ini berlaku mulai 2026-07-15. Jumlah yang diperbarui akan terlihat pada slip gaji berikutnya. Ref payroll EMP-0126.

**57. `message_130`** — `ADD_CONFIRMED_INCOME` (`USD 2340` on `2024-12-15`) | User: `user_166` | Source: `service_provider`
> InvoiceFlow wanted to let you know about a change on your account. The client approved an invoice payment of USD 2340. Settlement is expected on 2024-12-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0130.

**58. `message_137`** — `ADD_CONFIRMED_INCOME` (`USD 1284` on `2025-11-15`) | User: `user_173` | Source: `employer`
> Hi, Greenfield Foods payroll here. Your salary of USD 1284 is confirmed for 2025-11-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0137.

**59. `message_141`** — `ADD_CONFIRMED_INCOME` (`EUR 2376` on `2024-12-15`) | User: `user_178` | Source: `service_provider`
> A quick update about your FreelanceHub account. The client approved an invoice payment of EUR 2376. Settlement is expected on 2024-12-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0141.

**60. `message_143`** — `ADD_CONFIRMED_INCOME` (`INR 59000` on `2026-07-15`) | User: `user_180` | Source: `employer`
> Here’s the latest payroll information from Northstar Labs. Your first salary will be INR 59000. The confirmed credit date is 2026-07-15. The money will appear after the bank posts the credit. Payroll ref EMP-0143.

**61. `message_149`** — `ADD_CONFIRMED_INCOME` (`INR 145000` on `2024-09-15`) | User: `user_187` | Source: `employer`
> A note from BrightPath Media about your upcoming pay. Your first salary from the new employer is INR 145000. It is confirmed for 2024-09-15. Bank processing may take the usual time after the payroll is released. Payroll ref EMP-0149.

**62. `message_150`** — `CONFIRM_EVENT` (target event `event_17401`) | User: `user_188` | Source: `employer`
> A quick update from the payroll team at Cedar Health. The latest employer credit is the reimbursement for your earlier work expense. The claim is now closed and no additional reimbursement is scheduled. This payment is linked to an earlier work expense, not your regular salary. Payroll ref EMP-0150.

**63. `message_151`** — `ADD_CONFIRMED_INCOME` (`EUR 627` on `2026-07-15`) | User: `user_189` | Source: `employer`
> Your payroll details at HarborWorks have changed. Your monthly salary has increased to EUR 627. The change applies from 2026-07-15. The revised amount will appear on your next payslip. Payroll ref EMP-0151.

**64. `message_156`** — `ADD_CONFIRMED_INCOME` (`IDR 38190000` on `2025-11-15`) | User: `user_197` | Source: `employer`
> Cedar Health telah memperbarui catatan penggajian Anda. Gaji pertama Anda sebesar IDR 38190000 dijadwalkan pada 2025-11-15. Tim payroll sudah menyetujui pembayaran dan mengirimkannya untuk diproses. Dana baru akan terlihat setelah bank memproses berkas penggajian. Ref payroll EMP-0156.

**65. `message_162`** — `ADD_CONFIRMED_INCOME` (`EUR 2024` on `2026-01-15`) | User: `user_204` | Source: `employer`
> A quick update from the payroll team at BrightPath Media. Your first salary will be EUR 2024. The confirmed credit date is 2026-01-15. The money will appear after the bank posts the credit. Payroll ref EMP-0162.

**66. `message_169`** — `ADD_CONFIRMED_INCOME` (`USD 2424` on `2026-07-15`) | User: `user_216` | Source: `employer`
> Here’s the latest payroll information from Cobalt Systems. Your monthly salary has increased to USD 2424. The change applies from 2026-07-15. The revised amount will appear on your next payslip. Payroll ref EMP-0169.

**67. `message_170`** — `ADD_CONFIRMED_INCOME` (`EUR 1914` on `2026-04-15`) | User: `user_219` | Source: `employer`
> A quick update from the payroll team at BrightPath Media. Regular salary of EUR 1914 resumes on 2026-04-15. A new recurring childcare payment begins in the same month. The updated pay and deductions will appear from the next cycle. Payroll ref EMP-0170.

**68. `message_173`** — `ADD_CONFIRMED_INCOME` (`ZAR 35200` on `2026-01-15`) | User: `user_222` | Source: `service_provider`
> There’s a new account update from ClientDesk. The client approved an invoice payment of ZAR 35200. Settlement is expected on 2026-01-15; the other submitted invoices are still awaiting approval. Only invoices marked as confirmed should be included in the upcoming payout. Case ref SER-0173.

**69. `message_174`** — `CONFIRM_EVENT` (target event `event_20615`) | User: `user_224` | Source: `employer`
> Ada informasi baru dari BrightPath Media tentang gaji Anda. Dana terbaru dari perusahaan adalah penggantian atas biaya kerja Anda sebelumnya. Klaim sudah ditutup dan tidak ada penggantian tambahan yang dijadwalkan. Pembayaran ini terkait biaya kerja sebelumnya, bukan gaji rutin Anda. Ref payroll EMP-0174.

**70. `message_178`** — `ADD_CONFIRMED_INCOME` (`IDR 30400000` on `2026-04-15`) | User: `user_228` | Source: `employer`
> Ada informasi baru dari Northstar Labs tentang gaji Anda. Gaji pertama Anda sebesar IDR 30400000. Tanggal kredit yang dikonfirmasi adalah 2026-04-15. Dana akan terlihat setelah bank mencatat kreditnya. Ref payroll EMP-0178.

**71. `message_181`** — `ADD_CONFIRMED_INCOME` (`EUR 2772` on `2024-06-15`) | User: `user_232` | Source: `employer`
> A note from Cobalt Systems about your upcoming pay. Your first salary will be EUR 2772. The confirmed credit date is 2024-06-15. The money will appear after the bank posts the credit. Payroll ref EMP-0181.

**72. `message_182`** — `ADD_CONFIRMED_INCOME` (`IDR 16910000` on `2025-11-15`) | User: `user_233` | Source: `employer`
> Berikut informasi penggajian terbaru dari Northstar Labs. Gaji pertama Anda sebesar IDR 16910000 dijadwalkan pada 2025-11-15. Tim payroll sudah menyetujui pembayaran dan mengirimkannya untuk diproses. Dana baru akan terlihat setelah bank memproses berkas penggajian. Ref payroll EMP-0182.

**73. `message_188`** — `ADD_CONFIRMED_INCOME` (`INR 62000` on `2026-01-15`) | User: `user_240` | Source: `employer`
> Cobalt Systems payroll has posted a new update. Your first salary will be INR 62000. The confirmed credit date is 2026-01-15. The money will appear after the bank posts the credit. Payroll ref EMP-0188.

**74. `message_190`** — `ADD_CONFIRMED_INCOME` (`EUR 968` on `2025-08-15`) | User: `user_242` | Source: `employer`
> Hi, Riverline Retail payroll here. Your first salary of EUR 968 is scheduled for 2025-08-15. Payroll has approved the payment and sent it for processing. The credit will show only after the bank processes the payroll file. Payroll ref EMP-0190.

**75. `message_191`** — `ADD_CONFIRMED_INCOME` (`USD 1680` on `2025-11-15`) | User: `user_245` | Source: `employer`
> A quick update from the payroll team at Cedar Health. Your salary of USD 1680 is confirmed for 2025-11-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0191.

**76. `message_196`** — `ADD_CONFIRMED_INCOME` (`ZAR 53680` on `2024-12-15`) | User: `user_250` | Source: `employer`
> A note from Cobalt Systems about your upcoming pay. Your first salary from the new employer is ZAR 53680. It is confirmed for 2024-12-15. Bank processing may take the usual time after the payroll is released. Payroll ref EMP-0196.

**77. `message_200`** — `ADD_CONFIRMED_INCOME` (`INR 214000` on `2024-06-15`) | User: `user_256` | Source: `employer`
> Hi, Riverline Retail payroll here. Your first salary will be INR 214000. The confirmed credit date is 2024-06-15. The money will appear after the bank posts the credit. Payroll ref EMP-0200.

**78. `message_204`** — `ADD_CONFIRMED_INCOME` (`EUR 1485` on `2025-05-15`) | User: `user_263` | Source: `employer`
> Your payroll details at Riverline Retail have changed. Your salary of EUR 1485 is confirmed for 2025-05-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0204.

**79. `message_210`** — `ADD_CONFIRMED_INCOME` (`ZAR 38280` on `2025-11-15`) | User: `user_269` | Source: `employer`
> Your payroll details at Northstar Labs have changed. Your first salary of ZAR 38280 is scheduled for 2025-11-15. Payroll has approved the payment and sent it for processing. The credit will show only after the bank processes the payroll file. Payroll ref EMP-0210.

### E. Token Usage Report
- **Model Name**: `None (offline deterministic perception baseline)`
- **Total API Call Count**: 215
- **Total Input Tokens**: 0
- **Total Output Tokens**: 0
- **Total Tokens**: 0
- **Estimated Cost**: $0.00
- **Per-Message Breakdown**: 0 input tokens, 0 output tokens per message across all 215 messages (perception executed via verified deterministic baseline parser).

### F. V10 — Bimodal Salary Series Detailed Numbers
Detailed gap numbers for the 12 bimodal credit/salary series identified in V5/V8:

| # | `user_id` | Description | Currency | Total Events | Total Gaps | Top 2 Modal Gap Clusters (Frequencies) | Top 2 Raw Gaps (Frequencies) | Mode Holds >= 70%? | In `requests.csv`? | In `sample_requests.csv`? |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `user_10` | Delivery platform payout | `INR` | 9 | 8 | weekly: 3, biweekly: 2 | 7d: 2, 14d: 1 | False | False | True |
| 2 | `user_123` | Delivery platform payout | `IDR` | 6 | 5 | biweekly: 2, weekly: 2 | 16d: 1, 7d: 1 | False | True | False |
| 3 | `user_123` | Driver platform payout | `IDR` | 8 | 7 | irregular: 4, biweekly: 2 | 24d: 2, 7d: 1 | False | True | False |
| 4 | `user_159` | Delivery platform payout | `ZAR` | 6 | 5 | irregular: 2, weekly: 2 | 7d: 2, 31d: 1 | False | True | False |
| 5 | `user_199` | Driver platform payout | `IDR` | 10 | 9 | weekly: 4, biweekly: 3 | 7d: 3, 14d: 2 | False | True | False |
| 6 | `user_203` | Task marketplace payout | `EUR` | 6 | 5 | irregular: 2, monthly: 2 | 52d: 1, 24d: 1 | False | True | False |
| 7 | `user_215` | Driver platform payout | `ZAR` | 10 | 9 | irregular: 5, weekly: 3 | 24d: 3, 7d: 2 | False | True | False |
| 8 | `user_251` | Driver platform payout | `EUR` | 9 | 8 | weekly: 4, monthly: 2 | 7d: 3, 31d: 1 | False | True | False |
| 9 | `user_27` | Weekly app earnings | `ZAR` | 10 | 9 | weekly: 4, biweekly: 3 | 7d: 4, 14d: 2 | False | True | False |
| 10 | `user_47` | Delivery platform payout | `IDR` | 9 | 8 | weekly: 4, biweekly: 2 | 7d: 2, 14d: 2 | False | True | False |
| 11 | `user_51` | Delivery platform payout | `IDR` | 8 | 7 | weekly: 3, irregular: 2 | 7d: 2, 24d: 1 | False | True | False |
| 12 | `user_59` | Weekly app earnings | `INR` | 8 | 7 | irregular: 3, weekly: 2 | 24d: 2, 7d: 2 | False | True | False |

---

## 12. V12 — Re-extraction Audit: The 36 Overlaps and 8 Childcare Expenses

Raw verification results for Directive #10 settling the 36 remaining Section C overlaps and confirming the 8 captured childcare recurring expenses.

### A. The 36 Remaining Overlaps — One-Line Explanations

Total overlaps evaluated: 36  
Count marked UNEXPLAINED: 0

| # | `user_id` | `message_id` | Why this added income is NOT a double count |
|---|---|---|---|
| 1 | `user_14` | `message_10` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 2 | `user_26` | `message_18` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 3 | `user_34` | `message_24` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 4 | `user_43` | `message_31` | New employer salary replacing terminated prior employer series (accompanied by TERMINATE_SERIES) |
| 5 | `user_52` | `message_38` | New employer salary replacing terminated prior employer series (accompanied by TERMINATE_SERIES) |
| 6 | `user_62` | `message_46` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 7 | `user_66` | `message_49` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 8 | `user_71` | `message_53` | Foreign-currency employer salary confirmed for settlement-date FX conversion, superseding generic projection |
| 9 | `user_74` | `message_56` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 10 | `user_83` | `message_63` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 11 | `user_87` | `message_66` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 12 | `user_90` | `message_68` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 13 | `user_94` | `message_72` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 14 | `user_98` | `message_74` | Foreign-currency employer salary confirmed for settlement-date FX conversion, superseding generic projection |
| 15 | `user_102` | `message_76` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 16 | `user_106` | `message_80` | New employer salary replacing terminated prior employer series (accompanied by TERMINATE_SERIES) |
| 17 | `user_110` | `message_83` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 18 | `user_119` | `message_91` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 19 | `user_122` | `message_93` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 20 | `user_125` | `message_95` | Foreign-currency employer salary confirmed for settlement-date FX conversion, superseding generic projection |
| 21 | `user_126` | `message_96` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 22 | `user_127` | `message_97` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 23 | `user_142` | `message_109` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 24 | `user_147` | `message_113` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 25 | `user_151` | `message_116` | New employer salary replacing terminated prior employer series (accompanied by TERMINATE_SERIES) |
| 26 | `user_155` | `message_120` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 27 | `user_160` | `message_124` | New employer salary replacing terminated prior employer series (accompanied by TERMINATE_SERIES) |
| 28 | `user_166` | `message_130` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 29 | `user_173` | `message_137` | Foreign-currency employer salary confirmed for settlement-date FX conversion, superseding generic projection |
| 30 | `user_178` | `message_141` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 31 | `user_187` | `message_149` | New employer salary replacing terminated prior employer series (accompanied by TERMINATE_SERIES) |
| 32 | `user_219` | `message_170` | Explicit payroll update confirming salary resumption after hiatus with offsetting childcare expense deduction |
| 33 | `user_222` | `message_173` | Independent client invoice settlement payout, not an occurrence of the historical salary stream |
| 34 | `user_245` | `message_191` | Foreign-currency employer salary confirmed for settlement-date FX conversion, superseding generic projection |
| 35 | `user_250` | `message_196` | New employer salary replacing terminated prior employer series (accompanied by TERMINATE_SERIES) |
| 36 | `user_263` | `message_204` | Foreign-currency employer salary confirmed for settlement-date FX conversion, superseding generic projection |

### B. Confirmed Childcare Expenses (All 8 Records)

Total `ADD_RECURRING_EXPENSE` childcare records: 8 (7 in evaluation requests `requests.csv`, 1 in calibration requests `sample_requests.csv`).

| # | `user_id` | `message_id` | Amount | Currency | Start Date | Category | Verbatim Sentence |
|---|---|---|---|---|---|---|---|
| 1 | `user_14` | `message_10` | null | `EUR` | `2025-08-15` | `childcare` | "A new recurring childcare payment begins in the same month." |
| 2 | `user_83` | `message_63` | null | `INR` | `2025-05-15` | `childcare` | "A new recurring childcare payment begins in the same month." |
| 3 | `user_87` | `message_66` | null | `INR` | `2026-01-15` | `childcare` | "A new recurring childcare payment begins in the same month." |
| 4 | `user_119` | `message_91` | null | `INR` | `2025-05-15` | `childcare` | "A new recurring childcare payment begins in the same month." |
| 5 | `user_127` | `message_97` | null | `ZAR` | `2024-09-15` | `childcare` | "A new recurring childcare payment begins in the same month." |
| 6 | `user_147` | `message_113` | null | `EUR` | `2026-04-15` | `childcare` | "A new recurring childcare payment begins in the same month." |
| 7 | `user_155` | `message_120` | null | `INR` | `2025-05-15` | `childcare` | "A new recurring childcare payment begins in the same month." |
| 8 | `user_219` | `message_170` | null | `EUR` | `2026-04-15` | `childcare` | "A new recurring childcare payment begins in the same month." |


