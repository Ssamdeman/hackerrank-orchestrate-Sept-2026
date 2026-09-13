"""Pull messages from extraction-comparison involving MARK_NON_RECURRING and TERMINATE_SERIES."""

from __future__ import annotations

import csv
import json
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent

det_path = repo_root / "src" / "data" / "message_amendments.json"
model_path = repo_root / "src" / "data" / "model_message_amendments.json"
messages_path = repo_root / "dataset" / "messages.csv"

with open(det_path, "r", encoding="utf-8") as f:
    det_amends = json.load(f)
with open(model_path, "r", encoding="utf-8") as f:
    model_amends = json.load(f)

messages_map = {}
with open(messages_path, "r", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        messages_map[r["message_id"]] = r

det_by_mid = {}
for a in det_amends:
    det_by_mid.setdefault(a["message_id"], []).append(a)

model_by_mid = {}
for a in model_amends:
    model_by_mid.setdefault(a["message_id"], []).append(a)

target_actions = {"MARK_NON_RECURRING", "TERMINATE_SERIES"}

target_mids = set()
for a in det_amends:
    if a["action"] in target_actions:
        target_mids.add(a["message_id"])
for a in model_amends:
    if a["action"] in target_actions:
        target_mids.add(a["message_id"])

target_mids = sorted(target_mids)

print(f"Total messages involving MARK_NON_RECURRING or TERMINATE_SERIES: {len(target_mids)}")

for mid in target_mids:
    d_acts = [a["action"] for a in det_by_mid.get(mid, [])]
    m_acts = [a["action"] for a in model_by_mid.get(mid, [])]
    print(f"\n{mid}: Det={d_acts} | Model={m_acts}")
    print(f"Text: {messages_map[mid]['message_text']}")
    print(f"Det JSON: {det_by_mid.get(mid, [])}")
    print(f"Model JSON: {model_by_mid.get(mid, [])}")
