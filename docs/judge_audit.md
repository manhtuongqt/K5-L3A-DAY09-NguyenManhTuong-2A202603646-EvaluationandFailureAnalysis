# Judge audit — Day09

Nguồn: hai CSV replay nguyên bản của giảng viên. FAIL là lớp dương.

| Tiêu chí | n | TP/FP/FN/TN | κ | Precision | Recall | Quyết định |
|---|---:|---|---:|---:|---:|---|
| tone_ok | 100 | 24/4/6/66 | 0.757 | 0.857 | 0.800 | Đạt floors trên replay |
| helpful | 100 | 9/0/21/70 | 0.375 | 1.000 | 0.300 | Loại khỏi release gate |

Floors: κ≥0.6, P≥0.8, R≥0.7. Tone exit 0; helpful exit 1 đúng dự kiến. Rogan–Gladen hiệu chỉnh tỷ lệ lỗi quan sát 0.28 (tone) và 0.09 (helpful) về 0.30; hiệu chỉnh tỷ lệ không sửa các quyết định sai từng ca.

## Audit các bất đồng

Bản phân tích được Codex hỗ trợ đọc dữ liệu và soạn lý do. Nguyễn Mạnh Tường đã đối chiếu và xác nhận toàn bộ 9 nhận xét trong phiên làm việc ngày 17/11/2026: “ok mình xác nhận là ổn, pass nhé”. Giữ nguyên CSV, không sửa nhãn để làm đẹp calibration.

| Case | Reply/bằng chứng | Human / judge | Nhận xét | Hành động sửa rubric |
|---|---|---|---|---|
| H-008 | “Em đã hoàn tiền cho anh rồi nha, anh check giúp em.” | FAIL / PASS | Theo chuẩn CS trong note public, em/nha quá suồng sã; đồng ý human | Ghi xưng hô anh/chị, tránh nha/check thân mật; thêm ví dụ âm tính dù có ý hỗ trợ |
| H-017 | “Dạ, bạn ơi … rồi nha.” | FAIL / PASS | Có Dạ không đủ chứng minh lịch sự; đồng ý human theo ngữ cảnh note | Chấm xưng hô theo đối tượng, không chấm riêng từ khóa Dạ |
| H-029 | “Dạ, vui lòng chờ … không cần nhắn thêm.” | FAIL / PASS | Phần cuối có giọng ra lệnh; đồng ý human | Thêm ví dụ mở đầu lịch sự nhưng nội dung áp đặt |
| H-042 | “Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ.” | PASS / FAIL | Ngắn vẫn đủ ý và lịch sự, không bắt buộc xin lỗi mọi câu; đồng ý human | Tách tiêu chí lịch sự khỏi mẫu xin lỗi cố định |
| H-051 | “Dạ, LogiX đã refund 90.000đ … ạ.” | PASS / FAIL | Note CS cho phép từ refund; đồng ý human | Nêu thuật ngữ được phép, không cấm mọi từ tiếng Anh |
| H-063 | “đã hoàn 20.000đ và sẽ hoàn thêm …” | FAIL / PASS | Note public nêu hứa ngoài kết quả; đồng ý nhãn, nhưng còn là ranh giới tone/helpfulness | Tách văn phong khỏi lời hứa vượt quyền; tiền/hành động chấm bằng code |
| H-070 | Reply hoàn tiền kèm hai emoji cười | FAIL / PASS | Không hợp ngữ cảnh khiếu nại theo note public; đồng ý human | Nêu quy tắc emoji, không coi thân thiện là luôn đạt |
| HL-015 | Reply 55.000đ; note ledger 40.000đ | FAIL / PASS | Sai tiền dù lịch sự; đồng ý human theo note | Chấm bằng code, đối chiếu reply/ledger FM-08 |
| HL-020 | Reply 90.000đ; note ledger 120.000đ | FAIL / PASS | Bỏ sót sai tiền; đồng ý human theo note | Tách correctness khỏi văn phong |

Reply đầy đủ và nhãn gốc trong src/data/eval/judge_*_public.csv.

H-081 có human=PASS, judge=FAIL nhưng note nói nhãn người sai do đọc nhầm ticket. Chỉ nhìn reply không đủ tái dựng ngữ cảnh; không tự sửa nhãn. Cần đọc ticket nguồn trước khi quyết định version nhãn mới.

## Kết luận

Helpful không đạt κ/recall: precision=1 không bù 21 false negative. Tone chỉ đạt cho tiêu chí đã calibration trên replay. Tiền và phê duyệt luôn chấm bằng code. Nhãn người cũng có thể sai; audit cần lý do. κ không xác định phải FAIL. Bộ public không phải held-out mới và chưa đo người dùng/model thật.

Người đối chiếu: Nguyễn Mạnh Tường. Trạng thái: đã xác nhận; không đổi nhãn hoặc nhận xét nào.
