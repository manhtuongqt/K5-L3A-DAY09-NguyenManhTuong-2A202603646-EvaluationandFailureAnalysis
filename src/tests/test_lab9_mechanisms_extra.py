"""Exercise instructor mechanisms under new registry names, without matching variant names."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
import pytest
pytestmark = pytest.mark.student


@pytest.mark.parametrize("bugs,claim,expected", [
    ({"no_override", "quiet_override"}, "C-002", "quiet"),
    ({"no_override", "misreport"}, "C-008", "misreport"),
    ({"no_override", "paraphrase", "extra_lookup"}, "C-008", "honest"),
])
def test_lab9_advanced_mechanisms_without_known_shape_names(bugs, claim, expected):
    from lab8.shapes import SHAPES
    from lab8.db import load_json, load_jsonl
    from lab9.eval import make_task, WORLD
    from lab9.variant_agent import make_shape
    from lab9.graders import DbFactKept, RefundAmountCorrect, ReplyLedgerConsistent
    old = dict(SHAPES)
    try:
        name = "contract_probe"
        SHAPES[name] = make_shape(name, bugs)
        claims = load_jsonl(Path("data/public_claims.jsonl"))
        labels = {c["claim_id"]: c["expected"] for c in claims}
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            trial = make_task(name, load_json(WORLD), claims, labels, Path(temp))({"claim_id": claim, "seed": 22})
        ctx = SimpleNamespace(output=trial, expected_output=labels[claim])
        if expected == "quiet":
            assert not any(e["kind"] == "model_override" for e in trial["events"])
            assert DbFactKept().evaluate(ctx).value is True
            assert RefundAmountCorrect().evaluate(ctx).value is False
            assert trial["lab8_pass"] is False
        elif expected == "misreport":
            assert trial["lab8_pass"] is True  # Existing outcome grader cannot see a reply lie.
            assert RefundAmountCorrect().evaluate(ctx).value is True
            assert ReplyLedgerConsistent().evaluate(ctx).value is False
        else:
            assert trial["lab8_pass"] is True
            assert ReplyLedgerConsistent().evaluate(ctx).value is True
    finally:
        SHAPES.clear()
        SHAPES.update(old)
