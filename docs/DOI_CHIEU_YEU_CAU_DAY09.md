# Đối chiếu yêu cầu Day09

Người học: Nguyễn Mạnh Tường — 2A202603646 — lớp L3A, bài cá nhân.
Bài nộp: PR `starter/d09 → main` trong [fork Day09 cá nhân](https://github.com/manhtuongqt/K5-L3A-DAY09-NguyenManhTuong-2A202603646-EvaluationandFailureAnalysis), không phải repo nhóm Day08.
Nguồn agent được chép từ `src/` của repo gốc Day08 giảng viên tại `034c6c421c198dae67a9211d15e2587d5a378972`, import tại `0949ed9`. Day09 starter là `d1b9471540727d693c9eb392667b9f0d8a998bf5`. Baseline sinh bằng script trên swarm gốc, trước các candidate; CI chạy lại đối chiếu. Hạn lớp: **12:00 trưa 18/11/2026**, nộp URL PR vào **Day 9 Lab Assignment 3A** trên LMS.

## Gate và bằng chứng

| Yêu cầu | Kết quả public / phạm vi | Bằng chứng |
|---|---|---|
| M0 smoke | M0 PASS | evidence/day09/m0_smoke.txt |
| M0 eval set | 14 item, nhãn riêng | src/data/eval/eval_set_v1.jsonl và labels_v1.json |
| M1 taxonomy ≥5 FM | 8 cơ chế lỗi chạy thật; FM-09 thêm đối chứng phòng vệ | failure_taxonomy.md, src/reports/taxonomy_examples.json |
| M1 provenance và check | Check v1/v2 đều 0 problem; provenance ghi nguồn matrix/pack, không bịa người audit | evidence/day09/m1_evalset_v1.txt, m5_evalset_v2.txt |
| M1 năm anchor | Có phân tích event và mã cố định; key riêng chưa có nên không tự xác nhận khớp key | failure_taxonomy.md, trace_case.md; phía giảng viên |
| M2 stats | Core tests xanh; FAIL là lớp dương; kappa undefined bị từ chối | src/lab9/stats.py, evidence/day09/core_tests.txt |
| M2 tone | κ=.757, P=.857, R=.8, PASS | evidence/day09/m2_tone.txt |
| M2 helpful | κ=.375, P=1, R=.3, FAIL đúng dự kiến | evidence/day09/m2_helpful.txt |
| M2 audit ≥5 | 9 ca có lý do và sửa rubric, người học đã đối chiếu xác nhận | judge_audit.md |
| M3 hai grader | Tiền/approval chấm bằng code từ ledger và nhãn | src/lab9/graders.py, src/tests/test_lab9_graders.py giữ nguyên |
| M3 detection/false alarm | 100% / 0%; có lưu lượt trước 75% | evidence/day09/m3_detection.txt, m3_detection_before.txt |
| M3 FM-08 | reply_ledger_consistent blocking min=1; test chứng minh TrialPass cũ có thể bỏ sót | src/config/metric_spec*.yaml, src/tests/test_lab9_mechanisms_extra.py |
| Trace case + regression test | C-002@11 sai đầu tiên event 3; broken fail, fixed pass | trace_case.md, test_lab9_first_wrong_step_regression |
| M4 bootstrap | Δ −.271; CI [−.500, −.057], khớp tham chiếu | evidence/day09/m4_gate_seeded_regression.txt |
| M4 baseline | Swarm 69/70, cùng eval SHA/seeds/spec; fixed và PR swarm qua | src/reports/baseline_v1.json, eval_fixed.json, eval_pr.json |
| M4 CI Core | Phải chạy thật trên fork Day09 và đọc Checks của commit cuối | workflow eval-gate, evidence/day09/m4_ci_check.txt |
| Harness eval | Version 1.2, giữ section orchestration, thêm eval | src/harness_map.yaml |
| Eval card và PRD | Dẫn run_id, spec, version, metric, giới hạn và người giữ gate | eval_card.md, PRD_v1.1.md |
| M5 map/coverage | V2 đủ 28 item, 0 problem, mọi FM bị tấn công ≥3 item | config/fm_map.yaml, eval set v2, m5_evalset_v2.txt |
| M5 slices | money_movement và adversarial blocking; slice regression chỉ bị money_movement chặn | evidence/day09/v2_gate_slice_regression.txt |
| M6 pass@k/pass^k | Public/biên đúng; sai n,c,k bị từ chối | stats.py, test_lab9_contract_extra.py, advanced_tests.txt |
| M6 A/A | Hai seed set cho mọi Δ=0 trên MockLLM | evidence/day09/m6_aa.txt |
| M6 floor reliability | pass_hat_5 blocking min=.8; flaky chỉ đạt .5714 | metric_spec_v2.yaml, v2_gate_flaky_regression.txt |
| M7 integrity/ratchet | Chặn None/NaN, drop/cherry-pick, duplicate, evaluator error, đổi slice, nới spec | lab9/integrity.py, extra tests và log trap |
| M7 scorecard | 3/3 regression blocked, false alarm 0 | evidence/day09/m7_mutation.txt |
| M7 trap | 4/4 trap bị gate exit 1; lệnh tổng traps exit 0 | m7_traps.txt và m7_trap_*.txt |
| M7 baseline tự so | Merge ở cả v1/v2 | m4_baseline_self.txt, v2_baseline_self.txt |
| Test đúng phạm vi Day09 | 57 test host/CLI và 67 test Day09 có marker student đều PASS; không làm ba shape TODO Day08 | evidence/day09/host_tests.txt, day09_tests.txt |
| Bảo mật/nguồn | Kiểm file gốc, protected Lab08, mẫu credential và SHA | python -m lab9.check_sources; evidence/day09/source_check.txt |
| CI cuối | Cần bật Actions, eval-gate + eval-gate-v2 chạy thật; workflow bổ sung kiểm test/ratchet/traps | Tab Checks của PR starter/d09 trong fork cá nhân |
| Hidden | Chưa có key anchor, hidden variants/traps hoặc kết quả giảng viên | Không tự gán PASS/điểm hidden |

Các đường dẫn src/ trong bảng tính từ gốc repo; tài liệu ở docs/. Report JSON và log đều sinh từ chương trình, không gõ sửa số liệu. Các nhãn đánh dấu rủi ro item kiểm tra, không khẳng định mọi trial mắc lỗi.

## Các ràng buộc trừ điểm

- src/lab8/ giữ nguyên so với repo Day08 gốc giảng viên 034c6c4, bao gồm các TODO của ba shape không dùng cho Day09. Không chép code đã sửa của nhóm Day08.
- Tài liệu gốc Day09, workflow eval-gate, variant/trap/test/CSV/adversarial pack giảng viên giữ nguyên. Source lock còn kiểm 62 tệp Day08 gốc ngoài harness_map (được thêm section eval), chuẩn hóa CRLF/LF khi so source. Tập đường dẫn lab8 cũng phải trùng nguồn gốc.
- Report do runner/script sinh; raw logs được lưu cả hai lần phát hiện thiếu sót.
- Không nới ngưỡng trong cùng eval-set version. Workflow bổ sung dùng base-spec từ PR base, tránh lấy một bản spec đã bị nới trong PR làm chuẩn.
- Nhãn tách khỏi item; v2 giữ đủ v1 và pack.
- Không đưa .env, key, venv, SQLite, trace hay bộ chấm riêng lên Git.

## Lỗi đã sửa trong quá trình triển khai

1. Detection M3 75% vì bỏ sót proposal bị tự trừ trước dù ledger=0; bổ sung code metric proposal, lên 100%.
2. Full suite ban đầu 2 fail vì test Day09 làm bẩn registry SHAPES; sửa fixture của test mới, không đụng test/agent Day08.
3. CI Core ban đầu block vì SHA CRLF/LF khác nhau. Sửa generator LF và thuộc tính Git, sinh lại report bằng script. Không đổi ngưỡng hoặc sửa JSON bằng tay.
4. Job bổ sung dùng nhầm ci_check v1 cho chỉ số dẫn xuất v2. Giữ nguyên checker gốc; compare_reports đối chiếu tất cả aggregate và từng paired row của v2 để xác nhận tái lập.

## Phần còn thuộc người học / giảng viên

Audit judge đã được Nguyễn Mạnh Tường xác nhận trong phiên ngày 17/11/2026. Người học tiếp tục chịu trách nhiệm đọc/giải thích bài và tự nộp URL PR trên LMS trước 12:00 trưa 18/11/2026. PR cũ trên repo Day08 không dùng để nộp. Key năm anchor, vector/variant/trap ẩn và điểm chính thức do giảng viên đối chiếu. Public xanh không được mô tả thành bảo đảm 100 điểm.

Bonus Inspect AI/DeepEval chưa thực hiện; đây là mục ngoài thang chính M0–M7 và không cần để phủ đủ yêu cầu 100 điểm.
