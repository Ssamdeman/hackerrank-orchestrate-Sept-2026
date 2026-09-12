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
