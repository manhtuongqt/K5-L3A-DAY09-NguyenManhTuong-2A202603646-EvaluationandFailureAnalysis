# Eval card — Day09 Core

Bài cá nhân — Nguyễn Mạnh Tường — 2A202603646 — L3A.

## Phiên bản và nguồn

- Nền agent: repo Day08 gốc của giảng viên, commit 034c6c421c198dae67a9211d15e2587d5a378972; src/lab8/ giữ nguyên, không dùng bài nhóm Day08.
- Fork Day09 cá nhân từ starter d1b9471540727d693c9eb392667b9f0d8a998bf5; import nguồn gốc tại commit 0949ed9.
- Eval v1: SHA 2720d20ea159; 14 item × 5 seed 11/22/33/44/55; labels_v1.json tách riêng.
- metric_spec_version=1.0; grader trong lab9/graders.py, thống kê trong lab9/stats.py.
- Môi trường chạy local: Python 3.11.9, pydantic-evals 2.68.0, MockLLM; judge replay, không gọi model API.
- Code/grader commit và kết quả CI cuối được ghi trong bảng đối chiếu Day09 sau khi chốt PR.

## Kết quả v1

| Metric | Baseline swarm | fixed | seeded_regression | Quy định |
|---|---:|---:|---:|---|
| approval_bypass | 0 | 0 | 0 | Blocking max 0 |
| secret_leak | 0 | 0 | 0 | Blocking max 0 |
| refund_amount_correct | 0.9857 | 1.0000 | 0.8571 | Blocking min 0.95 + no significant drop |
| pass_rate | 0.9857 | 1.0000 | 0.7143 | Blocking min 0.85 + no significant drop |
| reply_ledger_consistent | 1.0000 | 1.0000 | 0.7857 | Blocking min 1 |
| db_fact_kept | 0.9857 | 1.0000 | 0.9286 | Theo dõi min 0.95 |
| proposal_amount_correct | 0.9857 | 1.0000 | 0.7857 | Chẩn đoán min 0.95, không blocking |
| pass_5 | 0.9286 | 1.0000 | 0.7143 | Theo dõi min 0.80 |
| cost_per_success | 49.5670 | 48.7157 | 81.2020 | Chi phí mô phỏng, theo dõi tăng tối đa 10% |

Nguồn máy sinh: [baseline](../src/reports/baseline_v1.json), [fixed](../src/reports/eval_fixed.json), [regression](../src/reports/eval_seeded_regression.json). Run ID lần lượt E-swarm-20261117-2720, E-fixed-20261117-2720, E-seeded_regression-20261117-2720.

Delta pass_rate regression − baseline = −0.271; paired percentile CI 95% [−0.500, −0.057]. Cặp bootstrap là trung bình mỗi item qua năm seed, không phải 70 quan sát độc lập. Cấu hình 1000 resample, rng=2027. fixed và swarm PR merge; regression block vì refund_amount_correct, pass_rate, reply_ledger_consistent. [Log gate](evidence/day09/m4_gate_seeded_regression.txt).

## Judge, trace và phạm vi

Tone đạt κ=.757, P=.857, R=.8 trên replay; helpful bị loại κ=.375, R=.3 dù P=1. [Audit đã được người học đối chiếu](judge_audit.md). Tiền/phê duyệt không giao judge.

[Trace case](trace_case.md) chỉ rõ C-002 event 3 là bước sai đầu tiên, có test đối chứng. Chủ trì gate: Nguyễn Mạnh Tường. Exit 1 là không merge; cần tìm nguyên nhân, sửa lớp eval đúng phạm vi và chạy lại. Không hạ ngưỡng để lấy build xanh.

Đã chạy lại lỗi duy nhất trong baseline v1: swarm C-002@55, event 3 đổi DB delay từ 2 thành 5. [TR01](trace_review/TR01.md) có trace, hash và ledger; [TR10](trace_review/TR10.md) là fixed cùng seed. Bộ [13 phiếu review](trace_review/REVIEW.md) gồm chín lỗi và bốn đối chứng/trường hợp thiếu dữ liệu đã được Nguyễn Mạnh Tường xác nhận ngày 17/11/2026. TR12 vẫn thiếu dữ liệu reply. Điểm benchmark giữ nguyên.

Pilot ở đây là đánh giá offline bài toán claim một đơn, approvals và mức tiền theo fixture. Chưa cho phép tác động tiền thật; chưa đo người dùng thật.

## Giới hạn

MockLLM deterministic không đại diện model thật. V1 chỉ 14 item, CI rộng; dữ liệu replay đã public không phải held-out mới. Metric reply_ledger_consistent kiểm tính nhất quán của số tiền quan sát được: swarm gốc không có reply event nên 1.0 không chứng minh toàn bộ trả lời đúng/đủ. Tiền trong ledger và proposal được đo riêng.

Đổi eval set phải tăng eval_set_version và chạy baseline mới. Đổi spec cần version/giải thích, không nới threshold trong cùng eval-set version; code giữ ratchet. Không tuyên bố điểm hidden khi chưa có kết quả giảng viên.


## V2 — slices, reliability và integrity

Eval set v2 SHA 67dc2eec100f, 28 item × 5 seed, gồm đủ 14 public và 14 adversarial; labels_v2.json tách riêng. Spec 2.0 giữ floor pass_rate=.85 và refund_amount_correct=.90 của starter. Không nới ngưỡng cùng version. Mã gate/grader, script kiểm nguồn và test bổ sung được theo dõi trên PR starter/d09 của fork Day09 cá nhân; mọi report được chạy lại trên nguồn agent gốc.

| Shape | Run ID | Pass rate | pass^5 | Gate |
|---|---|---:|---:|---|
| swarm | E-swarm-20261117-67dc | .9786 | .8929 | Merge khi tự so baseline |
| fixed | E-fixed-20261117-67dc | 1 | 1 | Merge |
| honest_refactor | E-honest_refactor-20261117-67dc | 1 | 1 | Merge |
| seeded_regression | E-seeded_regression-20261117-67dc | .6429 | .6429 | Block |
| slice_regression | E-slice_regression-20261117-67dc | .9357 | .8929 | Block duy nhất qua money_movement |
| flaky_regression | E-flaky_regression-20261117-67dc | .9143 | .5714 | Block pass_hat_5, pass_rate CI và money_movement |

Nguồn: reports/baseline_v2.json và eval_*_v2.json; [log mutation](evidence/day09/m7_mutation.txt). Cả fixed và honest_refactor không bị báo nhầm; chi phí honest_refactor tăng chỉ cảnh báo, không chặn vì đây là system metric không blocking.

### Ngưỡng và slice

- A/A dùng seeds 11/22/33/44/55 và 66/77/88/99/110: mọi Δ metric=0. [Output](evidence/day09/m6_aa.txt).
- Floor pass_hat_5=.80, thấp hơn mức reference .8929 và khoảng biến động A/A bằng 0; được cấu hình trước khi chạy scorecard, không tối ưu sau theo variant. A/A xác nhận hợp lý trên MockLLM chứ không chứng minh floor tối ưu cho model thật.
- money_movement: min=.90, no_significant_drop, blocking; có 12 item. slice_regression chỉ đạt .85 trong slice này, trong khi pass_rate chung .9357 vượt sàn và CI chung chạm 0.
- adversarial: min=.85, no_significant_drop, blocking; có 14 item.
- denial: min=.90, no_significant_drop, blocking; có 11 item.
- pass@5 của flaky vẫn=1 nhưng pass^5=.5714; chỉ số “có ít nhất một lần đúng” che mất sự thiếu ổn định.

### Integrity và ratchet

Bốn trap public đều bị gate chặn exit 1: None/NaN, bỏ dòng fail, chọn seed đẹp, nới spec. Lệnh traps tổng exit 0 vì không trap nào lọt. [Log](evidence/day09/m7_traps.txt). Test bổ sung còn kiểm dòng trùng thay dòng, evaluator_failures trên run xanh, đổi slice, aggregate mâu thuẫn, và cơ chế lỗi không để event override.

Ratchet cần base-spec tin cậy. Workflow gốc được giữ nguyên; workflow bổ sung day09-contract-and-integrity lấy spec từ commit base của PR, chạy host tests và test Day09, kiểm source và trap. Chỉ giữ metric/slices trong PR không đủ chứng minh không ai đã nới threshold.

### Giới hạn cỡ mẫu

Năm seed không bảo đảm phát hiện ổn định một lỗi có xác suất 1/3 hoặc thấp hơn, hay lỗi phụ thuộc những tình huống chưa có trong tập. Công tắc rare public bật khi seed chia hết cho 3; với năm seed hiện tại, nó bật đúng một seed. Không được đồng nhất cơ chế modulo của fixture với xác suất thật trên model ngoài đời. CI bootstrap trên ít item vẫn rộng; chưa chứng minh chất lượng production.

Key anchor và hidden variants/traps không public. Các probe bổ sung chỉ kiểm hợp đồng, không thay thế kết quả chấm ẩn.
