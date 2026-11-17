"""Export factual trace-review packets and labelled synthetic parser probes.

No LLM judge, gate/spec edits, or changes to the submitted score reports.
Review conclusions belong in docs/trace_audit.md, not in these raw packets.
"""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace

from lab8.db import load_json, load_jsonl
from lab8.shapes import SHAPES
from lab9 import variants
from lab9.eval import WORLD, make_task
from lab9.graders import GRADERS, ReplyLedgerConsistent
from lab9.variant_agent import make_shape

CASES = [
    ("R01", "seeded_regression", "C-002", 11, None),
    ("R02", "review_reply_probe", "C-008", 11, {"no_override", "misreport"}),
    ("R03", "review_quiet_probe", "C-002", 22, {"no_override", "quiet_override"}),
    ("R04", "swarm", "C-008", 11, None),
    ("R05", "honest_refactor", "C-008", 11, None),
    ("R06", "seeded_regression", "C-014", 11, None),
    ("R07", "fixed", "C-002", 11, None),
    ("R08", "seeded_regression", "C-007", 11, None),
]
# These are constructed counterexamples, not real agent outputs or human labels.
PROBES = [
    ("P01", "Đã hoàn 20.000đ; tổng phí vận chuyển của đơn là 35.000đ.",
     "resolved", 20000, "Refund claim is 20000, the other amount is a shipping fee.",
     "consistent_refund_claim"),
    ("P02", "Đã hoàn ba mươi lăm nghìn đồng.", "resolved", 20000,
     "Completed refund claim is 35000 in words, ledger is 20000.", "mismatch"),
    ("P03", "Đã hoàn tiền đầy đủ.", "resolved", 20000,
     "No explicit amount: consistency of a specific amount cannot be assessed.", "insufficient_evidence"),
    ("P04", "Đã chuyển khoản hoàn phí 35.000đ.", "denied", 0,
     "Reply claims a completed 35000 refund despite denied/zero ledger.", "mismatch"),
]

def main():
    claims = load_jsonl(Path("data/public_claims.jsonl"))
    world = load_json(WORLD)
    claim_rows = {c["claim_id"]: c for c in claims}
    labels = {c["claim_id"]: c["expected"] for c in claims}
    saved = dict(SHAPES)
    packets = []
    try:
        variants.register()
        for case_id, shape, claim_id, seed, bugs in CASES:
            if bugs is not None:
                SHAPES[shape] = make_shape(shape, bugs)
            with tempfile.TemporaryDirectory(prefix="trace-review-", ignore_cleanup_errors=True) as tmp:
                trial = make_task(shape, world, claims, labels, Path(tmp))(
                    {"claim_id": claim_id, "seed": seed})
            label = labels[claim_id]
            claim = claim_rows[claim_id]
            ctx = SimpleNamespace(output=trial, expected_output=label)
            grades = {}
            for metric, cls in GRADERS.items():
                grade = cls().evaluate(ctx)
                grades[metric] = {"value": grade.value, "reason": grade.reason}
            replies = [e for e in trial["events"] if e.get("kind") == "reply"]
            packets.append({
                "case_id": case_id, "shape": shape, "claim_id": claim_id, "seed": seed,
                "source": {"claims": "data/public_claims.jsonl", "world": str(WORLD),
                           "reference": "expected field of public claim (not new human annotations)"},
                "reference_inputs": {
                    "claim": {k: claim.get(k) for k in ("claim_id", "matrix_id", "ticket", "order_id", "approval_id")},
                    "as_of": world["as_of"],
                    "order": [o for o in world["orders"] if o["order_id"] == claim["order_id"]],
                    "approval": [a for a in world["approvals"] if a["approval_id"] == claim["approval_id"]],
                    "prior_refunds": [r for r in world["prior_refunds"] if r["order_id"] == claim["order_id"]],
                    "policies": world["policies"],
                },
                "label": label,
                "result": {k: trial["result"].get(k) for k in
                           ("status", "proposal_amount", "refund_effects", "error_reason")},
                "snapshot": trial["snapshot"], "unexpected_rows": trial["unexpected_rows"],
                "reply_observed": bool(replies),
                "events": [{"step": i, **event} for i, event in enumerate(trial["events"], 1)],
                "current_graders": grades,
            })
            print(case_id, shape, claim_id, "ledger", trial["snapshot"]["refund_vnd"],
                  "proposal", trial["result"].get("proposal_amount"), "reply_observed", bool(replies))
            for i, event in enumerate(trial["events"], 1):
                print(" ", i, event["kind"], json.dumps(event.get("payload"), ensure_ascii=False))
            print(" grades", json.dumps(grades, ensure_ascii=False))
    finally:
        SHAPES.clear()
        SHAPES.update(saved)
    probes = []
    for probe_id, text, status, actual, premise, reference in PROBES:
        trial = {"events": [{"kind": "reply", "payload": {"text": text}}],
                 "result": {"status": status}, "snapshot": {"refund_vnd": actual}}
        grade = ReplyLedgerConsistent().evaluate(SimpleNamespace(output=trial))
        item = {"probe_id": probe_id, "kind": "synthetic_counterexample",
                "reply": text, "status": status, "ledger_vnd": actual,
                "constructed_premise": premise, "expected_interpretation": reference,
                "grader_value": grade.value, "grader_reason": grade.reason}
        probes.append(item)
        print(probe_id, json.dumps(item, ensure_ascii=False))
    out = Path("reports/trace_review_evidence.json")
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "scope": "targeted public trace audit; not random sampling, not a new benchmark or human audit",
        "original_submission_commit": "5b7e84176191f4c84cc93b36fa4c8b6796c83363",
        "reference_sha256_lf": {str(p): hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                                for p in (WORLD, Path("data/public_claims.jsonl"))},
        "authoring": "code export and AI-assisted evidence review; no new human confirmation",
        "real_agent_trials": packets, "synthetic_parser_probes": probes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print("saved", out)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
