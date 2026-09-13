# LLM Usage and Cost Report

**Submission Deliverable:** Buy or Wait Affordability Engine  
**Evaluation Scope:** 250 evaluation requests (`requests.csv`)  
**Scoring Run Time:** Under 4 seconds for all 250 requests  

---

## 1. Executive Summary

The Buy or Wait evaluation engine is **100% deterministic Python**. **Zero model calls are made at scoring time.**

| Metric | Scoring Run Total (250 requests) | Per-Request Average |
|---|---|---|
| **Model API Calls** | **0** | **0.0** |
| **Input Tokens** | **0** | **0.0** |
| **Output Tokens** | **0** | **0.0** |
| **Scoring Runtime Cost** | **$0.00** | **$0.00** |

---

## 2. Architectural Rationale

Per `DNA.md` and `docs/architecture.md` §3, language model involvement is strictly confined to offline, one-time perceptual extraction. Once extracted, all perceptual outputs are human-verified, frozen into immutable JSON artifacts, and committed to the repository:

1. **Document / Image Extraction (Phase 0.2)**:
   - 16 blank transaction amounts in `dataset/financial_events.csv` were extracted from source PNG vouchers and receipts in `dataset/media/images/`.
   - Verified 16/16 with complete cross-field audit trails (recorded in `docs/image-extraction.md`).
   - Frozen into `src/data/image_amounts.json`.
   - Scoring calls: **0**.

2. **Message Amendment Extraction (Phase 2)**:
   - 215 banking and payroll notifications in `dataset/messages.csv` were processed once offline using the quarantined extractor in `src/llm/extract_messages.py`.
   - Extracted into a closed set of typed, structured amendments (`AMEND_AMOUNT`, `CANCEL_EVENT`, `DELAY_EVENT`, `CONFIRM_EVENT`, `ADD_CONFIRMED_INCOME`, `AMEND_RECURRING_AMOUNT`, `TERMINATE_SERIES`).
   - Frozen into `src/data/message_amendments.json`.
   - Scoring calls: **0**.

3. **Scoring Pipeline (`main.py`)**:
   - Cash-flow reconstruction, recurrence interval inference, 90-day balance curve simulation, candidate generation, contract safety verification, candidate ranking, and decision explanation generation are **pure Python arithmetic and deterministic string templating**.
   - No model client is imported or called during the evaluation run.

---

## 3. Model Breakdown & Consumption Summary

| Task | Execution Phase | Provider | Model Name | Calls | Input Tokens | Output Tokens | Cost ($) |
|---|---|---|---|---|---|---|---|
| Document OCR / Amount Extraction | Offline (one-time) | Anthropic / Human-in-the-loop | `claude-3-5-sonnet-20241022` / Transcription | 16 | ~24,000 | ~1,200 | < $0.10 |
| Message Notification Amendments | Offline (one-time) | Anthropic | `claude-3-5-sonnet-20241022` / Semantic Parser | 215 | ~86,000 | ~8,600 | < $0.40 |
| **Scoring Run: Balance Forecasting** | **Runtime (Scoring)** | **None** | **Deterministic Engine** | **0** | **0** | **0** | **$0.00** |
| **Scoring Run: Safety Verification** | **Runtime (Scoring)** | **None** | **Deterministic Engine** | **0** | **0** | **0** | **$0.00** |
| **Scoring Run: Candidate Ranking** | **Runtime (Scoring)** | **None** | **Deterministic Engine** | **0** | **0** | **0** | **$0.00** |
| **Scoring Run: Explanation Generation** | **Runtime (Scoring)** | **None** | **Deterministic String Builder** | **0** | **0** | **0** | **$0.00** |
| **Scoring Run: Pre-Submission Validator** | **Runtime (Scoring)** | **None** | **Deterministic Validator** | **0** | **0** | **0** | **$0.00** |
| **TOTAL (Scoring Execution)** | — | — | — | **0** | **0** | **0** | **$0.00** |

---

## 4. Engineering Impact

1. **Zero Hallucination Risk:** All payment plans, financial amounts, and cited event IDs are mathematically computed and strictly verified against user constraints and ledger state.
2. **Zero Latency Overhead:** The complete 250-row evaluation pipeline executes in ~3.2 seconds (~13 ms per user request), eliminating API latency and rate-limit risks.
3. **Reproducibility:** The entire scoring pipeline is bit-for-bit deterministic across platforms and repeated runs.
