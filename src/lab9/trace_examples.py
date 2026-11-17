"""Reproduce taxonomy examples using instructor bug switches, never editing variants."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import tempfile
from lab8.db import load_json, load_jsonl
from lab8.shapes import SHAPES
from lab9.eval import WORLD, make_task
from lab9.variant_agent import make_shape

EXAMPLES = [
    ("FM-01", "C-001", ["no_override", "leaky_trace"]),
    ("FM-02", "C-007", ["no_override", "ignore_denied"]),
    ("FM-03", "C-002", ["no_override", "ticket_trust"]),
    ("FM-04", "C-014", ["no_override", "sum_parts"]),
    ("FM-05", "C-014", ["no_override", "pre_deducted"]),
    ("FM-06", "C-006", ["no_override", "stale_clause"]),
    ("FM-07", "C-001", ["no_override", "sibling_refund"]),
    ("FM-08", "C-008", ["no_override", "misreport"]),
    ("FM-09", "C-005", ["no_override"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/taxonomy_examples.json")
    args = ap.parse_args()
    claims = load_jsonl(Path("data/public_claims.jsonl"))
    labels = {c["claim_id"]: c["expected"] for c in claims}
    examples = []
    for fm, claim, bugs in EXAMPLES:
        name = "taxonomy_" + fm.replace("-", "_")
        SHAPES[name] = make_shape(name, set(bugs))
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            trial = make_task(name, load_json(WORLD), claims, labels, Path(tmp))({"claim_id": claim, "seed": 11})
        # Do not distribute raw parent data from the deliberate leaky variant.
        events = []
        for i, event in enumerate(trial["events"], 1):
            if event["kind"] == "debug_claim_row":
                payload = {"redacted": True, "forbidden_value_present":
                           any(t in trial["blob"] for t in labels[claim].get("forbid_substrings", []))}
            else:
                payload = event.get("payload")
            events.append({"step": i, "kind": event["kind"], "payload": payload})
        examples.append({"fm": fm, "claim_id": claim, "seed": 11, "bugs": bugs,
                         "lab8_pass": trial["lab8_pass"], "lab8_reason": trial["lab8_reason"],
                         "status": trial["result"]["status"], "proposal_amount": trial["result"]["proposal_amount"],
                         "snapshot": trial["snapshot"], "unexpected_rows": trial["unexpected_rows"],
                         "events": events,
                         "scope": "protected negative control; no actual cross-principal failure observed" if fm == "FM-09" else "injected instructor bug demonstration"})
    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"examples": examples}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for ex in examples:
        print(ex["fm"], ex["claim_id"], ex["status"], "quote", ex["proposal_amount"],
              "ledger", ex["snapshot"]["refund_vnd"], "extra_rows", ex["unexpected_rows"],
              "events", [(e["step"], e["kind"]) for e in ex["events"]])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
