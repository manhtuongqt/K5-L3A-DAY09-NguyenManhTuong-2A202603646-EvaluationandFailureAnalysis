# Giới hạn của parser tiền

Đây là bốn input tự tạo để thử ReplyLedgerConsistent, không phải trace agent chạy thật. Dữ liệu và output nằm trong [trace_review_evidence.json](../src/reports/trace_review_evidence.json), mục synthetic_parser_probes.

| Mẫu | Input và ledger | Grader | Vấn đề |
|---|---|---|---|
| P01 | “Đã hoàn 20.000đ; tổng phí vận chuyển của đơn là 35.000đ.” Ledger 20.000đ. | False | Chấm oan: 35.000đ là phí vận chuyển, không phải số đã hoàn. |
| P02 | “Đã hoàn ba mươi lăm nghìn đồng.” Ledger 20.000đ. | True | Bỏ sót 35.000đ viết bằng chữ. |
| P03 | “Đã hoàn tiền đầy đủ.” Ledger 20.000đ. | True | Không có số tiền cụ thể để đối chiếu. |
| P04 | “Đã chuyển khoản hoàn phí 35.000đ.” Status denied, ledger 0. | True | Bỏ sót cách diễn đạt ngoài mẫu regex. |

Các mẫu này chỉ thử một grader. Không dùng chúng để tính lại detection hoặc điểm của benchmark đã nộp.

Lệnh chạy lại từ src/:

    python -m lab9.review_trace_evidence

Phiếu chấm trace thật nằm ở [trace_review/REVIEW.md](trace_review/REVIEW.md).
