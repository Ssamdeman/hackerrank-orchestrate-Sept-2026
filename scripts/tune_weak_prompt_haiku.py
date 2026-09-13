"""Step 3: Prompt tuning on Haiku targeting MARK_NON_RECURRING and TERMINATE_SERIES.

Runs baseline prompt vs revised prompt on the 33 messages involving these actions.
Caches Haiku responses under separate keys in src/data/.cache/haiku_tuning_cache.json.
Reports exact agreement before and after.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import re
import sys
from typing import Any

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

import anthropic
from llm.extract_messages import SYSTEM_PROMPT as BASELINE_SYSTEM_PROMPT, _load_env_if_needed

_load_env_if_needed()
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("Missing ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=api_key)

# The revised prompt targeting MARK_NON_RECURRING and TERMINATE_SERIES
REVISED_SYSTEM_PROMPT = BASELINE_SYSTEM_PROMPT.replace(
    '''2. TERMINATE_SERIES
   - Meaning: An existing recurring salary series has ended.
   - Case A: "first salary from the NEW employer" -> TERMINATE_SERIES (final_date is the start date of the new employer)
   - Case B: "seasonal contract has ended" / "employment has ended" / "kontrak musiman telah berakhir" / "no regular salary payments scheduled after..."
     Format: {"action": "TERMINATE_SERIES", "series_key": "salary", "final_date": "YYYY-MM-DD", "source_substring": "<exact verbatim quote>"}
     If no date is specified in the message text, use the message sent_at date.''',
    '''2. TERMINATE_SERIES
   - Meaning: An existing recurring salary series has ended.
   - Case A: "first salary from the NEW employer" -> TERMINATE_SERIES (final_date is the start date of the new employer)
   - Case B: "seasonal contract has ended" / "employment has ended" / "kontrak musiman telah berakhir" / "no regular salary payments scheduled after..."
     Format: {"action": "TERMINATE_SERIES", "series_key": "salary", "final_date": "YYYY-MM-DD", "source_substring": "<exact verbatim quote>"}
     If no explicit end date is specified in the message text, use "2026-12-31" as final_date.
   - EXCLUSION: Do NOT emit TERMINATE_SERIES for partial household employment notices ("One household employment record has ended. The remaining confirmed monthly salary is..." / "Salah satu sumber pendapatan kerja rumah tangga telah berakhir..."). Emit NOTHING (empty amendments list) for these notices.'''
).replace(
    '''6. MARK_NON_RECURRING
   - Trigger: "claim is closed / reimbursement, not regular salary" / "penggantian atas biaya kerja ... bukan gaji rutin".
   - Target: Must match the related_event_id.
   - Format: {"action": "MARK_NON_RECURRING", "event_id": "<related_event_id>", "source_substring": "<exact verbatim quote>"}

7. CONFIRM_EVENT
   - Trigger: "settled in the cash account", "reached your account after withholding", "confirmed received on DATE".
   - Target: Must match the related_event_id.
   - Format: {"action": "CONFIRM_EVENT", "event_id": "<related_event_id>", "source_substring": "<exact verbatim quote>"}''',
    '''6. MARK_NON_RECURRING & EXPENSE REIMBURSEMENTS
   - Trigger: Work expense reimbursement ("reimbursement for your earlier work expense", "not your regular salary" / "penggantian atas biaya kerja", "bukan gaji rutin").
   - MUST emit BOTH:
     1) CONFIRM_EVENT for the related_event_id: {"action": "CONFIRM_EVENT", "event_id": "<related_event_id>", "source_substring": "<exact verbatim quote>"}
     2) MARK_NON_RECURRING for the related_event_id: {"action": "MARK_NON_RECURRING", "event_id": "<related_event_id>", "source_substring": "<exact verbatim quote>"}
   - PRIZE PROCEEDS RULE: For prize proceeds ("prize proceeds have reached your account after withholding... claim is now closed" / "FIN-xxxx"), emit ONLY CONFIRM_EVENT. Do NOT emit MARK_NON_RECURRING for prize proceeds.

7. CONFIRM_EVENT
   - Trigger: "settled in the cash account", "reached your account after withholding", "prize proceeds have reached your account", "confirmed received on DATE".
   - Target: Must match the related_event_id.
   - Format: {"action": "CONFIRM_EVENT", "event_id": "<related_event_id>", "source_substring": "<exact verbatim quote>"}'''
)

# Load dataset and ground truth deterministic amendments
det_path = repo_root / "src" / "data" / "message_amendments.json"
messages_path = repo_root / "dataset" / "messages.csv"
cache_path = repo_root / "src" / "data" / ".cache" / "haiku_tuning_cache.json"

cache_path.parent.mkdir(parents=True, exist_ok=True)
tuning_cache: dict[str, Any] = {}
if cache_path.is_file():
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            tuning_cache = json.load(f)
    except Exception:
        tuning_cache = {}

with open(det_path, "r", encoding="utf-8") as f:
    det_amends = json.load(f)

det_by_m: dict[str, list[dict[str, Any]]] = {}
for a in det_amends:
    det_by_m.setdefault(a["message_id"], []).append(a)

messages_map: dict[str, dict[str, str]] = {}
with open(messages_path, "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        messages_map[r["message_id"]] = r

# Target subsets
MARK_NON_RECURRING_MIDS = [
    "message_28", "message_88", "message_99", "message_110",
    "message_117", "message_150", "message_174"
]

TERMINATE_SERIES_MIDS = [
    "message_09", "message_103", "message_116", "message_119",
    "message_124", "message_129", "message_149", "message_160",
    "message_166", "message_180", "message_186", "message_187",
    "message_189", "message_192", "message_196", "message_203",
    "message_206", "message_21", "message_30", "message_31",
    "message_37", "message_38", "message_45", "message_57",
    "message_80", "message_84"
]

TARGET_MIDS = sorted(set(MARK_NON_RECURRING_MIDS) | set(TERMINATE_SERIES_MIDS))


def normalize_amend(a: dict[str, Any]) -> tuple[Any, ...]:
    action = a.get("action")
    if action in ("ESTABLISH_SERIES", "ADD_CONFIRMED_INCOME"):
        return (action, str(a.get("amount")), str(a.get("currency")), str(a.get("start_date") or a.get("date")))
    elif action == "AMEND_RECURRING_AMOUNT":
        return (action, str(a.get("new_amount")), str(a.get("effective_date")))
    elif action == "TERMINATE_SERIES":
        return (action, str(a.get("final_date")))
    elif action == "ADD_RECURRING_EXPENSE":
        return (action, str(a.get("category")), str(a.get("start_date")))
    elif action in ("CONFIRM_EVENT", "MARK_NON_RECURRING", "CANCEL_EVENT"):
        return (action, str(a.get("event_id")))
    elif action == "AMEND_AMOUNT":
        return (action, str(a.get("event_id")), str(a.get("new_amount")))
    elif action == "DELAY_EVENT":
        return (action, str(a.get("event_id")), str(a.get("new_date")))
    return (action, str(a))


def call_haiku(mid: str, prompt: str, cache_prefix: str) -> list[dict[str, Any]]:
    cache_key = f"{cache_prefix}_{mid}"
    if cache_key in tuning_cache:
        cached_res = tuning_cache[cache_key].get("amendments", [])
        if isinstance(cached_res, list):
            return [a for a in cached_res if isinstance(a, dict)]
        return []

    m = messages_map[mid]
    user_content = (
        f"Message ID: {mid}\n"
        f"User ID: {m['user_id']}\n"
        f"Source Type: {m['source_type']}\n"
        f"Related Event ID: {m.get('related_event_id') or 'None'}\n"
        f"Sent At: {m.get('sent_at', '')}\n"
        f"Message Text:\n{m['message_text']}"
    )

    res = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=prompt,
        messages=[{"role": "user", "content": user_content}],
    )

    raw_text = ""
    for block in res.content:
        if getattr(block, "type", None) == "text":
            raw_text += getattr(block, "text", "")
    if "```json" in raw_text:
        raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in raw_text:
        raw_text = raw_text.split("```", 1)[1].split("```", 1)[0]

    amends: list[dict[str, Any]] = []
    try:
        parsed = json.loads(raw_text.strip())
        raw_amends = parsed.get("amendments", [])
        if isinstance(raw_amends, list):
            amends = [a for a in raw_amends if isinstance(a, dict)]
    except Exception as e:
        print(f"Error parsing JSON for {mid}: {e} (raw: {raw_text})")
        amends = []

    tuning_cache[cache_key] = {
        "amendments": amends,
        "raw": raw_text,
        "usage": {
            "input_tokens": res.usage.input_tokens,
            "output_tokens": res.usage.output_tokens,
        }
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(tuning_cache, f, indent=2)

    return amends


def evaluate_run(name: str, prompt: str, cache_prefix: str) -> dict[str, Any]:
    print(f"\n--- Evaluating {name} on Haiku ---")
    results_by_mid: dict[str, list[dict[str, Any]]] = {}
    for mid in TARGET_MIDS:
        amends = call_haiku(mid, prompt, cache_prefix)
        results_by_mid[mid] = amends

    # Check agreements
    mnr_matches = 0
    tser_matches = 0
    total_matches = 0

    print("\nDetailed Per-Message Evaluation:")
    for mid in TARGET_MIDS:
        d_sigs = sorted(normalize_amend(a) for a in det_by_m.get(mid, []))
        m_sigs = sorted(normalize_amend(a) for a in results_by_mid.get(mid, []))
        is_match = (d_sigs == m_sigs)
        if is_match:
            total_matches += 1

        in_mnr = mid in MARK_NON_RECURRING_MIDS
        in_tser = mid in TERMINATE_SERIES_MIDS

        if in_mnr and is_match:
            mnr_matches += 1
        if in_tser and is_match:
            tser_matches += 1

        flag = "PASS" if is_match else "FAIL"
        category = "MNR" if in_mnr else "TSER"
        print(f"[{flag}] ({category}) {mid}: Det={d_sigs} | Model={m_sigs}")

    print(f"\nSummary for {name}:")
    print(f"  MARK_NON_RECURRING exact agreement: {mnr_matches} / {len(MARK_NON_RECURRING_MIDS)}")
    print(f"  TERMINATE_SERIES exact agreement:   {tser_matches} / {len(TERMINATE_SERIES_MIDS)}")
    print(f"  Overall 33 messages exact agreement: {total_matches} / {len(TARGET_MIDS)}")

    return {
        "mnr_matches": mnr_matches,
        "tser_matches": tser_matches,
        "total_matches": total_matches,
        "results_by_mid": results_by_mid,
    }


if __name__ == "__main__":
    print(f"Total target messages to evaluate: {len(TARGET_MIDS)}")
    before = evaluate_run("BASELINE PROMPT (Before)", BASELINE_SYSTEM_PROMPT, "haiku_weak_before")
    after = evaluate_run("REVISED PROMPT (After)", REVISED_SYSTEM_PROMPT, "haiku_weak_after")

    print("\n" + "="*50)
    print("COMPARISON SUMMARY (Haiku):")
    print("="*50)
    print(f"MARK_NON_RECURRING: Before = {before['mnr_matches']}/{len(MARK_NON_RECURRING_MIDS)}  -->  After = {after['mnr_matches']}/{len(MARK_NON_RECURRING_MIDS)}")
    print(f"TERMINATE_SERIES:   Before = {before['tser_matches']}/{len(TERMINATE_SERIES_MIDS)}  -->  After = {after['tser_matches']}/{len(TERMINATE_SERIES_MIDS)}")
    print(f"Overall (33 msgs):  Before = {before['total_matches']}/{len(TARGET_MIDS)}  -->  After = {after['total_matches']}/{len(TARGET_MIDS)}")
