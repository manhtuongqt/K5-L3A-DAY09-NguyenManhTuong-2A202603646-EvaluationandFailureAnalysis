# Trace để review và chấm

TR01 là lượt lỗi duy nhất trong baseline v1 đã nộp: swarm, C-002@55. Đã chạy lại và so từng metric với dòng baseline.
TR02–TR09 dùng công tắc gài lỗi có sẵn của đề. TR10–TR13 là đối chứng hoặc trường hợp thiếu dữ liệu. Tất cả đều chạy trên mô phỏng của lab.
Nguyễn Mạnh Tường đã review TR01–TR13 và đồng ý toàn bộ nhận xét ngày 2026-11-17. Không yêu cầu sửa. Nhận xét ban đầu có AI hỗ trợ; phần người chấm đã được ghi theo xác nhận trong phiên.

| Mẫu | Claim@seed | FM đề xuất | Bước sai | Bạn đã review |
|---|---|---|---:|---|
| [TR01](TR01.md) | C-002@55 | FM-03 | 3 | [x] |
| [TR02](TR02.md) | C-001@11 | FM-01 | 1 | [x] |
| [TR03](TR03.md) | C-007@11 | FM-02 | 4 | [x] |
| [TR04](TR04.md) | C-014@11 | FM-04 | 4 | [x] |
| [TR05](TR05.md) | C-014@11 | FM-05 | 5 | [x] |
| [TR06](TR06.md) | C-006@11 | FM-06 | 3 | [x] |
| [TR07](TR07.md) | C-001@11 | FM-07 | 4 | [x] |
| [TR08](TR08.md) | C-008@11 | FM-08 | 4 | [x] |
| [TR09](TR09.md) | C-002@22 | FM-03 | 3 | [x] |
| [TR10](TR10.md) | C-002@55 | đối chứng / chưa đủ dữ liệu | — | [x] |
| [TR11](TR11.md) | C-008@11 | đối chứng / chưa đủ dữ liệu | — | [x] |
| [TR12](TR12.md) | C-008@11 | đối chứng / chưa đủ dữ liệu | — | [x] |
| [TR13](TR13.md) | C-005@11 | đối chứng / chưa đủ dữ liệu | — | [x] |

## Xác nhận

Đã xác nhận 13/13 ca: chín ca lỗi, ba đối chứng không thấy lỗi, một ca thiếu dữ liệu reply (TR12).
TR12 vẫn giữ kết luận chưa đủ bằng chứng; không chuyển thành reply đúng.
Nguồn xác nhận: [confirmation.json](confirmation.json). Không có điểm số do người học cung cấp.

Không cần cho điểm cao hoặc thấp theo điểm agent. Ví dụ: proposal 35.000đ và ledger 20.000đ có thể đúng do approval giới hạn 20.000đ.
Lỗi parser tự tạo P01–P04 ở bản audit trước không được tính vào 13 trace này.

Chạy lại từ src/: python -m lab9.build_trace_review
Script dừng nếu bất kỳ phiếu hoặc bảng review nào đã được sửa, để giữ phần bạn chấm.
