# Trace để review và chấm

TR01 là lượt lỗi duy nhất trong baseline v1 đã nộp: swarm, C-002@55. Đã chạy lại và so từng metric với dòng baseline.
TR02–TR09 dùng công tắc gài lỗi có sẵn của đề. TR10–TR13 là đối chứng hoặc trường hợp thiếu dữ liệu. Tất cả đều chạy trên mô phỏng của lab.
Nhận xét và FM hiện tại là đề xuất có AI hỗ trợ. Cột chấm của người học đang để trống.

| Mẫu | Claim@seed | FM đề xuất | Bước sai | Bạn đã review |
|---|---|---|---:|---|
| [TR01](TR01.md) | C-002@55 | FM-03 | 3 | [ ] |
| [TR02](TR02.md) | C-001@11 | FM-01 | 1 | [ ] |
| [TR03](TR03.md) | C-007@11 | FM-02 | 4 | [ ] |
| [TR04](TR04.md) | C-014@11 | FM-04 | 4 | [ ] |
| [TR05](TR05.md) | C-014@11 | FM-05 | 5 | [ ] |
| [TR06](TR06.md) | C-006@11 | FM-06 | 3 | [ ] |
| [TR07](TR07.md) | C-001@11 | FM-07 | 4 | [ ] |
| [TR08](TR08.md) | C-008@11 | FM-08 | 4 | [ ] |
| [TR09](TR09.md) | C-002@22 | FM-03 | 3 | [ ] |
| [TR10](TR10.md) | C-002@55 | đối chứng / chưa đủ dữ liệu | — | [ ] |
| [TR11](TR11.md) | C-008@11 | đối chứng / chưa đủ dữ liệu | — | [ ] |
| [TR12](TR12.md) | C-008@11 | đối chứng / chưa đủ dữ liệu | — | [ ] |
| [TR13](TR13.md) | C-005@11 | đối chứng / chưa đủ dữ liệu | — | [ ] |

## Chấm từng mẫu

1. Mở trace và evidence.json. Đọc dữ liệu gốc được dẫn trong mẫu.
2. Kiểm tra bước được nêu có thực sự sai không. Nếu chưa đủ dữ liệu, ghi rõ chỗ thiếu.
3. Điền kết luận, FM, bước sai và lý do ở mục Bạn review. Đánh dấu lại trong bảng này.

Không cần cho điểm cao hoặc thấp theo điểm agent. Ví dụ: proposal 35.000đ và ledger 20.000đ có thể đúng do approval giới hạn 20.000đ.
Lỗi parser tự tạo P01–P04 ở bản audit trước không được tính vào 13 trace này.

Chạy lại từ src/: python -m lab9.build_trace_review
Script dừng nếu bất kỳ phiếu hoặc bảng review nào đã được sửa, để giữ phần bạn chấm.
