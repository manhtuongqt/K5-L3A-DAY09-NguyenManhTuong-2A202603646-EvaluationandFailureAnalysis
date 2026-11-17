"""Additional contract tests; original instructor tests remain unchanged."""
import copy
import math
from types import SimpleNamespace
import pytest
from lab9 import stats

pytestmark = pytest.mark.student


@pytest.fixture(autouse=True)
def _lab9_dependencies():
    # Preserve collection under the unchanged Lab08 CI, which does not install
    # pydantic-evals and deselects these student tests.
    global gate, ReplyLedgerConsistent, investigate
    from lab9 import gate
    from lab9.graders import ReplyLedgerConsistent
    from lab9.trace_case import investigate
    from lab8.shapes import SHAPES
    original = dict(SHAPES)
    yield
    SHAPES.clear()
    SHAPES.update(original)


@pytest.mark.parametrize("args", [(0, 0, 0), (5, -1, 1), (5, 6, 1), (5, 2, 0),
                                  (5, 2, 6), (5.0, 2, 1), (True, 1, 1)])
def test_lab9_advanced_bad_combinatorial_inputs(args):
    for fn in (stats.pass_at_k, stats.pass_hat_k):
        with pytest.raises(ValueError):
            fn(*args)


@pytest.mark.parametrize("c", range(6))
def test_lab9_advanced_reliability_order(c):
    assert stats.pass_hat_k(5, c, 3) <= c / 5 + 1e-12
    assert c / 5 <= stats.pass_at_k(5, c, 3) + 1e-12


def test_lab9_stats_bad_inputs():
    with pytest.raises(ValueError):
        stats.confusion(["FAIL"], [])
    with pytest.raises(ValueError):
        stats.confusion(["OTHER"], ["PASS"])
    with pytest.raises(ValueError):
        stats.rogan_gladen(0.5, 0.4, 0.5)
    with pytest.raises(ValueError):
        stats.paired_bootstrap([float("nan")], [1])
    with pytest.raises(ValueError):
        stats.paired_bootstrap([1], [1, 2])


def test_lab9_evalset_hash_bytes_are_platform_independent(tmp_path, monkeypatch):
    import json
    from lab9 import evalset
    source = tmp_path / "public.jsonl"
    source.write_text(json.dumps({"claim_id": "C-X", "matrix_id": "T01", "expected": {"refund_vnd": 0}}),
                      encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    evalset.build(source)
    assert b"\r" not in evalset.ITEMS.read_bytes()


@pytest.mark.parametrize("text,status,actual,expected", [
    ("Dạ, LogiX đã hoàn 35.000đ cho đơn O-123.", "resolved", 35000, True),
    ("LogiX đã hoàn phí 20,000 VND cho đơn O-99 trong 3–5 ngày.", "resolved", 20000, True),
    ("Đã hoàn 35 000 đồng.", "resolved", 20000, False),
    ("Đã hoàn 35000đ.", "resolved", 20000, False),
    ("Dạ, không đủ điều kiện hoàn 35.000đ.", "denied", 0, True),
    ("Dạ, đã hoàn 35.000đ.", "denied", 0, False),
    ("Xin chờ 3 ngày, mã đơn O-123.", "resolved", 20000, True),
])
def test_lab9_reply_consistency(text, status, actual, expected):
    trial = {"events": [{"kind": "reply", "payload": {"text": text}}],
             "result": {"status": status}, "snapshot": {"refund_vnd": actual}}
    assert ReplyLedgerConsistent().evaluate(SimpleNamespace(output=trial)).value is expected


def test_lab9_first_wrong_step_regression():
    broken = investigate("seeded_regression", "C-002", 11)["trial"]
    fixed = investigate("fixed", "C-002", 11)["trial"]
    assert broken["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}
    assert broken["snapshot"]["refund_vnd"] == 20000 and not broken["lab8_pass"]
    assert fixed["snapshot"]["refund_vnd"] == 0 and fixed["lab8_pass"]
    assert all(e["kind"] != "model_override" for e in fixed["events"])


def _report():
    return {"manifest": {"eval_set_sha": "x", "items": 2, "seeds": [1, 2]},
            "rows": [{"item_id": f"E-{i}", "seed": s, "pass_rate": True, "slices": ["money"]}
                     for i in (1, 2) for s in (1, 2)],
            "metrics": {"pass_rate": 1.0}, "evaluator_failures": []}


SPEC = {"eval_set_version": "v2", "metrics": [
    {"id": "pass_rate", "blocking": True, "threshold": {"min": 0.8, "no_significant_drop": True}}],
    "slices": [{"name": "money", "metric": "pass_rate", "blocking": True,
                "min": 0.8, "no_significant_drop": True}]}


@pytest.mark.parametrize("mutation", ["duplicate", "error_on_green", "none", "nan", "inf", "slice",
                                      "missing", "extra_seed", "incomplete_grid", "aggregate"])
def test_lab9_advanced_hidden_style_integrity(mutation):
    base = _report()
    pr = copy.deepcopy(base)
    if mutation == "duplicate":
        pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    elif mutation == "error_on_green":
        pr["evaluator_failures"] = ["a grader failed"]
    elif mutation == "none":
        pr["rows"][0]["pass_rate"] = None
    elif mutation in ("nan", "inf"):
        pr["metrics"]["pass_rate"] = float(mutation)
    elif mutation == "slice":
        pr["rows"][0]["slices"] = []
    elif mutation == "missing":
        del pr["metrics"]["pass_rate"]
    elif mutation == "extra_seed":
        pr["manifest"]["seeds"].append(3)
    elif mutation == "incomplete_grid":
        pr["rows"][-1]["item_id"] = "E-3"
    elif mutation == "aggregate":
        # Add complete harness contract so recomputation is meaningful.
        pr["rows"][0]["pass_rate"] = False
        for rep in (pr, base):
            for row in rep["rows"]:
                row["cost"] = 1.0
    assert gate.integrity_check(pr, base, SPEC)


@pytest.mark.parametrize("change", ["min", "blocking", "remove_metric", "remove_slice", "slice_min", "ci"])
def test_lab9_advanced_ratchet(change):
    original = copy.deepcopy(SPEC)
    new = copy.deepcopy(original)
    if change == "min":
        new["metrics"][0]["threshold"]["min"] = 0.7
    elif change == "blocking":
        new["metrics"][0]["blocking"] = False
    elif change == "remove_metric":
        new["metrics"] = []
    elif change == "remove_slice":
        new["slices"] = []
    elif change == "slice_min":
        new["slices"][0]["min"] = 0.7
    elif change == "ci":
        new["slices"][0]["no_significant_drop"] = False
    assert gate.integrity_check(_report(), _report(), new, original)


def test_lab9_advanced_baseline_self_merge():
    assert gate.check(_report(), _report(), SPEC, SPEC)[0] == []


def test_lab9_advanced_single_item_slice():
    assert stats.paired_bootstrap([0.6], [1.0]) == (-0.4, -0.4, -0.4)
