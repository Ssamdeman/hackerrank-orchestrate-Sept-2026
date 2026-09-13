# Message Amendment Extraction Comparison

This document compares the deterministic baseline extractions (`src/data/message_amendments.json`) against the `claude-sonnet-5` model perception extractions (`src/data/model_message_amendments.json`).

## 1. High-Level Summary

- **Total Messages in Dataset**: 215
- **Messages Producing Amendments (Deterministic)**: 109 (Total amendments: 127)
- **Messages Producing Amendments (Model)**: 121 (Total amendments: 139)
- **Both Empty (No Amendments)**: 93
- **Exact Matches (Identical Actions & Core Attributes)**: 85
- **Disagreements / Divergences**: 37
  - Emitted only by deterministic: 1
  - Emitted only by model: 13
  - Emitted by both but differing in action or parameters: 23

## 2. Action Breakdown and Agreements

| Action Type | Deterministic Count | Model Count | Exact Agreements |
|---|---|---|---|
| `ADD_CONFIRMED_INCOME` | 15 | 15 | 15 |
| `ADD_RECURRING_EXPENSE` | 8 | 8 | 8 |
| `AMEND_RECURRING_AMOUNT` | 32 | 37 | 22 |
| `CONFIRM_EVENT` | 14 | 13 | 13 |
| `ESTABLISH_SERIES` | 35 | 43 | 35 |
| `MARK_NON_RECURRING` | 3 | 3 | 3 |
| `TERMINATE_SERIES` | 20 | 20 | 7 |

## 3. Itemized Disagreements

The following sections document every disagreement for architectural review. The outputs are not merged.

### `message_08` (model_only)
**Verbatim Message Text:**
> Berikut informasi penggajian terbaru dari Greenfield Foods. Gaji pokok yang dikonfirmasi adalah IDR 38760000. Komisi dari transaksi yang masih berjalan belum disetujui. Transaksi yang masih berjalan tidak masuk pembayaran sampai komisinya dinyatakan diperoleh. Ref payroll EMP-0008.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 38760000,
    "currency": "IDR",
    "start_date": "2025-04-22",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 22,
    "source_substring": "Gaji pokok yang dikonfirmasi adalah IDR 38760000",
    "message_id": "message_08",
    "user_id": "user_11",
    "source_message_id": "message_08"
  }
]
```

---

### `message_09` (content_or_action_mismatch)
**Verbatim Message Text:**
> A note from Cobalt Systems about your upcoming pay. The current seasonal contract has ended. No off-season income or renewal has been confirmed. We’ll contact you separately if another shift block or contract is approved. Payroll ref EMP-0009.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_09",
    "user_id": "user_12",
    "source_substring": "The current seasonal contract has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-03-25",
    "source_substring": "The current seasonal contract has ended.",
    "message_id": "message_09",
    "user_id": "user_12",
    "source_message_id": "message_09"
  }
]
```

---

### `message_100` (model_only)
**Verbatim Message Text:**
> BrightPath Media payroll has posted a new update. Your temporary monthly pay is USD 2177.28. The reduced amount continues for the next payroll. This is the amount currently scheduled for the affected pay cycle. Payroll ref EMP-0100.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 2177.28,
    "effective_date": "2024-11-26",
    "source_substring": "Your temporary monthly pay is USD 2177.28.",
    "message_id": "message_100",
    "user_id": "user_130",
    "source_message_id": "message_100"
  }
]
```

---

### `message_103` (content_or_action_mismatch)
**Verbatim Message Text:**
> Rincian penggajian Anda di HarborWorks telah berubah. Kontrak musiman saat ini telah berakhir. Belum ada pendapatan di luar musim atau perpanjangan kontrak yang dikonfirmasi. Kami akan menghubungi Anda jika jadwal kerja atau kontrak berikutnya disetujui. Ref payroll EMP-0103.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_103",
    "user_id": "user_133",
    "source_substring": "Kontrak musiman saat ini telah berakhir"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2024-03-06",
    "source_substring": "Kontrak musiman saat ini telah berakhir",
    "message_id": "message_103",
    "user_id": "user_133",
    "source_message_id": "message_103"
  }
]
```

---

### `message_122` (model_only)
**Verbatim Message Text:**
> Ada pembaruan singkat dari tim payroll HarborWorks. Gaji bulanan sementara Anda adalah IDR 23940000. Jumlah yang lebih rendah masih berlaku untuk penggajian berikutnya. Inilah jumlah yang saat ini dijadwalkan untuk periode penggajian tersebut. Ref payroll EMP-0122.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 23940000,
    "effective_date": "2024-02-29",
    "source_substring": "Gaji bulanan sementara Anda adalah IDR 23940000",
    "message_id": "message_122",
    "user_id": "user_157",
    "source_message_id": "message_122"
  }
]
```

---

### `message_127` (model_only)
**Verbatim Message Text:**
> Greenfield Foods telah memperbarui catatan penggajian Anda. Gaji rutin Anda untuk penggajian berikutnya adalah IDR 30400000. Penggajian yang sama mencakup penyesuaian tunggakan satu kali sebesar IDR 13680000. Slip gaji berikutnya akan menampilkan gaji rutin dan penyesuaian satu kali secara terpisah. Ref payroll EMP-0127.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 30400000,
    "effective_date": "2024-09-02",
    "source_substring": "Gaji rutin Anda untuk penggajian berikutnya adalah IDR 30400000",
    "message_id": "message_127",
    "user_id": "user_163",
    "source_message_id": "message_127"
  }
]
```

---

### `message_129` (content_or_action_mismatch)
**Verbatim Message Text:**
> A note from Cedar Health about your upcoming pay. Your employment has ended. There are no regular salary payments scheduled after the final settlement. Details of any final settlement will be sent separately. Payroll ref EMP-0129.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_129",
    "user_id": "user_165",
    "source_substring": "Your employment has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-04-03",
    "source_substring": "Your employment has ended. There are no regular salary payments scheduled after the final settlement.",
    "message_id": "message_129",
    "user_id": "user_165",
    "source_message_id": "message_129"
  }
]
```

---

### `message_132` (content_or_action_mismatch)
**Verbatim Message Text:**
> A note from Greenfield Foods about your upcoming pay. Your next salary is reduced to INR 137150. The adjustment is due to approved unpaid leave. The adjustment will be visible on your next payslip. Payroll ref EMP-0132.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "source_message_id": "message_132",
    "message_id": "message_132",
    "user_id": "user_168",
    "series_key": "user_168_Payroll credit_INR",
    "new_amount": 137150.0,
    "effective_date": "2026-01-04",
    "source_substring": "Your next salary is reduced to INR 137150. The adjustment is due to approved unpaid leave."
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 137150,
    "effective_date": "2026-01-04",
    "source_substring": "Your next salary is reduced to INR 137150",
    "message_id": "message_132",
    "user_id": "user_168",
    "source_message_id": "message_132"
  }
]
```

---

### `message_137` (content_or_action_mismatch)
**Verbatim Message Text:**
> Hi, Greenfield Foods payroll here. Your salary of USD 1284 is confirmed for 2025-11-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0137.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": "1284",
    "effective_date": "2025-11-15",
    "message_id": "message_137",
    "user_id": "user_173"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 1284,
    "currency": "USD",
    "start_date": "2025-11-15",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 15,
    "source_substring": "Your salary of USD 1284 is confirmed for 2025-11-15",
    "message_id": "message_137",
    "user_id": "user_173",
    "source_message_id": "message_137"
  }
]
```

---

### `message_148` (content_or_action_mismatch)
**Verbatim Message Text:**
> Here’s the latest payroll information from HarborWorks. Your next salary is reduced to ZAR 31889. The adjustment is due to approved unpaid leave. The adjustment will be visible on your next payslip. Payroll ref EMP-0148.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "source_message_id": "message_148",
    "message_id": "message_148",
    "user_id": "user_186",
    "series_key": "user_186_Payroll credit_ZAR",
    "new_amount": 31889.0,
    "effective_date": "2025-12-29",
    "source_substring": "Your next salary is reduced to ZAR 31889. The adjustment is due to approved unpaid leave."
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 31889,
    "effective_date": "2025-12-29",
    "source_substring": "Your next salary is reduced to ZAR 31889. The adjustment is due to approved unpaid leave.",
    "message_id": "message_148",
    "user_id": "user_186",
    "source_message_id": "message_148"
  }
]
```

---

### `message_160` (content_or_action_mismatch)
**Verbatim Message Text:**
> Tim payroll Northstar Labs telah mengirim pembaruan. Kontrak musiman saat ini telah berakhir. Belum ada pendapatan di luar musim atau perpanjangan kontrak yang dikonfirmasi. Kami akan menghubungi Anda jika jadwal kerja atau kontrak berikutnya disetujui. Ref payroll EMP-0160.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_160",
    "user_id": "user_201",
    "source_substring": "Kontrak musiman saat ini telah berakhir"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-03-26",
    "source_substring": "Kontrak musiman saat ini telah berakhir",
    "message_id": "message_160",
    "user_id": "user_201",
    "source_message_id": "message_160"
  }
]
```

---

### `message_166` (content_or_action_mismatch)
**Verbatim Message Text:**
> HarborWorks payroll has posted a new update. The current seasonal contract has ended. No off-season income or renewal has been confirmed. We’ll contact you separately if another shift block or contract is approved. Payroll ref EMP-0166.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_166",
    "user_id": "user_213",
    "source_substring": "The current seasonal contract has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2025-12-30",
    "source_substring": "The current seasonal contract has ended.",
    "message_id": "message_166",
    "user_id": "user_213",
    "source_message_id": "message_166"
  }
]
```

---

### `message_176` (model_only)
**Verbatim Message Text:**
> Greenfield Foods has updated your payroll record. Your regular salary for the next payroll is INR 260000. The same payroll includes a one-time arrears adjustment of INR 117000. Your next payslip will show the regular pay and any one-off adjustment separately. Payroll ref EMP-0176.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 260000,
    "effective_date": "2024-11-25",
    "source_substring": "Your regular salary for the next payroll is INR 260000",
    "message_id": "message_176",
    "user_id": "user_226",
    "source_message_id": "message_176"
  }
]
```

---

### `message_186` (content_or_action_mismatch)
**Verbatim Message Text:**
> Ada pembaruan singkat dari tim payroll BrightPath Media. Kontrak musiman saat ini telah berakhir. Belum ada pendapatan di luar musim atau perpanjangan kontrak yang dikonfirmasi. Kami akan menghubungi Anda jika jadwal kerja atau kontrak berikutnya disetujui. Ref payroll EMP-0186.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_186",
    "user_id": "user_237",
    "source_substring": "Kontrak musiman saat ini telah berakhir"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-03-26",
    "source_substring": "Kontrak musiman saat ini telah berakhir",
    "message_id": "message_186",
    "user_id": "user_237",
    "source_message_id": "message_186"
  }
]
```

---

### `message_189` (content_or_action_mismatch)
**Verbatim Message Text:**
> Riverline Retail telah memperbarui catatan penggajian Anda. Kontrak musiman saat ini telah berakhir. Belum ada pendapatan di luar musim atau perpanjangan kontrak yang dikonfirmasi. Kami akan menghubungi Anda jika jadwal kerja atau kontrak berikutnya disetujui. Ref payroll EMP-0189.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_189",
    "user_id": "user_241",
    "source_substring": "Kontrak musiman saat ini telah berakhir"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2024-02-29",
    "source_substring": "Kontrak musiman saat ini telah berakhir",
    "message_id": "message_189",
    "user_id": "user_241",
    "source_message_id": "message_189"
  }
]
```

---

### `message_191` (content_or_action_mismatch)
**Verbatim Message Text:**
> A quick update from the payroll team at Cedar Health. Your salary of USD 1680 is confirmed for 2025-11-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0191.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": "1680",
    "effective_date": "2025-11-15",
    "message_id": "message_191",
    "user_id": "user_245"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 1680,
    "currency": "USD",
    "start_date": "2025-11-15",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 15,
    "source_substring": "Your salary of USD 1680 is confirmed for 2025-11-15.",
    "message_id": "message_191",
    "user_id": "user_245",
    "source_message_id": "message_191"
  }
]
```

---

### `message_192` (content_or_action_mismatch)
**Verbatim Message Text:**
> Here’s the latest payroll information from Cedar Health. Your employment has ended. There are no regular salary payments scheduled after the final settlement. Details of any final settlement will be sent separately. Payroll ref EMP-0192.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_192",
    "user_id": "user_246",
    "source_substring": "Your employment has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-03-24",
    "source_substring": "Your employment has ended. There are no regular salary payments scheduled after the final settlement.",
    "message_id": "message_192",
    "user_id": "user_246",
    "source_message_id": "message_192"
  }
]
```

---

### `message_193` (model_only)
**Verbatim Message Text:**
> Northstar Labs payroll has posted a new update. Your temporary monthly pay is EUR 1528.56. The reduced amount continues for the next payroll. This is the amount currently scheduled for the affected pay cycle. Payroll ref EMP-0193.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 1528.56,
    "effective_date": "2024-08-30",
    "source_substring": "Your temporary monthly pay is EUR 1528.56.",
    "message_id": "message_193",
    "user_id": "user_247",
    "source_message_id": "message_193"
  }
]
```

---

### `message_195` (content_or_action_mismatch)
**Verbatim Message Text:**
> Here’s the latest payroll information from Greenfield Foods. Your next salary is reduced to USD 702. The adjustment is due to approved unpaid leave. The adjustment will be visible on your next payslip. Payroll ref EMP-0195.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "source_message_id": "message_195",
    "message_id": "message_195",
    "user_id": "user_249",
    "series_key": "user_249_Payroll credit_USD",
    "new_amount": 702.0,
    "effective_date": "2025-12-27",
    "source_substring": "Your next salary is reduced to USD 702. The adjustment is due to approved unpaid leave."
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 702,
    "effective_date": "2025-12-27",
    "source_substring": "Your next salary is reduced to USD 702.",
    "message_id": "message_195",
    "user_id": "user_249",
    "source_message_id": "message_195"
  }
]
```

---

### `message_204` (content_or_action_mismatch)
**Verbatim Message Text:**
> Your payroll details at Riverline Retail have changed. Your salary of EUR 1485 is confirmed for 2025-05-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0204.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": "1485",
    "effective_date": "2025-05-15",
    "message_id": "message_204",
    "user_id": "user_263"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 1485,
    "currency": "EUR",
    "start_date": "2025-05-15",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 15,
    "source_substring": "Your salary of EUR 1485 is confirmed for 2025-05-15.",
    "message_id": "message_204",
    "user_id": "user_263",
    "source_message_id": "message_204"
  }
]
```

---

### `message_206` (content_or_action_mismatch)
**Verbatim Message Text:**
> A note from Greenfield Foods about your upcoming pay. The current seasonal contract has ended. No off-season income or renewal has been confirmed. We’ll contact you separately if another shift block or contract is approved. Payroll ref EMP-0206.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_206",
    "user_id": "user_265",
    "source_substring": "The current seasonal contract has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2024-02-28",
    "source_substring": "The current seasonal contract has ended.",
    "message_id": "message_206",
    "user_id": "user_265",
    "source_message_id": "message_206"
  }
]
```

---

### `message_21` (content_or_action_mismatch)
**Verbatim Message Text:**
> Here’s the latest payroll information from Riverline Retail. The current seasonal contract has ended. No off-season income or renewal has been confirmed. We’ll contact you separately if another shift block or contract is approved. Payroll ref EMP-0021.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_21",
    "user_id": "user_29",
    "source_substring": "The current seasonal contract has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2025-10-27",
    "source_substring": "The current seasonal contract has ended.",
    "message_id": "message_21",
    "user_id": "user_29",
    "source_message_id": "message_21"
  }
]
```

---

### `message_27` (model_only)
**Verbatim Message Text:**
> Cedar Health telah memperbarui catatan penggajian Anda. Gaji rutin Anda untuk penggajian berikutnya adalah IDR 21090000. Penggajian yang sama mencakup penyesuaian tunggakan satu kali sebesar IDR 9490500. Slip gaji berikutnya akan menampilkan gaji rutin dan penyesuaian satu kali secara terpisah. Ref payroll EMP-0027.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 21090000,
    "effective_date": "2024-03-01",
    "source_substring": "Gaji rutin Anda untuk penggajian berikutnya adalah IDR 21090000",
    "message_id": "message_27",
    "user_id": "user_37",
    "source_message_id": "message_27"
  }
]
```

---

### `message_36` (model_only)
**Verbatim Message Text:**
> Rincian penggajian Anda di Greenfield Foods telah berubah. Gaji bulanan sementara Anda adalah IDR 31464000. Jumlah yang lebih rendah masih berlaku untuk penggajian berikutnya. Inilah jumlah yang saat ini dijadwalkan untuk periode penggajian tersebut. Ref payroll EMP-0036.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 31464000,
    "effective_date": "2024-02-21",
    "source_substring": "Gaji bulanan sementara Anda adalah IDR 31464000",
    "message_id": "message_36",
    "user_id": "user_49",
    "source_message_id": "message_36"
  }
]
```

---

### `message_45` (content_or_action_mismatch)
**Verbatim Message Text:**
> Greenfield Foods has updated your payroll record. The current seasonal contract has ended. No off-season income or renewal has been confirmed. We’ll contact you separately if another shift block or contract is approved. Payroll ref EMP-0045.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_45",
    "user_id": "user_61",
    "source_substring": "The current seasonal contract has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2024-02-28",
    "source_substring": "The current seasonal contract has ended.",
    "message_id": "message_45",
    "user_id": "user_61",
    "source_message_id": "message_45"
  }
]
```

---

### `message_53` (content_or_action_mismatch)
**Verbatim Message Text:**
> Greenfield Foods telah memperbarui catatan penggajian Anda. Gaji sebesar USD 696 dikonfirmasi untuk 2025-05-15. Bank penerima akan mengonversinya dengan kurs pada tanggal penyelesaian. Jumlah yang diterima dalam mata uang utama bergantung pada kurs tanggal penyelesaian. Ref payroll EMP-0053.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": "696",
    "effective_date": "2025-05-15",
    "message_id": "message_53",
    "user_id": "user_71"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 696,
    "currency": "USD",
    "start_date": "2025-05-15",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 15,
    "source_substring": "Gaji sebesar USD 696 dikonfirmasi untuk 2025-05-15",
    "message_id": "message_53",
    "user_id": "user_71",
    "source_message_id": "message_53"
  }
]
```

---

### `message_57` (content_or_action_mismatch)
**Verbatim Message Text:**
> A quick update from the payroll team at Northstar Labs. Your employment has ended. There are no regular salary payments scheduled after the final settlement. Details of any final settlement will be sent separately. Payroll ref EMP-0057.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_57",
    "user_id": "user_75",
    "source_substring": "Your employment has ended"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-04-04",
    "source_substring": "Your employment has ended. There are no regular salary payments scheduled after the final settlement.",
    "message_id": "message_57",
    "user_id": "user_75",
    "source_message_id": "message_57"
  }
]
```

---

### `message_62` (model_only)
**Verbatim Message Text:**
> Hi, Cedar Health payroll here. Your regular salary for the next payroll is USD 1752. The same payroll includes a one-time arrears adjustment of USD 788.40. Your next payslip will show the regular pay and any one-off adjustment separately. Payroll ref EMP-0062.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 1752,
    "effective_date": "2024-11-26",
    "source_substring": "Your regular salary for the next payroll is USD 1752",
    "message_id": "message_62",
    "user_id": "user_82",
    "source_message_id": "message_62"
  }
]
```

---

### `message_64` (deterministic_only)
**Verbatim Message Text:**
> BuyBox confirmed that the tote bag order was paid in INR on 3 April 2026. The receipt has the final amount. Order ref MER-0064.

**Deterministic Output:**
```json
[
  {
    "action": "CONFIRM_EVENT",
    "event_id": "event_7941",
    "message_id": "message_64",
    "user_id": "user_84"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[]
```

---

### `message_65` (model_only)
**Verbatim Message Text:**
> Halo, ini tim payroll BrightPath Media. Gaji bulanan sementara Anda adalah IDR 8618400. Jumlah yang lebih rendah masih berlaku untuk penggajian berikutnya. Inilah jumlah yang saat ini dijadwalkan untuk periode penggajian tersebut. Ref payroll EMP-0065.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 8618400,
    "effective_date": "2024-02-27",
    "source_substring": "Gaji bulanan sementara Anda adalah IDR 8618400",
    "message_id": "message_65",
    "user_id": "user_85",
    "source_message_id": "message_65"
  }
]
```

---

### `message_74` (content_or_action_mismatch)
**Verbatim Message Text:**
> Greenfield Foods payroll has posted a new update. Your salary of EUR 1804 is confirmed for 2025-08-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0074.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": "1804",
    "effective_date": "2025-08-15",
    "message_id": "message_74",
    "user_id": "user_98"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 1804,
    "currency": "EUR",
    "start_date": "2025-08-15",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 15,
    "source_substring": "Your salary of EUR 1804 is confirmed for 2025-08-15.",
    "message_id": "message_74",
    "user_id": "user_98",
    "source_message_id": "message_74"
  }
]
```

---

### `message_77` (model_only)
**Verbatim Message Text:**
> Cobalt Systems has updated your payroll record. Your temporary monthly pay is INR 164880. The reduced amount continues for the next payroll. This is the amount currently scheduled for the affected pay cycle. Payroll ref EMP-0077.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 164880,
    "effective_date": "2024-09-05",
    "source_substring": "Your temporary monthly pay is INR 164880.",
    "message_id": "message_77",
    "user_id": "user_103",
    "source_message_id": "message_77"
  }
]
```

---

### `message_82` (model_only)
**Verbatim Message Text:**
> Your payroll details at Riverline Retail have changed. Your confirmed base salary is ZAR 33440. The commission shown for open deals is still pending approval. Open deals will stay out of the payout until the commission is marked as earned. Payroll ref EMP-0082.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 33440,
    "effective_date": "2026-06-28",
    "source_substring": "Your confirmed base salary is ZAR 33440.",
    "message_id": "message_82",
    "user_id": "user_108",
    "source_message_id": "message_82"
  }
]
```

---

### `message_84` (content_or_action_mismatch)
**Verbatim Message Text:**
> Ada informasi baru dari HarborWorks tentang gaji Anda. Hubungan kerja Anda telah berakhir. Tidak ada pembayaran gaji rutin yang dijadwalkan setelah penyelesaian akhir. Rincian penyelesaian akhir akan dikirim secara terpisah. Ref payroll EMP-0084.

**Deterministic Output:**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-12-31",
    "message_id": "message_84",
    "user_id": "user_111",
    "source_substring": "Hubungan kerja Anda telah berakhir"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "TERMINATE_SERIES",
    "series_key": "salary",
    "final_date": "2026-04-01",
    "source_substring": "Tidak ada pembayaran gaji rutin yang dijadwalkan setelah penyelesaian akhir",
    "message_id": "message_84",
    "user_id": "user_111",
    "source_message_id": "message_84"
  }
]
```

---

### `message_86` (model_only)
**Verbatim Message Text:**
> MoneyHub account update: Your wallet was charged for the session at Charge Point 1110 in Krishnagiri on 3 September 2026 at 12:35 a.m. The receipt contains the final INR amount. Your employer has confirmed a USD 1296 salary credit for 15 September 2026. The salary will use the exchange rate when it settles. Account ref FIN-0086.

**Deterministic Output:**
```json
[]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 1296,
    "currency": "USD",
    "start_date": "2026-09-15",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 15,
    "source_substring": "Your employer has confirmed a USD 1296 salary credit for 15 September 2026.",
    "message_id": "message_86",
    "user_id": "user_113",
    "source_message_id": "message_86"
  }
]
```

---

### `message_87` (content_or_action_mismatch)
**Verbatim Message Text:**
> Riverline Retail payroll has posted a new update. Your next salary is reduced to INR 148200. The adjustment is due to approved unpaid leave. The adjustment will be visible on your next payslip. Payroll ref EMP-0087.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "source_message_id": "message_87",
    "message_id": "message_87",
    "user_id": "user_114",
    "series_key": "user_114_Payroll credit_INR",
    "new_amount": 148200.0,
    "effective_date": "2025-12-30",
    "source_substring": "Your next salary is reduced to INR 148200. The adjustment is due to approved unpaid leave."
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": 148200,
    "effective_date": "2025-12-30",
    "source_substring": "Your next salary is reduced to INR 148200",
    "message_id": "message_87",
    "user_id": "user_114",
    "source_message_id": "message_87"
  }
]
```

---

### `message_95` (content_or_action_mismatch)
**Verbatim Message Text:**
> A quick update from the payroll team at Greenfield Foods. Your salary of EUR 748 is confirmed for 2025-11-15. The receiving bank will convert it using the rate applied on the settlement date. The amount received in your home currency will depend on the settlement-date conversion. Payroll ref EMP-0095.

**Deterministic Output:**
```json
[
  {
    "action": "AMEND_RECURRING_AMOUNT",
    "series_key": "salary",
    "new_amount": "748",
    "effective_date": "2025-11-15",
    "message_id": "message_95",
    "user_id": "user_125"
  }
]
```

**Model Output (`claude-sonnet-5`):**
```json
[
  {
    "action": "ESTABLISH_SERIES",
    "amount": 748,
    "currency": "EUR",
    "start_date": "2025-11-15",
    "series_key": "salary",
    "category": "salary",
    "description": "New employer payroll",
    "cadence_day": 15,
    "source_substring": "Your salary of EUR 748 is confirmed for 2025-11-15.",
    "message_id": "message_95",
    "user_id": "user_125",
    "source_message_id": "message_95"
  }
]
```

---
