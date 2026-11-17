"""Strict reproduction comparison, including derived pass^k metrics.

The instructor ci_check remains unchanged and is used for Core v1. Its check
that every own metric is a registered Evaluator does not apply to derived
pass_hat_5, which the harness calculates in aggregate(). This separate check
compares ALL v2 metrics and paired rows; it does not waive or remove a grader.
"""
import argparse
import json
from pathlib import Path
from lab9.ci_check import _same


def compare(actual, baseline):
    errors = []
    if actual.get("shape") != "swarm" or baseline.get("shape") != "swarm":
        errors.append("both reports must be swarm")
    for field in ("eval_set_sha", "items", "seeds", "metric_spec_version", "llm"):
        if not _same(actual.get("manifest", {}).get(field), baseline.get("manifest", {}).get(field)):
            errors.append("manifest mismatch: " + field)
    if not _same(actual.get("metrics", {}), baseline.get("metrics", {})):
        errors.append("aggregate metrics mismatch")
    key = lambda row: (row["item_id"], row["seed"])
    if not _same(sorted(actual["rows"], key=key), sorted(baseline["rows"], key=key)):
        errors.append("paired rows mismatch")
    if actual.get("evaluator_failures") or baseline.get("evaluator_failures"):
        errors.append("evaluator failure")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--actual", required=True)
    ap.add_argument("--baseline", required=True)
    args = ap.parse_args()
    read = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
    errors = compare(read(args.actual), read(args.baseline))
    print("\n".join(errors) if errors else "PASS: all derived metrics and paired rows reproduce baseline")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
