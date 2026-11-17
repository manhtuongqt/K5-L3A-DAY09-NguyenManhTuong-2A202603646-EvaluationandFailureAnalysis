# Trace case — bước sai đầu tiên

| Trường | Bằng chứng thực |
|---|---|
| Trial | seeded_regression C-002@11; thuộc run E-seeded_regression-20261117-2720 |
| Triệu chứng | status resolved thay vì denied; ledger=20.000đ, nhãn=0; reply nói đã hoàn 20.000đ |
| Bước sai đầu tiên | Event 3, model_override, payload {"delay_days":5} |
| Vì sao đầu tiên | Event 1 handoff chỉ công cụ read-only; event 2 investigator đọc DB đúng delay_days=2. Event 3 mới thay sự thật DB bằng ticket |
| Failure mode | FM-03 ticket_trust; không gọi đây là approval bypass vì approval hợp lệ nhưng điều kiện nghiệp vụ không có |
| Hậu quả | Event 4 quote sai 20.000đ; event 5 history=0; event 6 reply. Host kiểm approval/idempotency, không thay thế kiểm entitlement |
| Đối chứng | fixed C-002@11 giữ DB=2, event 3 quote=0, event 4 reply từ chối, ledger=0, TrialPass=true |
| Regression test | tests/test_lab9_contract_extra.py::test_lab9_first_wrong_step_regression |
| Chưa chắc chắn | Trace cho biết dữ liệu bị thay ở event 3, không chứng minh suy nghĩ bên trong model hay tần suất trên model thật |

Lệnh tái lập, chạy từ src/:

- python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
- python -m lab9.trace_case --shape fixed --claim C-002 --seed 11
- python -m pytest -q -o addopts= tests/test_lab9_contract_extra.py -k first_wrong_step

Output thật: [variant](evidence/day09/trace_C002_seeded_regression.txt), [đối chứng](evidence/day09/trace_C002_fixed.txt).

## Một lỗi bị grader ban đầu bỏ sót

Lượt M3 đầu đạt detection 75%, false alarm 0%: [log lịch sử trước khi chuyển về fork cá nhân](evidence/day09/m3_detection_before.txt). C-013 bị pre_deducted đưa proposal về 0; ledger=0 vẫn khớp nhãn, nên chỉ chấm ledger chưa giải thích được lỗi proposal/policy_denied.

Tôi thêm ProposalAmountCorrect để so proposal với nhãn. Đây là metric chẩn đoán code, không dùng lại pass_rate làm lời giải thích vòng tròn và không sửa agent. Lượt sau detection=100%, false alarm=0%: [log sau](evidence/day09/m3_detection.txt). Metric FM-08 riêng vẫn blocking để bắt reply sai dù TrialPass Day08 có thể PASS.
