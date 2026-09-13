"""Compare deterministic vs LLM message amendment extraction and write docs/extraction-comparison.md."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import json
from pathlib import Path
from typing import Any


def run_comparison() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    det_path = repo_root / "src" / "data" / "message_amendments.json"
    model_path = repo_root / "src" / "data" / "model_message_amendments.json"
    messages_path = repo_root / "dataset" / "messages.csv"
    output_doc_path = repo_root / "docs" / "extraction-comparison.md"

    if not det_path.is_file():
        raise FileNotFoundError(f"Missing deterministic amendments at {det_path}")
    if not model_path.is_file():
        raise FileNotFoundError(f"Missing model amendments at {model_path}")

    with open(det_path, "r", encoding="utf-8") as f:
        det_amends: list[dict[str, Any]] = json.load(f)
    with open(model_path, "r", encoding="utf-8") as f:
        model_amends: list[dict[str, Any]] = json.load(f)

    messages_map: dict[str, dict[str, str]] = {}
    with open(messages_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            messages_map[r["message_id"]] = r

    # Group amendments by message_id
    det_by_msg: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in det_amends:
        det_by_msg[a["message_id"]].append(a)

    model_by_msg: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in model_amends:
        model_by_msg[a["message_id"]].append(a)

    all_mids = sorted(messages_map.keys())

    # Count by action type
    det_action_counts = Counter(a["action"] for a in det_amends)
    model_action_counts = Counter(a["action"] for a in model_amends)
    all_actions = sorted(set(det_action_counts.keys()) | set(model_action_counts.keys()))

    # Categorize agreements and disagreements
    agreements_by_action: Counter[str] = Counter()
    disagreements: list[dict[str, Any]] = []
    det_only_messages: list[str] = []
    model_only_messages: list[str] = []
    both_empty_count = 0
    exact_match_count = 0

    for mid in all_mids:
        det_list = det_by_msg.get(mid, [])
        model_list = model_by_msg.get(mid, [])

        if not det_list and not model_list:
            both_empty_count += 1
            continue
        elif det_list and not model_list:
            det_only_messages.append(mid)
            disagreements.append({
                "message_id": mid,
                "type": "deterministic_only",
                "det": det_list,
                "model": model_list,
                "text": messages_map[mid]["message_text"],
            })
            continue
        elif not det_list and model_list:
            model_only_messages.append(mid)
            disagreements.append({
                "message_id": mid,
                "type": "model_only",
                "det": det_list,
                "model": model_list,
                "text": messages_map[mid]["message_text"],
            })
            continue

        # Compare normalized representations
        def normalize_amend(a: dict[str, Any]) -> tuple[Any, ...]:
            action = a.get("action")
            # Compare key fields based on action
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

        det_sigs = sorted(normalize_amend(a) for a in det_list)
        model_sigs = sorted(normalize_amend(a) for a in model_list)

        if det_sigs == model_sigs:
            exact_match_count += 1
            for sig in det_sigs:
                agreements_by_action[sig[0]] += 1
        else:
            disagreements.append({
                "message_id": mid,
                "type": "content_or_action_mismatch",
                "det": det_list,
                "model": model_list,
                "text": messages_map[mid]["message_text"],
            })

    # Generate Markdown Report
    lines = [
        "# Message Amendment Extraction Comparison",
        "",
        "This document compares the deterministic baseline extractions (`src/data/message_amendments.json`) "
        "against the `claude-sonnet-5` model perception extractions (`src/data/model_message_amendments.json`).",
        "",
        "## 1. High-Level Summary",
        "",
        f"- **Total Messages in Dataset**: {len(all_mids)}",
        f"- **Messages Producing Amendments (Deterministic)**: {len(det_by_msg)} (Total amendments: {len(det_amends)})",
        f"- **Messages Producing Amendments (Model)**: {len(model_by_msg)} (Total amendments: {len(model_amends)})",
        f"- **Both Empty (No Amendments)**: {both_empty_count}",
        f"- **Exact Matches (Identical Actions & Core Attributes)**: {exact_match_count}",
        f"- **Disagreements / Divergences**: {len(disagreements)}",
        f"  - Emitted only by deterministic: {len(det_only_messages)}",
        f"  - Emitted only by model: {len(model_only_messages)}",
        f"  - Emitted by both but differing in action or parameters: {len(disagreements) - len(det_only_messages) - len(model_only_messages)}",
        "",
        "## 2. Action Breakdown and Agreements",
        "",
        "| Action Type | Deterministic Count | Model Count | Exact Agreements |",
        "|---|---|---|---|",
    ]

    for act in all_actions:
        lines.append(
            f"| `{act}` | {det_action_counts.get(act, 0)} | {model_action_counts.get(act, 0)} | {agreements_by_action.get(act, 0)} |"
        )

    lines.extend([
        "",
        "## 3. Itemized Disagreements",
        "",
        "The following sections document every disagreement for architectural review. The outputs are not merged.",
        "",
    ])

    for d in disagreements:
        mid = d["message_id"]
        dtype = d["type"]
        text = d["text"]
        lines.append(f"### `{mid}` ({dtype})")
        lines.append(f"**Verbatim Message Text:**")
        lines.append(f"> {text}")
        lines.append("")
        lines.append("**Deterministic Output:**")
        lines.append("```json")
        lines.append(json.dumps(d["det"], indent=2))
        lines.append("```")
        lines.append("")
        lines.append("**Model Output (`claude-sonnet-5`):**")
        lines.append("```json")
        lines.append(json.dumps(d["model"], indent=2))
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    output_doc_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_doc_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Comparison report written to {output_doc_path} ({len(disagreements)} disagreements found).")


if __name__ == "__main__":
    run_comparison()
