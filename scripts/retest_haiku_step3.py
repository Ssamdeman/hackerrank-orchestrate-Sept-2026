"""Step 3 re-test: evaluate revised prompt on Haiku for the 33 messages + household checks."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import sys
from typing import Any

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "src"))

import anthropic
from llm.extract_messages import SYSTEM_PROMPT, _load_env_if_needed

_load_env_if_needed()
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise RuntimeError("Missing ANTHROPIC_API_KEY")

client = anthropic.Anthropic(api_key=api_key)

det_path = repo_root / "src" / "data" / "message_amendments.json"
messages_path = repo_root / "dataset" / "messages.csv"
cache_path = repo_root / "src" / "data" / ".cache" / "haiku_tuning_cache.json"

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

MARK_NON_RECURRING_MIDS = [
    "message_28", "message_88", "message_99", "message_110",
    "message_117", "message_150", "message_174"
]

# True contract termination messages (20 messages from deterministic baseline)
TERMINATE_SERIES_DET_MIDS = [
    "message_09", "message_103", "message_116", "message_124", "message_129",
    "message_149", "message_160", "message_166", "message_186", "message_189",
    "message_192", "message_196", "message_206", "message_21", "message_31",
    "message_38", "message_45", "message_57", "message_80", "message_84"
]

HOUSEHOLD_MIDS = [
    "message_30", "message_37", "message_42",
    "message_119", "message_180", "message_187", "message_203"
]

EVAL_MIDS = sorted(set(MARK_NON_RECURRING_MIDS) | set(TERMINATE_SERIES_DET_MIDS) | set(HOUSEHOLD_MIDS))


def normalize_amend(a: dict[str, Any]) -> tuple[Any, ...]:
    action = a.get("action")
    if action in ("ESTABLISH_SERIES", "ADD_CONFIRMED_INCOME"):
        return (action, str(a.get("amount")), str(a.get("currency")), str(a.get("start_date") or a.get("date")))
    elif action == "AMEND_RECURRING_AMOUNT":
        return (action, str(a.get("new_amount")), str(a.get("effective_date")))
    elif action == "TERMINATE_SERIES":
        # Check action and series_key; final_date is not used by engine
        return (action, str(a.get("series_key", "salary")))
    elif action == "ADD_RECURRING_EXPENSE":
        return (action, str(a.get("category")), str(a.get("start_date")))
    elif action in ("CONFIRM_EVENT", "MARK_NON_RECURRING", "CANCEL_EVENT"):
        return (action, str(a.get("event_id")))
    elif action == "AMEND_AMOUNT":
        return (action, str(a.get("event_id")), str(a.get("new_amount")))
    elif action == "DELAY_EVENT":
        return (action, str(a.get("event_id")), str(a.get("new_date")))
    return (action, str(a))


def call_haiku(mid: str, cache_prefix: str) -> list[dict[str, Any]]:
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
        max_tokens=1024,
        system=SYSTEM_PROMPT,
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
        print(f"Error parsing JSON for {mid}: {e}")
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


if __name__ == "__main__":
    print(f"Running Haiku evaluation across {len(EVAL_MIDS)} messages...")
    results: dict[str, list[dict[str, Any]]] = {}
    for mid in EVAL_MIDS:
        results[mid] = call_haiku(mid, "haiku_tuned_step3")

    # 1. MARK_NON_RECURRING agreement
    mnr_matches = 0
    print("\n--- MARK_NON_RECURRING (7 messages) ---")
    for mid in MARK_NON_RECURRING_MIDS:
        d_sigs = sorted(normalize_amend(a) for a in det_by_m.get(mid, []))
        m_sigs = sorted(normalize_amend(a) for a in results.get(mid, []))
        is_match = (d_sigs == m_sigs)
        if is_match:
            mnr_matches += 1
        flag = "PASS" if is_match else "FAIL"
        print(f"[{flag}] {mid}: Det={d_sigs} | Model={m_sigs}")

    # 2. TERMINATE_SERIES agreement
    tser_matches = 0
    print("\n--- TERMINATE_SERIES (20 messages from deterministic baseline) ---")
    for mid in TERMINATE_SERIES_DET_MIDS:
        d_sigs = sorted(normalize_amend(a) for a in det_by_m.get(mid, []))
        m_sigs = sorted(normalize_amend(a) for a in results.get(mid, []))
        is_match = (d_sigs == m_sigs)
        if is_match:
            tser_matches += 1
        flag = "PASS" if is_match else "FAIL"
        print(f"[{flag}] {mid}: Det={d_sigs} | Model={m_sigs}")

    # 3. HOUSEHOLD MESSAGES (7 messages)
    hh_matches = 0
    print("\n--- HOUSEHOLD SALARY MESSAGES (7 messages) ---")
    for mid in HOUSEHOLD_MIDS:
        m_amends = results.get(mid, [])
        is_valid = (
            len(m_amends) == 1
            and m_amends[0].get("action") == "AMEND_RECURRING_AMOUNT"
            and m_amends[0].get("new_amount") is not None
        )
        if is_valid:
            hh_matches += 1
        flag = "PASS" if is_valid else "FAIL"
        amt = m_amends[0].get("new_amount") if m_amends else None
        print(f"[{flag}] {mid}: Action={m_amends[0].get('action') if m_amends else None}, Amount={amt}, Text={messages_map[mid]['message_text']}")

    print("\n" + "=" * 50)
    print("SUMMARY OF RE-TEST ON HAIKU:")
    print("=" * 50)
    print(f"MARK_NON_RECURRING exact agreement: {mnr_matches} / {len(MARK_NON_RECURRING_MIDS)}")
    print(f"TERMINATE_SERIES agreement:         {tser_matches} / {len(TERMINATE_SERIES_DET_MIDS)}")
    print(f"Household AMEND_RECURRING_AMOUNT:   {hh_matches} / {len(HOUSEHOLD_MIDS)}")
