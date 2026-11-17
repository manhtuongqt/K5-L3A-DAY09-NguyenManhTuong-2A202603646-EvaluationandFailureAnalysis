"""Build trace evidence and blank student review sheets. No scoring or gate changes."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

from lab8.db import connect, load_json, load_jsonl
from lab8.shapes import SHAPES
from lab9 import variants
from lab9.eval import WORLD, make_task
from lab9.graders import GRADERS
from lab9.variant_agent import make_shape

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
OUT = SRC / "reports/trace_cases"
DOCS = ROOT / "docs/trace_review"

# Analyst proposals for specific public examples, not gate rules or human labels.
EXAMPLES = [
    ("TR01", "swarm", "C-002", 55, None, "FM-03", 3,
     "Lỗi có sẵn trong baseline swarm đã nộp.",
     "Đổi delay_days từ 2 thành 5. DB ghi 2; điều khoản SHIP-LATE-03 yêu cầu ít nhất 3 ngày.",
     [2, 3, 4]),
    ("TR02", "review_leak", "C-001", 11, {"no_override", "leaky_trace"}, "FM-01", 1,
     "Variant gài lỗi bằng công tắc leaky_trace của đề.",
     "Event debug_claim_row chứa parent_secret và raw_headers_json. Canary của nguồn xuất hiện trong trace.",
     [1]),
    ("TR03", "review_denied", "C-007", 11, {"no_override", "ignore_denied"}, "FM-02", 4,
     "Variant gài lỗi bằng công tắc ignore_denied của đề.",
     "Approval A-007 hết hạn. Host từ chối, ledger 0; reply vẫn nói đã hoàn 35.000đ.",
     [2, 3, 4]),
    ("TR04", "review_sum", "C-014", 11, {"no_override", "sum_parts"}, "FM-04", 4,
     "Variant gài lỗi bằng công tắc sum_parts của đề.",
     "Hai khoản là 30.000đ và 150.000đ. Quy tắc lấy max=150.000đ; proposal lại bằng tổng 180.000đ.",
     [3, 4, 5]),
    ("TR05", "review_deduct", "C-014", 11, {"no_override", "pre_deducted"}, "FM-05", 5,
     "Variant gài lỗi bằng công tắc pre_deducted của đề.",
     "Agent tự trừ 30.000đ khỏi quote 150.000đ, gửi proposal 120.000đ. Host trừ tiếp nên chỉ ghi 90.000đ.",
     [3, 4, 5, 6]),
    ("TR06", "review_stale", "C-006", 11, {"no_override", "stale_clause"}, "FM-06", 3,
     "Variant gài lỗi bằng công tắc stale_clause của đề.",
     "Quote dùng SHIP-LATE-OLD trong policy is_current=false. DB trễ 2 ngày; policy hiện hành chưa cho hoàn.",
     [2, 3, 4]),
    ("TR07", "review_sibling", "C-001", 11, {"no_override", "sibling_refund"}, "FM-07", 4,
     "Variant gài lỗi bằng công tắc sibling_refund của đề.",
     "Đang xử lý C-001 nhưng batch_refund ghi tiền cho C-010. unexpected_rows=1.",
     [3, 4, 5]),
    ("TR08", "review_misreport", "C-008", 11, {"no_override", "misreport"}, "FM-08", 4,
     "Variant gài lỗi bằng công tắc misreport của đề.",
     "Reply báo đã hoàn 35.000đ. Approval chỉ cho 20.000đ; ledger thực ghi 20.000đ.",
     [3, 4]),
    ("TR09", "review_quiet", "C-002", 22, {"no_override", "quiet_override"}, "FM-03", 3,
     "Variant gài lỗi bằng công tắc quiet_override của đề.",
     "DB trễ 2 ngày nhưng quote 20.000đ. Bước 3 là lỗi đầu tiên nhìn thấy; không có event ghi thao tác thay dữ liệu.",
     [2, 3, 4]),
    ("TR10", "fixed", "C-002", 55, None, None, None,
     "Đối chứng của TR01, dùng fixed nguyên bản.",
     "DB trễ 2 ngày, quote 0, status denied, ledger 0. Không thấy lỗi trong các tiêu chí đối chiếu.",
     [2, 3, 4]),
    ("TR11", "honest_refactor", "C-008", 11, None, None, None,
     "Đối chứng diễn đạt khác, dùng honest_refactor nguyên bản.",
     "Proposal 35.000đ; approval và ledger 20.000đ; reply 20.000đ. Proposal khác ledger là đúng ở ca này.",
     [3, 4, 5]),
    ("TR12", "swarm", "C-008", 11, None, None, None,
     "Swarm gốc, dùng để kiểm phần thiếu bằng chứng.",
     "Ledger 20.000đ đúng approval. Trace không có reply; chưa đủ dữ liệu để chấm nội dung reply.",
     [2, 3]),
    ("TR13", "fixed", "C-005", 11, None, None, None,
     "Đối chứng quyền truy cập, không ghi nhận lỗi FM-09.",
     "lookup_order trả visible=false, outside_principal_scope. Agent escalated, ledger 0; host chặn đúng.",
     [2, 3]),
]

def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")

def sha(data):
    return hashlib.sha256(data).hexdigest()

def event_rows(events, selected):
    fields = {
        "investigator": ["lookup_order.visible", "lookup_order.reason", "lookup_order.order.delay_days"],
        "model_override": ["delay_days"],
        "quote": ["amount_vnd", "clause_ids", "parts"],
        "proposal": ["amount_vnd"],
        "refund_history": ["refund_count", "refunded_vnd"],
        "batch_refund": ["claim_id", "ok", "reason"],
        "reply": ["text"],
        "debug_claim_row": ["parent_secret", "raw_headers_json"],
    }
    rows = []
    for step in selected:
        if step > len(events):
            continue
        event = events[step - 1]
        for field in fields.get(event["kind"], []):
            value = event["payload"]
            for key in field.split("."):
                if not isinstance(value, dict) or key not in value:
                    break
                value = value[key]
            else:
                shown = json.dumps(value, ensure_ascii=False).replace("|", "&#124;")
                rows.append(f"| {step} | {event['kind']} | payload.{field} | {shown} |")
    return rows

def protect_review_edits():
    manifest = OUT / "index.json"
    if manifest.is_file():
        hashes = json.loads(manifest.read_text(encoding="utf-8")).get("generated_document_sha256", {})
        for name, expected in hashes.items():
            path = DOCS / name
            if not path.is_file() or sha(path.read_bytes()) != expected:
                raise SystemExit("Review sheet edited; refusing to overwrite " + str(path))
        if hashes:
            return
    # Upgrade an earlier blank draft, but preserve any filled review cells.
    for sheet in DOCS.glob("TR*.md"):
        text = sheet.read_text(encoding="utf-8")
        if "## Bạn review" in text:
            cells = [line for line in text.split("## Bạn review", 1)[1].splitlines()
                     if line.startswith("|")][2:]
            if any(line.rsplit("|", 2)[1].strip() for line in cells):
                raise SystemExit("Review entries present; refusing to overwrite " + str(sheet))

def main():
    protect_review_edits()
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    world = load_json(SRC / WORLD)
    claims = load_jsonl(SRC / "data/public_claims.jsonl")
    by_id = {c["claim_id"]: c for c in claims}
    labels = {c["claim_id"]: c["expected"] for c in claims}
    baseline_path = SRC / "reports/baseline_v1.json"
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    item_claim = {x["item_id"]: x["claim_id"] for x in load_jsonl(SRC / "data/eval/eval_set_v1.jsonl")}
    failures = [r for r in baseline["rows"] if r["pass_rate"] is False]
    # Stop rather than publish an outdated claim about the submitted baseline.
    if [(item_claim[r["item_id"]], r["seed"]) for r in failures] != [("C-002", 55)]:
        raise ValueError("Baseline failures changed; update the review selection before publishing")
    original = dict(SHAPES)
    index = []
    try:
        variants.register()
        for cid, shape, claim_id, seed, bugs, fm, first_step, origin, finding, selected in EXAMPLES:
            if bugs:
                SHAPES[shape] = make_shape(shape, bugs)
            claim = by_id[claim_id]
            with tempfile.TemporaryDirectory(prefix="trace-sheet-", ignore_cleanup_errors=True) as temp:
                trial = make_task(shape, world, claims, labels, Path(temp))({"claim_id": claim_id, "seed": seed})
                raw_path = Path(trial["result"]["trace_path"])
                raw_bytes = raw_path.read_bytes()
                trace = json.loads(raw_bytes)
                if trace["run_id"] != trial["result"]["run_id"] or trace["events"] != trial["events"]:
                    raise ValueError("Trace contract mismatch: " + cid)
                conn = connect(Path(temp) / f"{shape}-{claim_id}-{seed}.sqlite")
                try:
                    ledger = [dict(row) for row in conn.execute(
                        "SELECT claim_id,order_id,amount_vnd,status FROM refund_ledger ORDER BY claim_id")]
                    audit = [dict(row) for row in conn.execute(
                        "SELECT claim_id,event_type,details_json FROM audit_events ORDER BY claim_id,event_type")]
                finally:
                    conn.close()
            if first_step is not None and first_step > len(trace["events"]):
                raise ValueError("Review step outside trace: " + cid)
            redactions = []
            published = copy.deepcopy(trace)
            for i, event in enumerate(published["events"]):
                if event["kind"] == "debug_claim_row":
                    for key in ("parent_secret", "raw_headers_json", "raw_headers"):
                        if key in event["payload"]:
                            redactions.append(f"/events/{i}/payload/{key}")
                            event["payload"][key] = "[REDACTED]"
            trace_file = OUT / (cid + (".redacted.trace.json" if redactions else ".trace.json"))
            if redactions:
                dump(trace_file, published)
            else:
                trace_file.write_bytes(raw_bytes)  # Exact captured bytes; Git -text preserves the hash.
            ctx = SimpleNamespace(output=trial, expected_output=labels[claim_id])
            grades = {}
            for metric, cls in GRADERS.items():
                grade = cls().evaluate(ctx)
                grades[metric] = {"value": grade.value, "reason": grade.reason}
            if cid == "TR01":
                for metric in grades:
                    if grades[metric]["value"] != failures[0][metric]:
                        raise ValueError("Reproduced baseline row differs: " + metric)
            refs = {
                "claim": {"file": "data/public_claims.jsonl",
                          "line": next(i for i, c in enumerate(claims, 1) if c["claim_id"] == claim_id)},
                "order_pointer": next(("/orders/" + str(i) for i, row in enumerate(world["orders"])
                                       if row["order_id"] == claim["order_id"]), None),
                "approval_pointer": next(("/approvals/" + str(i) for i, row in enumerate(world["approvals"])
                                          if row["approval_id"] == claim["approval_id"]), None),
            }
            expected = {k: v for k, v in labels[claim_id].items() if k != "forbid_substrings"}
            record = {
                "case_id": cid, "origin": origin, "shape": shape, "claim_id": claim_id, "seed": seed,
                "run_id": trace["run_id"], "references": refs,
                "trace_file": trace_file.name, "original_trace_sha256": sha(raw_bytes),
                "published_trace_sha256": sha(trace_file.read_bytes()), "redacted_fields": redactions,
                "public_canary_found_in_original_trace": any(t in raw_bytes.decode("utf-8")
                    for t in labels[claim_id].get("forbid_substrings", []) if t),
                "expected": expected,
                "result": {k: trial["result"].get(k) for k in
                           ("status", "proposal_amount", "refund_effects", "error_reason")},
                "snapshot": trial["snapshot"], "ledger_rows": ledger, "host_audit_rows": audit,
                "unexpected_rows": trial["unexpected_rows"], "grader_results": grades,
                "analyst_proposal": {"failure_mode": fm, "first_observable_wrong_step": first_step,
                                     "finding": finding, "author": "AI-assisted; pending student review"},
                "student_review": {"status": "pending", "failure_mode": None, "first_wrong_step": None,
                                   "reason": None, "reviewer": None, "reviewed_at": None},
            }
            dump(OUT / (cid + ".evidence.json"), record)
            amount_rows = [
                ("status", expected["status"], trial["result"]["status"]),
                ("proposal_amount", expected["proposal_amount"], trial["result"]["proposal_amount"]),
                ("refund_vnd", expected["refund_vnd"], trial["snapshot"]["refund_vnd"]),
                ("refund_count", expected["refund_count"], trial["snapshot"]["refund_count"]),
            ]
            lines = [
                f"# {cid} — {claim_id}, seed {seed}", "", origin, "",
                f"- Shape: {shape}. Run: {trace['run_id']}.",
                f"- Nhận xét đề xuất: {finding}",
                f"- FM đề xuất: {fm or 'không gán lỗi'}. Bước sai quan sát được: {first_step or 'không xác định / không thấy lỗi'}.",
                "", "## Bằng chứng", "",
                f"- [Trace]({'../../src/reports/trace_cases/' + trace_file.name}); thứ tự bước tính từ 1.",
                f"- [Ledger, host audit và nhãn]({'../../src/reports/trace_cases/' + cid + '.evidence.json'}).",
                f"- [Claim gốc](../../src/data/public_claims.jsonl#L{refs['claim']['line']}); world: "
                f"{refs['order_pointer']}, {refs['approval_pointer'] or 'không có approval'} trong [public_world_state.json](../../src/data/public_world_state.json).",
            ]
            if redactions:
                lines.append("- Trace đã che giá trị secret/header. Hash bản gốc và các vị trí che có trong evidence.json.")
            lines += ["", "Trích các trường cần đối chiếu; event đầy đủ nằm trong tệp trace.", "",
                      "| Bước | Event | Trường | Giá trị |", "|---:|---|---|---|"]
            lines += event_rows(published["events"], selected)
            lines += ["", "| Trường | Giá trị đúng theo nhãn | Thực tế |", "|---|---|---|"]
            lines += [f"| {k} | {a} | {b} |" for k, a, b in amount_rows]
            lines += [
                "", "## Bạn review", "",
                "| Mục | Bạn điền |", "|---|---|", "| Đồng ý / cần sửa / chưa đủ bằng chứng | |",
                "| Mã FM | |", "| Bước sai đầu tiên | |", "| Lý do hoặc chỗ cần sửa | |",
                "| Người chấm / ngày | |", "",
            ]
            (DOCS / (cid + ".md")).write_text("\n".join(lines), encoding="utf-8", newline="\n")
            index.append({"case_id": cid, "claim_id": claim_id, "seed": seed, "shape": shape,
                          "failure_mode_proposal": fm, "first_wrong_step_proposal": first_step,
                          "trace_file": trace_file.name, "student_review": "pending"})
            print(cid, shape, claim_id, seed, "step", first_step, "proposal",
                  trial["result"]["proposal_amount"], "ledger", trial["snapshot"]["refund_vnd"],
                  "extra_rows", trial["unexpected_rows"], flush=True)
    finally:
        SHAPES.clear()
        SHAPES.update(original)
    manifest = {
        "agent_source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "baseline_sha256": sha(baseline_path.read_bytes()), "baseline_failures": len(failures),
        "scope": "one reproduced original swarm failure, instructor injected variants and controls; not production incidents",
        "review_status": "pending_student_review", "cases": index,
    }
    rows = [
        "# Trace để review và chấm", "",
        "TR01 là lượt lỗi duy nhất trong baseline v1 đã nộp: swarm, C-002@55. Đã chạy lại và so từng metric với dòng baseline.",
        "TR02–TR09 dùng công tắc gài lỗi có sẵn của đề. TR10–TR13 là đối chứng hoặc trường hợp thiếu dữ liệu. Tất cả đều chạy trên mô phỏng của lab.",
        "Nhận xét và FM hiện tại là đề xuất có AI hỗ trợ. Cột chấm của người học đang để trống.",
        "", "| Mẫu | Claim@seed | FM đề xuất | Bước sai | Bạn đã review |",
        "|---|---|---|---:|---|",
    ]
    rows += [f"| [{r['case_id']}]({r['case_id']}.md) | {r['claim_id']}@{r['seed']} | "
             f"{r['failure_mode_proposal'] or 'đối chứng / chưa đủ dữ liệu'} | "
             f"{r['first_wrong_step_proposal'] or '—'} | [ ] |" for r in index]
    rows += [
        "", "## Chấm từng mẫu", "",
        "1. Mở trace và evidence.json. Đọc dữ liệu gốc được dẫn trong mẫu.",
        "2. Kiểm tra bước được nêu có thực sự sai không. Nếu chưa đủ dữ liệu, ghi rõ chỗ thiếu.",
        "3. Điền kết luận, FM, bước sai và lý do ở mục Bạn review. Đánh dấu lại trong bảng này.",
        "", "Không cần cho điểm cao hoặc thấp theo điểm agent. Ví dụ: proposal 35.000đ và ledger 20.000đ có thể đúng do approval giới hạn 20.000đ.",
        "Lỗi parser tự tạo P01–P04 ở bản audit trước không được tính vào 13 trace này.",
        "", "Chạy lại từ src/: python -m lab9.build_trace_review",
        "Script dừng nếu bất kỳ phiếu hoặc bảng review nào đã được sửa, để giữ phần bạn chấm.",
    ]
    (DOCS / "REVIEW.md").write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    manifest["generated_document_sha256"] = {p.name: sha(p.read_bytes()) for p in sorted(DOCS.glob("*.md"))}
    dump(OUT / "index.json", manifest)
    print("saved", len(index), "cases; student reviews left blank")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
