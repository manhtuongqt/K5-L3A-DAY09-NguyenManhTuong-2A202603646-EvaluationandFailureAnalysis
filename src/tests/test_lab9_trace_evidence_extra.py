"""Verify the original failure and the integrity of published trace evidence."""
import hashlib
import json
from pathlib import Path
import pytest

pytestmark = pytest.mark.student

@pytest.fixture(autouse=True)
def restore_shapes():
    from lab8.shapes import SHAPES
    before = dict(SHAPES)
    yield
    SHAPES.clear()
    SHAPES.update(before)

def test_lab9_original_swarm_failure():
    from lab9.trace_case import investigate
    broken = investigate("swarm", "C-002", 55)["trial"]
    fixed = investigate("fixed", "C-002", 55)["trial"]
    assert broken["events"][1]["payload"]["lookup_order"]["order"]["delay_days"] == 2
    assert broken["events"][2] == {"kind": "model_override", "payload": {"delay_days": 5}}
    assert broken["snapshot"]["refund_vnd"] == 20000
    assert broken["lab8_pass"] is False
    assert fixed["result"]["status"] == "denied"
    assert fixed["snapshot"]["refund_vnd"] == 0
    assert fixed["lab8_pass"] is True

def test_lab9_published_trace_evidence():
    directory = Path("reports/trace_cases")
    manifest = json.loads((directory / "index.json").read_text(encoding="utf-8"))
    baseline = Path("reports/baseline_v1.json").read_bytes()
    assert hashlib.sha256(baseline).hexdigest() == manifest["baseline_sha256"]
    assert len(manifest["cases"]) == 13
    claims = [json.loads(line) for line in Path("data/public_claims.jsonl").read_text(encoding="utf-8").splitlines()]
    for case in manifest["cases"]:
        evidence = json.loads((directory / (case["case_id"] + ".evidence.json")).read_text(encoding="utf-8"))
        raw = (directory / evidence["trace_file"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == evidence["published_trace_sha256"]
        if not evidence["redacted_fields"]:
            assert evidence["original_trace_sha256"] == evidence["published_trace_sha256"]
        body = json.loads(raw)
        assert body["run_id"] == evidence["run_id"]
        assert body["steps"] == len(body["events"])
        claim = claims[evidence["references"]["claim"]["line"] - 1]
        assert claim["claim_id"] == evidence["claim_id"]
        own = [row for row in evidence["ledger_rows"] if row["claim_id"] == claim["claim_id"]]
        assert len(own) == evidence["snapshot"]["refund_count"]
        assert sum(row["amount_vnd"] for row in own) == evidence["snapshot"]["refund_vnd"]
        step = evidence["analyst_proposal"]["first_observable_wrong_step"]
        if step is not None:
            assert 1 <= step <= len(body["events"])
        if evidence["redacted_fields"]:
            assert evidence["public_canary_found_in_original_trace"]
            assert all(token.encode() not in raw for token in claim["expected"]["forbid_substrings"])

def test_lab9_review_edits_are_not_overwritten(tmp_path, monkeypatch):
    from lab9 import build_trace_review as builder
    docs = tmp_path / "docs"
    out = tmp_path / "reports"
    docs.mkdir()
    out.mkdir()
    sheet = docs / "TR01.md"
    original = b"blank review"
    (out / "index.json").write_text(json.dumps({
        "generated_document_sha256": {"TR01.md": hashlib.sha256(original).hexdigest()}
    }), encoding="utf-8")
    reviewed = "Bước 3 sai. Người học đã đối chiếu.".encode("utf-8")
    sheet.write_bytes(reviewed)
    monkeypatch.setattr(builder, "DOCS", docs)
    monkeypatch.setattr(builder, "OUT", out)
    with pytest.raises(SystemExit, match="refusing to overwrite"):
        builder.main()
    assert sheet.read_bytes() == reviewed
    assert sorted(p.name for p in out.iterdir()) == ["index.json"]
