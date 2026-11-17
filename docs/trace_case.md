# Trace case — lỗi trong swarm gốc

## C-002, seed 55

Đây là lượt lỗi duy nhất trong baseline v1: 69/70 trial đạt. Đã chạy lại và so từng metric với dòng C-002@55 của baseline.

| Mục | Bằng chứng |
|---|---|
| Trace | [TR01.trace.json](../src/reports/trace_cases/TR01.trace.json), run R-swarm-C-002-s55 |
| Dữ liệu đúng | Event 2: DB delay_days=2. SHIP-LATE-03 chỉ áp dụng khi trễ ít nhất 3 ngày. |
| Bước sai đầu tiên | Event 3, /events/2: model_override đặt delay_days=5. |
| Hậu quả | Event 4 quote 20.000đ; ledger ghi 20.000đ. Nhãn yêu cầu proposal=0, refund=0, status=denied. |
| FM | FM-03: tin ticket thay cho DB. Không gọi đây là approval bypass; approval của ca này hợp lệ. |
| Đối chứng | [TR10](trace_review/TR10.md), fixed C-002@55: quote 0, ledger 0, denied. |
| Test | tests/test_lab9_trace_evidence_extra.py::test_lab9_original_swarm_failure |
| Phần bạn chấm | [TR01.md](trace_review/TR01.md), mục Bạn review |

Lệnh chạy test từ src/:

    python -m pytest -q -m student -o addopts= tests/test_lab9_trace_evidence_extra.py

## Các lỗi khác

[trace_audit.md](trace_audit.md) liệt kê chín ca lỗi và bốn đối chứng/trường hợp thiếu dữ liệu. Mỗi ca dẫn thẳng tới event, ledger và dữ liệu gốc.

Ca seeded_regression C-002@11 trước đó vẫn được lưu ở [log](evidence/day09/trace_C002_seeded_regression.txt), có test test_lab9_first_wrong_step_regression. Đó là variant gài lỗi của đề; không nhầm với swarm gốc C-002@55.

## Grader từng bỏ sót gì?

- C-008: ledger 20.000đ nhưng reply 35.000đ. TrialPass cũ vẫn PASS; metric FM-08 bắt được.
- C-013: proposal bị trừ trước còn 0; chỉ nhìn ledger sẽ bỏ sót. Thêm ProposalAmountCorrect để chẩn đoán.
- Detection public: [trước 75%](evidence/day09/m3_detection_before.txt), [sau 100%](evidence/day09/m3_detection.txt). Không suy ra phát hiện mọi lỗi ngoài bộ public.

Chỉ ghi bước quan sát được. Không có log về thao tác nội bộ thì không tự đặt thêm bước hoặc nguyên nhân.
