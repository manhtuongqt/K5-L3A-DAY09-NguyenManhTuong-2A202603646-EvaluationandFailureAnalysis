"""Record an explicit student confirmation; leave trace data and scores unchanged."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
OUT = SRC / "reports/trace_cases"
DOCS = ROOT / "docs/trace_review"

def read_at(commit, path):
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")

def main():
    source = DOCS / "confirmation.json"
    confirmation = json.loads(source.read_text(encoding="utf-8"))
    commit = confirmation["reviewed_commit"]
    reviewer, date = confirmation["reviewer"], confirmation["reviewed_on"]
    if confirmation["decision"] != "accept_all_existing_findings_without_changes":
        raise ValueError("This recorder only accepts an explicit unchanged confirmation")
    original_index = json.loads(read_at(commit, "src/reports/trace_cases/index.json"))
    case_ids = [case["case_id"] for case in original_index["cases"]]
    if set(case_ids) != set(confirmation["case_ids"]) or len(case_ids) != len(confirmation["case_ids"]):
        raise ValueError("Confirmation does not cover exactly the reviewed cases")
    plan = []
    for case in original_index["cases"]:
        cid = case["case_id"]
        rel = "src/reports/trace_cases/" + cid + ".evidence.json"
        record = json.loads(read_at(commit, rel))
        current = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        # Confirmation may update review metadata, never the recorded evidence.
        for key in record.keys() - {"student_review", "analyst_proposal"}:
            if current[key] != record[key]:
                raise ValueError("Evidence changed since review: " + cid + "/" + key)
        trace = OUT / record["trace_file"]
        if digest(trace.read_bytes()) != record["published_trace_sha256"]:
            raise ValueError("Trace hash changed since review: " + cid)
        proposal = record["analyst_proposal"]
        if current["analyst_proposal"]["finding"] != proposal["finding"]:
            raise ValueError("Finding changed since review: " + cid)
        fm, step = proposal["failure_mode"], proposal["first_observable_wrong_step"]
        assessment = ("observed_failure" if fm else
                      "insufficient_evidence_for_reply" if cid == "TR12" else "no_observed_failure")
        record["student_review"] = {
            "status": "confirmed", "assessment": assessment,
            "failure_mode": fm, "first_wrong_step": step,
            "reason": proposal["finding"], "accepted_existing_finding": True,
            "reviewer": reviewer, "reviewed_at": date, "reviewed_commit": commit,
            "confirmation_source": "docs/trace_review/confirmation.json",
            "confirmation_sha256": digest(source.read_bytes()),
        }
        record["analyst_proposal"]["author"] = "AI-assisted proposal; confirmed by student"
        rel_doc = f"docs/trace_review/{cid}.md"
        old_doc = read_at(commit, rel_doc).decode("utf-8").replace("\r\n", "\n")
        prefix = old_doc.split("## Bạn review", 1)[0]
        conclusion = "Đồng ý với nhận xét đề xuất."
        if cid == "TR12":
            conclusion = "Đồng ý: chưa đủ bằng chứng để chấm reply."
        step_text = str(step) if step is not None else (
            "Không xác định vì không có reply" if cid == "TR12" else "Không có bước sai quan sát được")
        footer = "\n".join([
            "## Kết quả review của người học", "",
            "| Mục | Xác nhận |", "|---|---|",
            f"| Kết luận | {conclusion} |",
            f"| Mã FM | {fm or 'Không gán lỗi'} |",
            f"| Bước sai đầu tiên | {step_text} |",
            "| Lý do / chỗ cần sửa | Đồng ý với bằng chứng và nhận xét ở trên; không yêu cầu sửa. |",
            f"| Người chấm / ngày | {reviewer} — {date} |", "",
            "Ghi theo [xác nhận của người học](confirmation.json) trong phiên làm việc. Không tự gán điểm số.", "",
        ])
        new_doc = prefix + footer
        actual_doc = (ROOT / rel_doc).read_text(encoding="utf-8").replace("\r\n", "\n")
        if actual_doc not in (old_doc, new_doc):
            raise ValueError("Review sheet has additional edits; refusing to overwrite " + cid)
        plan.append((ROOT / rel, record, ROOT / rel_doc, new_doc, assessment))
    index = json.loads((OUT / "index.json").read_text(encoding="utf-8"))
    index["review_status"] = "confirmed_by_student"
    index["confirmation"] = {
        "reviewer": reviewer, "reviewed_on": date, "reviewed_commit": commit,
        "source": "docs/trace_review/confirmation.json",
        "source_sha256": digest(source.read_bytes()), "confirmed_cases": len(case_ids),
        "observed_failures": 9, "no_observed_failure_controls": 3, "insufficient_reply_evidence": 1,
    }
    for case in index["cases"]:
        case["student_review"] = "confirmed"
    old_list = read_at(commit, "docs/trace_review/REVIEW.md").decode("utf-8").replace("\r\n", "\n")
    new_list = old_list.replace(
        "Nhận xét và FM hiện tại là đề xuất có AI hỗ trợ. Cột chấm của người học đang để trống.",
        f"{reviewer} đã review TR01–TR13 và đồng ý toàn bộ nhận xét ngày {date}. Không yêu cầu sửa. "
        "Nhận xét ban đầu có AI hỗ trợ; phần người chấm đã được ghi theo xác nhận trong phiên.")
    new_list = new_list.replace("| [ ] |", "| [x] |")
    new_list = new_list.replace("## Chấm từng mẫu", "## Xác nhận")
    start = new_list.index("1. Mở trace và evidence.json.")
    end = new_list.index("Không cần cho điểm cao hoặc thấp", start)
    new_list = (new_list[:start] +
                "Đã xác nhận 13/13 ca: chín ca lỗi, ba đối chứng không thấy lỗi, một ca thiếu dữ liệu reply (TR12).\n"
                "TR12 vẫn giữ kết luận chưa đủ bằng chứng; không chuyển thành reply đúng.\n"
                "Nguồn xác nhận: [confirmation.json](confirmation.json). Không có điểm số do người học cung cấp.\n\n" +
                new_list[end:])
    current_list = (DOCS / "REVIEW.md").read_text(encoding="utf-8").replace("\r\n", "\n")
    if current_list not in (old_list, new_list):
        raise ValueError("Review list has additional edits; refusing to overwrite")
    for path, record, doc, text, assessment in plan:
        write_json(path, record)
        doc.write_text(text, encoding="utf-8", newline="\n")
        print(record["case_id"], "confirmed", assessment)
    (DOCS / "REVIEW.md").write_text(new_list, encoding="utf-8", newline="\n")
    # Keep original blank-sheet hashes: build_trace_review must not erase completed reviews.
    index["confirmed_document_sha256"] = {p.name: digest(p.read_bytes()) for p in sorted(DOCS.glob("*.md"))}
    write_json(OUT / "index.json", index)
    print("recorded", len(plan), "confirmed reviews; trace bytes and score reports unchanged")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
