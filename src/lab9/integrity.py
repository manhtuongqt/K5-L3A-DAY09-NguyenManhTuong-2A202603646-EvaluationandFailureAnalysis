"""Validation helpers for M7; independent of shape/variant names."""
from __future__ import annotations

import math
from collections import Counter
from lab9.eval import aggregate
from lab9.graders import GRADERS


def _finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def _ratchet_entries(current, previous, key, threshold_key):
    problems = []
    now = {x[key]: x for x in current}
    if len(now) != len(current):
        problems.append(f"duplicate spec {key}")
    for old in previous:
        name = old[key]
        new = now.get(name)
        if new is None:
            problems.append(f"ratchet removed {name}")
            continue
        if old.get("blocking") and not new.get("blocking"):
            problems.append(f"ratchet disabled blocking {name}")
        a = new.get(threshold_key, {}) if threshold_key else new
        b = old.get(threshold_key, {}) if threshold_key else old
        for field, loose in (("min", lambda x, y: x < y),
                             ("max", lambda x, y: x > y),
                             ("max_increase", lambda x, y: x > y)):
            if field in b and (field not in a or not _finite(a[field]) or loose(a[field], b[field])):
                problems.append(f"ratchet loosened {name}.{field}")
        if b.get("no_significant_drop") and not a.get("no_significant_drop"):
            problems.append(f"ratchet removed no_significant_drop {name}")
        if threshold_key is None and new.get("metric") != old.get("metric"):
            problems.append(f"ratchet changed slice metric {name}")
    return problems


def validate(pr, base, spec, base_spec=None):
    problems = []
    pairs, tagmaps = [], []
    graded = {m["id"] for m in spec.get("metrics", []) if m["id"] in GRADERS}
    for title, report in (("PR", pr), ("baseline", base)):
        manifest = report.get("manifest", {})
        rows, metrics = report.get("rows"), report.get("metrics", {})
        if not isinstance(rows, list) or not rows or not isinstance(metrics, dict):
            problems.append(f"{title}: missing rows/metrics")
            pairs.append(set()); tagmaps.append({})
            continue
        seeds, count = manifest.get("seeds", []), manifest.get("items")
        if (not seeds or any(type(s) is not int for s in seeds)
                or len(set(seeds)) != len(seeds) or type(count) is not int or count < 1):
            problems.append(f"{title}: invalid manifest item/seed counts")
        if len(rows) != (count or 0) * len(seeds):
            problems.append(f"{title}: row count differs from manifest")
        if report.get("evaluator_failures"):
            problems.append(f"{title}: evaluator_failures")
        for mid, value in metrics.items():
            if not _finite(value):
                problems.append(f"{title}: nonfinite/missing metric {mid}")
        for m in spec.get("metrics", []):
            if m["id"] not in metrics:
                problems.append(f"{title}: missing spec metric {m['id']}")
        counter, tags = Counter(), {}
        for row in rows:
            item, seed = row.get("item_id"), row.get("seed")
            if not isinstance(item, str) or not item or type(seed) is not int:
                problems.append(f"{title}: invalid item_id/seed")
                continue
            counter[(item, seed)] += 1
            slices = row.get("slices", [])
            if not isinstance(slices, list) or any(not isinstance(t, str) for t in slices):
                problems.append(f"{title}: invalid slices {item}")
                slices = []
            if len(set(slices)) != len(slices):
                problems.append(f"{title}: duplicate slice tags {item}")
            tagset = frozenset(slices)
            if item in tags and tags[item] != tagset:
                problems.append(f"{title}: inconsistent slice tags {item}")
            tags[item] = tagset
            row_metrics = graded | {m["id"] for m in spec.get("metrics", []) if m["id"] in row}
            for mid in row_metrics:
                value = row.get(mid)
                if not _finite(value) or not 0 <= value <= 1:
                    problems.append(f"{title}: invalid grader value {item}@{seed}/{mid}")
            if "cost" in row and (not _finite(row["cost"]) or row["cost"] < 0):
                problems.append(f"{title}: invalid cost")
        if any(n != 1 for n in counter.values()):
            problems.append(f"{title}: duplicate item/seed rows")
        item_ids = {i for i, _ in counter}
        if len(item_ids) != count or set(counter) != {(i, s) for i in item_ids for s in seeds}:
            problems.append(f"{title}: incomplete item x seed grid")
        pairs.append(set(counter)); tagmaps.append(tags)
        # Recompute only when the full harness row contract is present; small test
        # reports need not provide cost or derived aggregate metrics.
        if not problems and all("cost" in row and graded <= row.keys() for row in rows):
            values = aggregate(rows, sorted(graded), k_values=spec.get("pass_k", []))
            for mid, value in values.items():
                if mid in metrics and (_finite(value) != _finite(metrics[mid])
                                       or (_finite(value) and abs(value - metrics[mid]) > 0.000051)):
                    problems.append(f"{title}: aggregate disagrees with rows {mid}")
    if pairs[0] != pairs[1]:
        problems.append("PR/baseline item x seed set differs")
    if tagmaps[0] != tagmaps[1]:
        problems.append("PR/baseline slice tags differ")
    if base_spec and base_spec.get("eval_set_version") == spec.get("eval_set_version"):
        problems += _ratchet_entries(spec.get("metrics", []), base_spec.get("metrics", []), "id", "threshold")
        problems += _ratchet_entries(spec.get("slices", []), base_spec.get("slices", []), "name", None)
        if spec.get("seeds") != base_spec.get("seeds"):
            problems.append("ratchet changed seeds")
    return problems
