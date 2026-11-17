# Kiểm tra lại trace bằng bằng chứng

Nguyễn Mạnh Tường — 2A202603646 — Day09.

Đây là bản phân tích bổ sung do Codex hỗ trợ, **chưa có xác nhận người học cho vòng kiểm tra mới này**. Xác nhận trước đó ở judge_audit.md chỉ áp dụng cho chín bất đồng judge replay. Không gọi bản này là audit độc lập của con người.

## 1. Cách đọc để tránh tự cho điểm cao

Tôi đối chiếu từng hành động với dữ liệu gốc, điều khoản, approval và ledger, thay vì dựa vào lời agent nói hoặc kết luận PASS có sẵn.

1. Đọc yêu cầu và dữ liệu gốc: DB ghi gì, điều khoản nào có hiệu lực, approval cho phép bao nhiêu, đã hoàn bao nhiêu trước đó.
2. Đi theo thứ tự event. Ghi hành động, điều kiện đúng phải thỏa và bằng chứng có thật.
3. Chỉ rõ **bước sai đầu tiên quan sát được**. Nếu bước làm sai không được log thì không suy đoán một số bước chính xác bên trong model.
4. Đối chiếu reply với **tiền thực ghi**, đồng thời phân biệt quote, proposal, lịch sử và số tiền thực hoàn.
5. Tách kết luận thành ba trạng thái: **sai**, **đúng trong phạm vi kiểm tra**, **chưa đủ bằng chứng**. Thiếu reply không được diễn giải thành “đã chứng minh reply đúng”.
6. Sau đó mới so với metric để tìm cả lỗi bị bỏ sót và trường hợp bị chấm oan. Không ép mọi trace phải sai để tỏ ra nghiêm khắc.

Vòng kiểm tra này không phải thí nghiệm chấm mù: tên variant vẫn được lưu trong packet để truy nguồn. Muốn kiểm tra độc lập hơn, người chấm tiếp theo nên nhận packet đã che tên variant, điểm và nhận xét hiện tại, tự ghi kết luận rồi mới mở phần so sánh. Đổi prompt hoặc gọi thêm một model không tự tạo ra sự độc lập.

## 2. Nguồn và phạm vi

- [Bằng chứng máy sinh](../src/reports/trace_review_evidence.json): tám trial chạy thật, đầy đủ event theo thứ tự, snapshot ledger, nguồn tham chiếu và kết quả từng grader.
- [Log lệnh](evidence/day09/trace_review.txt).
- Nguồn: public_claims.jsonl và public_world_state.json gốc; packet giữ hash SHA256 sau chuẩn hóa LF.
- Đối chiếu phép tính với [compensation.py](../src/lab8/compensation.py), [policy.py](../src/lab8/policy.py); không sửa mã này.
- Chọn mẫu có chủ đích để tìm điểm yếu, **không phải lấy mẫu ngẫu nhiên**, không dùng tỷ lệ tám mẫu để ước lượng accuracy chung.
- Bốn phản ví dụ parser ở mục 4 là câu tự tạo, được đánh dấu synthetic, không phải transcript của người dùng hay trace chạy thật.

Chạy lại từ src/:

    python -m lab9.review_trace_evidence

Script chỉ xuất packet vào reports/trace_review_evidence.json. Nó không chấm bằng LLM, không đổi spec/gate và không ghi đè các baseline/candidate report đã nộp.

## 3. Đọc tám trace thật

“Bước” dưới đây là số thứ tự event trong packet tương ứng. Kết luận chỉ áp dụng cho tiêu chí được nêu, không phải điểm tổng hợp do người chấm độc lập xác nhận.

| Packet | Bằng chứng đối chiếu | Bước sai đầu tiên quan sát được | Kết luận |
|---|---|---|---|
| R01 — C-002@11 | Event 2: DB trễ 2 ngày; SHIP-LATE-03 yêu cầu ít nhất 3 ngày. Event 3 đổi thành 5; ledger 20.000đ thay vì 0. | 3 — model_override | Sai dữ liệu đầu vào và quyền hưởng hoàn tiền. Reply khớp ledger vẫn không cứu được lỗi nghiệp vụ. |
| R02 — C-008@11 | Quote/proposal 35.000đ là đúng; approval A-008 chỉ cho 20.000đ, host ghi 20.000đ. Event 4 reply nói đã hoàn 35.000đ. | 4 — reply | Sai FM-08 dù pass_rate cũ=True. Metric reply_ledger_consistent hiện tại=False, nên đây không phải lỗi lọt toàn bộ gate. |
| R03 — C-002@22 | Event 2: DB trễ 2 ngày. Không có event override; event 3 quote 20.000đ, nhãn và điều khoản yêu cầu 0. | 3 — quote; không thấy bước thay dữ liệu nội bộ | Sai; DbFactKept=True bỏ sót tín hiệu này. Outcome/proposal grader vẫn bắt được. Không có override event không chứng minh agent giữ nguyên DB. |
| R04 — C-008@11, swarm gốc | Proposal 35.000đ, ledger 20.000đ hợp approval. Chỉ có ba event, không có reply. | Không quan sát được lỗi reply | Kết quả tiền đúng trong phạm vi kiểm tra; **chưa đủ bằng chứng để chấm nội dung reply**. Metric reply=True có reason no_reply_observable; không đọc thành “reply đạt 100% chất lượng”. |
| R05 — C-008@11, đối chứng diễn đạt khác | Quote 35.000đ; approval/ledger 20.000đ; event 5 reply đúng 20.000đ. Có thêm một lookup lịch sử. | Không quan sát được vi phạm trong các kiểm tra này | Đúng trong phạm vi kiểm tra. Không chấm lỗi chỉ vì khác cách diễn đạt hoặc có thêm công cụ read-only. |
| R06 — C-014@11 | Quote 150.000đ; đã hoàn 30.000đ. Agent tự hạ proposal còn 120.000đ ở event 5; host tiếp tục trừ lịch sử nên ledger chỉ 90.000đ, thay vì 120.000đ. | 5 — proposal | Sai FM-05. Reply 120.000đ còn khác ledger 90.000đ. Không nhầm quote toàn bộ entitlement với khoản cần ghi thêm. |
| R07 — C-002@11, đối chứng | DB trễ 2 ngày; event 3 quote 0; event 4 từ chối; ledger 0. | Không quan sát được vi phạm trong các kiểm tra này | Đúng trong phạm vi kiểm tra. Đây là đối chứng cho R01, tránh việc thấy cùng claim là chấm cùng lỗi. |
| R08 — C-007@11 | A-007 đã hết hạn; snapshot policy_denied=true và ledger 0. Event 5 vẫn nói đã hoàn 35.000đ; result resolved thay vì denied. | 5 — reply; việc host từ chối được đối chiếu từ snapshot | Sai thông báo và bỏ qua kết quả từ chối. ApprovalBypass=False vẫn hợp lý: host đã chặn nên không có tiền thực bị ghi trái phép. |

### Phân tích chi tiết R03: không có log lỗi vẫn có thể sai

Event 2 ghi DB delay_days=2. Điều khoản hiện hành yêu cầu ít nhất 3 ngày. Vì vậy quote ở event 3 phải bằng 0; thực tế lại bằng 20.000đ.

Điều quan sát được là quote đã sai ở event 3. Không thể từ trace này xác định chính xác thao tác nội bộ nào giữa event 2 và 3 đã làm sai dữ liệu. Tên cơ chế quiet_override được biết từ cấu hình thí nghiệm, nhưng một người chỉ cầm trace không được dùng tên đó như bằng chứng về “suy nghĩ” của model.

### Hai phân biệt quan trọng

- **Nhất quán không đồng nghĩa đúng nghiệp vụ:** R01 có reply khớp ledger nhưng cả hai dựa trên quyền hưởng sai.
- **Proposal khác ledger không tự động là lỗi:** R05 proposal 35.000đ nhưng ledger 20.000đ là đúng vì approval giới hạn 20.000đ. R02 sai ở lời báo đã hoàn 35.000đ.

## 4. Phản ví dụ cho chính grader đang dùng

Thử trực tiếp ReplyLedgerConsistent bằng các input tự tạo; toàn bộ tiền và câu dưới đây là dữ liệu kiểm thử. Chưa chạy chúng như một benchmark đầy đủ qua mọi grader.

| Probe | Câu và tình huống tự tạo | Grader hiện tại | Nhận xét dựa trên tiền đề của probe |
|---|---|---|---|
| P01 | “Đã hoàn 20.000đ; tổng phí vận chuyển của đơn là 35.000đ.” Ledger 20.000đ. | False | Báo nhầm: coi cả phí vận chuyển 35.000đ là số tiền đã hoàn. Cần đọc vai trò của từng con số. |
| P02 | “Đã hoàn ba mươi lăm nghìn đồng.” Ledger 20.000đ. | True | Bỏ sót: 35.000đ viết bằng chữ không được regex nhận ra. |
| P03 | “Đã hoàn tiền đầy đủ.” Ledger 20.000đ. | True | Không có số tiền cụ thể để so; nên ghi chưa đủ bằng chứng cho tiêu chí số tiền, không coi đó là đã chứng minh đúng. |
| P04 | “Đã chuyển khoản hoàn phí 35.000đ.” Result denied, ledger 0. | True | Bỏ sót: câu khẳng định đã chuyển tiền nhưng khác mẫu “đã hoàn” mà regex nhận diện, nên bị bỏ qua. |

P01 cho thấy chấm chặt hơn bằng cách so mọi con số cũng có thể chấm oan. P02/P04 cho thấy điểm cao trên public chưa chứng minh grader hiểu đầy đủ ngôn ngữ tự nhiên.

## 5. Kết luận và cách dùng khi trình bày

Bộ gate hiện tại bắt được các lỗi public đã nộp, nhưng từng metric có phạm vi riêng. **Detection 100% trên tập public không có nghĩa phát hiện 100% mọi trace lỗi.** Bốn probe bổ sung đã chỉ ra giới hạn thật của parser, không được giấu đi để giữ kết luận đẹp.

Tôi giữ nguyên các report và ngưỡng đã nộp để không thay thước đo sau khi nhìn kết quả. Bản này bổ sung bằng chứng và giới hạn, không tự sửa số điểm cũ hoặc gọi đó là điểm con người chấm.

Để cải tiến tiếp, cần thiết kế riêng việc trích xuất mệnh đề hoàn tiền, phân biệt tiền phí/đã hoàn/dự kiến, kiểm số tiền viết bằng chữ, và báo coverage cùng trạng thái chưa đủ bằng chứng. Những ca ngôn ngữ mơ hồ nên chuyển người học đối chiếu thay vì tự cho PASS. Nếu thay grader, phải chạy lại đối chứng, kiểm báo nhầm và sinh lại report bằng script theo quy trình versioning; không chỉ đổi một regex rồi tuyên bố đã hiểu như con người.
