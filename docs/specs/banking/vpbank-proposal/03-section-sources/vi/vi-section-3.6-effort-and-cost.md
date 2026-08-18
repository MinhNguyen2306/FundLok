# 3.6 Dự toán khối lượng công việc và chi phí

*[NỘI DUNG — Edward và Huy. Bản thảo tiếng Anh để rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

Mục này dự toán khối lượng công việc kỹ thuật đứng sau các Mục 3.3, 3.4 và 3.5, nêu rõ những phần chi phí do FundLok chịu, và trình bày tải vận hành thường xuyên mà thoả thuận này tạo ra sau khi đi vào hoạt động.

**Về các dự toán dành cho VPBank.** Các số liệu người-ngày đối với các thành phần của VPBank là dự toán mang tính tham khảo do FundLok đưa ra, nhằm giúp hai bên xác định quy mô thảo luận và trình tự triển khai công việc. Đây không phải là tuyên bố về chi phí, nguồn lực hay đơn giá nội bộ của VPBank, và **không đặt bất kỳ giá trị tiền tệ nào cho khối lượng công việc của VPBank** — VPBank tự định giá phần xây dựng của mình. Ở những thành phần mà khối lượng công việc phụ thuộc vào việc một sản phẩm hiện có có thể được cấu hình hay bắt buộc phải xây mới, cả hai số liệu đều được nêu: số thấp hơn là hướng cấu hình, số cao hơn là hướng xây mới.

**Về các dự toán dành cho FundLok.** Các số liệu này phản ánh tốc độ triển khai đã được quan sát trên thực tế của chính FundLok với một đội gồm hai kỹ sư — Edward Wong và Phat — cả hai đều làm việc với sự hỗ trợ của phát triển có AI. Người rà soát khi so chiếu các số liệu này với đơn giá ngày công thông thường cần lưu ý giả định đó một cách rõ ràng: các con số mô tả tốc độ ra sản phẩm của chính đội ngũ này, được minh chứng bằng việc sổ sách ghi kép và bộ máy định giá tín dụng đều đã được đặc tả, xây dựng, kiểm thử và hợp nhất trong vòng hai tháng vừa qua. Đây không phải là tuyên bố rằng khối lượng công việc là nhỏ.

Toàn bộ số liệu là dự toán nội bộ của FundLok, lập ngày 4 August 2026. Một người-ngày là một kỹ sư làm việc trong một ngày làm việc.

---

## 3.6.1 VPBank — Giai đoạn 1

| Mã | Thành phần | Người-ngày, hướng cấu hình | Người-ngày, hướng xây mới | FundLok chịu chi phí hoặc đồng tài trợ |
|---|---|---|---|---|
| A1 | Tài khoản hạn chế mục đích sử dụng cho từng khoản vay | 2 | 15 | Không — sản phẩm của ngân hàng |
| A2 | Danh sách tài khoản đích được phép do ngân hàng cưỡng chế thực thi | 3 | 20 | **Đồng tài trợ — xem 3.6.4** |
| A2a | Dung lượng danh sách tài khoản đích — 12 mục cho mỗi tài khoản, 700 mục trên toàn danh mục | 1 | 8 | Không |
| A3 | Sửa đổi danh sách tài khoản đích có kiểm soát | 1 | 3 | Không |
| A4 | Cách đặt tên tài khoản | 0.5 | 0.5 | Không |
| A5 | Quy trình mở và đóng tài khoản theo lô | 2 | 2 | Không — thiết kế quy trình |
| A6 | Không thấu chi, không hạn mức tín dụng, không bù trừ | 0.5 | 0.5 | Không |
| B1 | Kênh gửi lệnh thanh toán theo lô an toàn | 1 | 1 | Không — kênh hiện có |
| B2 | Phê duyệt bởi hai người | 1 | 1 | Không — quyền hạn hiện có |
| B3 | Xác nhận nhận lô và kết quả theo từng dòng | 1 | 3 | Không |
| B4 | Mã lý do từ chối ở cấp từng dòng | 1 | 2 | Không |
| B5 | Chống trùng lặp lệnh | 4 | 10 | **Đồng tài trợ — xem 3.6.4** |
| B6 | Các lệnh chuyển tiền thất bại vẫn nằm trong tài khoản ký quỹ | 0.5 | 0.5 | Không |
| C1 | Sao kê hằng ngày ở định dạng máy đọc được | 1 | 3 | Không |
| C2 | Mã nhận dạng giao dịch ổn định | 1 | 5 | Không |
| C3 | Bảo toàn thông tin bên chuyển tiền và toàn bộ nội dung tham chiếu | 1 | 6 | Không |
| C4 | Cung cấp số dư hằng ngày | 0.5 | 0.5 | Không |
| C5 | Truy xuất sao kê theo khoảng thời gian | 1 | 2 | Không |
| D1 | Thu nợ qua VietQR vào tài khoản ký quỹ | 1 | 3 | Không |
| D2 | Chuyển tiếp nguyên vẹn nội dung tham chiếu trên VietQR | 1 | 6 | Không |
| D3 | Tài khoản ảo theo từng bên trả tiền — không bắt buộc trong Giai đoạn 1 | 15 | 25 | **Đồng tài trợ — xem 3.6.4** |
| D4 | Thông báo ghi có theo thời gian thực | Hoãn sang Giai đoạn 2 | Hoãn sang Giai đoạn 2 | Không áp dụng |
| D5 | Năng lực phân bổ nội bộ hằng ngày — chỉ theo Phương án B | 2 | 18 | **Đồng tài trợ — xem 3.6.4** |
| E1 | Người dùng định danh, phân tách quyền hạn | 1 | 1 | Không — quyền hạn hiện có |
| E2 | Thu hồi quyền hạn | 0.5 | 0.5 | Không |
| E3 | Vết kiểm toán phía ngân hàng | 0.5 | 0.5 | Không |
| E4 | Truyền dữ liệu được mã hoá | 0.5 | 0.5 | Không |
| E5 | Thẩm định khách hàng (CDD) của chính VPBank | Quy trình hiện có | Quy trình hiện có | Không |

**Tổng Giai đoạn 1.** Không tính tài khoản ảo theo từng bên trả tiền (không bắt buộc): **29.5 người-ngày theo hướng cấu hình, 112.5 theo hướng xây mới.** Nếu tính cả thành phần này: 44.5 và 137.5.

D5 chỉ áp dụng nếu Phương án B của Mục 1.8 được lựa chọn. Theo Phương án A, các số liệu là 27.5 và 94.5, không tính tài khoản ảo.

Khoảng chênh lệch giữa hai hướng gần như hoàn toàn do hai hạng mục quyết định. A1 và A2 cộng lại là 5 người-ngày nếu sản phẩm tài khoản phong toả hiện có của VPBank có thể được cấu hình, và là 35 nếu không thể — một khoảng dao động 30 người-ngày, phụ thuộc vào duy nhất câu hỏi nêu tại Mục 3.3.2. **Việc trả lời câu hỏi đó có giá trị đối với công tác lập kế hoạch của quan hệ đối tác này lớn hơn bất kỳ hạng mục nào khác trong đề xuất này.**

---

## 3.6.2 VPBank — Giai đoạn 2 (hoãn lại)

Ghi nhận để đầy đủ. Không bắt buộc đối với chương trình thử nghiệm (pilot), và chỉ được kích hoạt bởi ngưỡng khối lượng nêu tại Mục 3.4.

| Mã | Thành phần | Người-ngày, mức thấp | Người-ngày, mức cao | Ghi chú |
|---|---|---|---|---|
| P1 | API lệnh thanh toán | 15 | 25 | Có khả năng nằm trong phạm vi triển khai Circular 64 của VPBank |
| P2 | Truy vấn trạng thái lệnh thanh toán | 5 | 10 | Có khả năng nằm trong phạm vi triển khai đó |
| P3 | Chống trùng lặp lệnh được thực thi ở cấp API | 4 | 8 | Giảm nếu B5 đã được xây dựng trong Giai đoạn 1 |
| P4 | Thông báo ghi có đến theo thời gian thực | 10 | 18 | Thành phần cải thiện trải nghiệm của các bên nhiều nhất |
| P5 | Truy vấn số dư và sao kê theo yêu cầu | 6 | 12 | Có khả năng nằm trong phạm vi triển khai đó |
| P6 | Mở và đóng tài khoản tự động | 8 | 15 | — |
| P7 | Tài khoản ảo theo từng bên trả tiền ở quy mô lớn | 15 | 25 | Không phát sinh thêm nếu đã được triển khai dưới dạng D3 trong Giai đoạn 1 |
| P8 | Cấp quyền và sự đồng ý truy cập API dựa trên token | 6 | 12 | Có khả năng nằm trong phạm vi triển khai đó |
| P9 | Tài khoản riêng cho từng bên | 12 | 22 | Chỉ áp dụng nếu triển khai theo Phương án A rồi sau đó chuyển sang Phương án B |
| P10 | Phân bổ nội bộ theo lô ở quy mô lớn | 12 | 20 | Chỉ theo Phương án B; giảm tải xử lý cho chính VPBank |

**Tổng Giai đoạn 2.** Không tính P9 và P10: **69 đến 125 người-ngày.** Tính cả hai hạng mục: **93 đến 167.**

Một phần đáng kể của P1, P2, P5 và P8 là năng lực ngân hàng mở thông thường mà VPBank buộc phải triển khai trước ngày 1 March 2027 theo Circular 64/2024/TT-NHNN. Trong phạm vi công việc đó đã được lên kế hoạch, yêu cầu Giai đoạn 2 của FundLok là việc sử dụng năng lực đã được cam kết chứ không phải xây dựng bổ sung. Hạng mục 3 của Mục 3.4.6 đề nghị VPBank xác nhận những thành phần nào thuộc bên nào của ranh giới đó.

---

## 3.6.3 FundLok — phần xây dựng của chính FundLok

| Mã | Thành phần | Người-ngày, mức thấp | Người-ngày, mức cao |
|---|---|---|---|
| N1 | Bộ máy tạo lệnh thanh toán có kiểm soát kép | 6 | 9 |
| N2 | Khởi tạo và quản lý vòng đời tài khoản ký quỹ | 4 | 6 |
| N3 | Bản ghi thanh toán từ ngân hàng và đối chiếu tự động | 8 | 12 |
| N4 | Khớp các khoản thu nợ | 6 | 10 |
| N5 | Bộ máy phân phối | 5 | 8 |
| N6 | Đăng ký và xác minh tài khoản thanh toán | 3 | 5 |
| N7 | Bảng điều khiển vận hành và đối chiếu | 5 | 8 |
| N8 | Phân hệ theo dõi dư nợ và báo cáo | 4 | 6 |
| N9 | Các biện pháp kiểm soát bảo vệ dữ liệu | 4 | 6 |
| N10 | Tích hợp T-VAN — thu nhận hằng ngày dữ liệu bán hàng ở cấp hoá đơn | 7 | 12 |
| N11 | Bộ máy chia sẻ doanh thu hằng ngày — tính số tiền phải trả, phát hành yêu cầu, theo dõi nghĩa vụ | 6 | 10 |
| N12 | Tích hợp và kiểm thử, phía FundLok (Mục 3.7) | 6 | 9 |

**Tổng của FundLok: 64 đến 101 người-ngày.** Với hai kỹ sư, khối lượng này tương đương khoảng sáu đến mười tuần làm việc. Mức tăng so với dự toán trước đó phản ánh hai thành phần được bổ sung sau khi cơ chế trả nợ được xác nhận là chia sẻ doanh thu hằng ngày thay vì lịch trả nợ theo kỳ: N10 và N11 cộng lại là 13 đến 22 người-ngày, và N10 là một phụ thuộc của chính dòng tiền — không có luồng dữ liệu bán hàng thì không có số liệu để thu nợ. Cả hai thành phần đều chưa được khởi động; không có bất kỳ nội dung nào liên quan đến việc tích hợp T-VAN xuất hiện trong kho mã nguồn của FundLok tại thời điểm 5 August 2026. Tổng này không bao gồm tám thành phần đã được xây dựng và đang hoạt động, được liệt kê tại Mục 3.5.1, mà chi phí đã do FundLok chịu.

---

## 3.6.4 Những phần chi phí FundLok chịu hoặc đồng tài trợ

FundLok chịu **toàn bộ chi phí của mọi hạng mục nêu tại 3.6.3** — xây dựng, kiểm thử, hạ tầng vận hành, phí xác minh của bên thứ ba, và vận hành thường xuyên. Không phần nào trong đó được tính cho VPBank hoặc chia sẻ với VPBank.

Đối với phần xây dựng của chính VPBank, quan điểm của FundLok như sau.

FundLok không kỳ vọng VPBank chịu chi phí của những năng lực tồn tại chủ yếu vì lợi ích của FundLok. Vì lý do đó, FundLok **đề xuất đồng tài trợ ba hạng mục cụ thể**, theo các điều kiện sẽ được thống nhất:

- **A2, danh sách tài khoản đích được phép.** Đây là biện pháp kiểm soát làm cho toàn bộ cấu trúc trở nên vững chắc, và là hạng mục có khả năng cao nhất đòi hỏi công việc xây mới thực sự. FundLok mong muốn góp phần chi trả hơn là để hạng mục này bị loại khỏi phạm vi.
- **B5, chống trùng lặp lệnh.** Đây là dạng lỗi duy nhất không có biện pháp khắc phục dứt điểm. FundLok xem đây là điều không thể thương lượng và sẵn sàng chi trả cho hạng mục này.
- **D3 hoặc P7, tài khoản ảo theo từng bên trả tiền.** Không bắt buộc, nhưng loại bỏ được cả một nhóm trường hợp ngoại lệ vận hành cho cả hai bên. FundLok sẵn sàng đồng tài trợ để đưa hạng mục này lên Giai đoạn 1.
- **D5, năng lực phân bổ nội bộ hằng ngày.** Chỉ cần thiết theo Phương án B của Mục 1.8, và tồn tại thuần túy để phục vụ mô hình phân bổ của FundLok. FundLok sẽ không đề nghị VPBank chịu chi phí này.

Mọi hạng mục còn lại trong 3.6.1 đều là năng lực hiện có được cấu hình hoặc là chức năng thông thường của sản phẩm lưu ký, và FundLok không đưa ra đề xuất đóng góp nào đối với các hạng mục đó. FundLok không đề xuất đồng tài trợ bất kỳ phần nào của Giai đoạn 2 thuộc phạm vi triển khai Circular 64 của VPBank.

Việc đồng tài trợ được đề xuất dưới hình thức góp phần vào khối lượng công việc phát triển. Hình thức, mức đóng góp và cơ chế là các vấn đề thương mại thuộc phạm vi đàm phán và không được đề xuất tại đây.

---

## 3.6.5 Chi phí vận hành thường xuyên

Chi phí vận hành được thể hiện bằng số điểm can thiệp thủ công mỗi tháng của FundLok và số giờ nhân sự mà chúng tiêu tốn, kết thúc bằng một số liệu về nhân sự tăng thêm — đây là chi phí vận hành của việc triển khai thoả thuận này, không phải một dự toán bằng tiền.

**Các giả định.** Toàn bộ số liệu là dự toán nội bộ của FundLok, lập ngày 5 August 2026: 5–10 khoản vay được cấp vốn mỗi tháng; trung bình tám nhà đầu tư tham gia mỗi khoản vay, suy ra từ đặc điểm nhà đầu tư là văn phòng gia đình của FundLok; kỳ hạn trung bình giả định là 12 tháng; 22 ngày làm việc mỗi tháng; thu nợ theo chia sẻ doanh thu hằng ngày. Tỷ lệ trường hợp ngoại lệ được tách theo loại hình thanh toán — **3% đối với các lượt chuyển tiền thanh toán ra bên ngoài** (chuyển tiền liên ngân hàng đến các tài khoản do bên thứ ba cung cấp) và **0.2% đối với các lượt chuyển tiền nội bộ trong VPBank** giữa các tài khoản do chính VPBank mở và do FundLok đăng ký trước, là những lượt chuyển tiền thất bại với tần suất thấp hơn nhiều. Hai mươi phút để rà soát và phê duyệt kép một lô lệnh thanh toán, 15 phút cho mỗi lần mở tài khoản, 10 phút cho mỗi lần đóng tài khoản, 12 phút cho mỗi trường hợp ngoại lệ, và 5 phút mỗi ngày làm việc để rà soát bản tổng hợp đối chiếu tự động. Một nhân sự quy đổi toàn thời gian (FTE) tương ứng 160 giờ làm việc mỗi tháng.

| Kỳ | Lượt chuyển tiền / tháng, Phương án A | Lượt chuyển tiền / tháng, Phương án B | Điểm can thiệp thủ công / tháng | Giờ nhân sự / tháng | Nhân sự quy đổi toàn thời gian (FTE) |
|---|---|---|---|---|---|
| Tháng 1 | 168–336 | 1,158–2,316 | 62–78 | 14.1–17.6 | 0.09–0.11 |
| Tháng 3 | 414–829 | 3,384–6,769 | 69–101 | 15.6–22.2 | 0.10–0.14 |
| Tháng 6 | 784–1,568 | 6,724–13,448 | 81–135 | 17.8–29.0 | 0.11–0.18 |
| Tháng 12 | 1,523–3,046 | 13,403–26,806 | 108–213 | 23.1–44.3 | 0.14–0.28 |

Các khoảng giá trị của điểm can thiệp thủ công, giờ nhân sự và FTE bao trùm cả hai phương án — giới hạn dưới là Phương án A với 5 khoản vay mỗi tháng, giới hạn trên là Phương án B với 10 khoản vay.

Một điểm can thiệp thủ công là một hành động cần đến con người: phê duyệt một lô lệnh thanh toán, yêu cầu mở hoặc đóng một tài khoản, xử lý một trường hợp ngoại lệ, hoặc rà soát bản tổng hợp đối chiếu hằng ngày.

### Nhân sự tăng thêm

**0.5 nhân sự quy đổi toàn thời gian — một chuyên viên phân tích vận hành làm việc bán thời gian — đủ đáp ứng từ chương trình thử nghiệm (pilot) đến hết tháng 12.**

Tải công việc theo mô hình tại tháng 12 là 0.14 đến 0.28 FTE, tuỳ theo cấu trúc tài khoản. FundLok nêu con số 0.5 thay vì 0.28 để dự phòng cho những biến động mà mô hình không phản ánh: tỷ lệ trường hợp ngoại lệ cao hơn mức giả định trong những tháng đầu, nhịp độ hằng ngày thay vì theo kỳ của chu trình thu nợ, và việc rà soát đối chiếu hằng ngày có giám sát mà Bước 4 của Mục 3.7 yêu cầu trước khi chuyển sang chế độ chỉ rà soát theo trường hợp ngoại lệ.

Tải công việc bị chi phối bởi một cấu phần cố định khoảng 16 giờ nhân sự mỗi tháng và một cấu phần biến đổi phụ thuộc vào loại hình thanh toán: khoảng 0.006 giờ nhân sự cho mỗi lượt chuyển tiền thanh toán ra bên ngoài, và khoảng 0.0004 giờ cho mỗi lượt chuyển tiền nội bộ trong VPBank. Trên cơ sở đó, FundLok đạt tới một vị trí toàn thời gian ở mức khoảng 24,000 lượt chuyển tiền thanh toán ra bên ngoài mỗi tháng, hoặc 360,000 lượt chuyển tiền nội bộ — cả hai đều lớn hơn khối lượng của chương trình thử nghiệm (pilot) một bậc độ lớn. **Thoả thuận này không trở nên thâm dụng nhân sự trước khi nó đủ đáng để tự động hoá.**

Chính cấu trúc tài khoản, chứ không phải nhịp độ thu nợ, là yếu tố làm dịch chuyển các số liệu này. Thu nợ hằng ngày làm phát sinh thêm một lượt chuyển tiền cho mỗi khoản vay trong mỗi ngày làm việc. *Phân bổ* hằng ngày theo Phương án B của Mục 1.8 làm phát sinh thêm một lượt chuyển tiền cho mỗi nhà đầu tư, cho mỗi khoản vay, trong mỗi ngày làm việc, và đó là nguyên nhân của mức chênh lệch tám lần giữa hai cột lượt chuyển tiền nêu trên. Vì các lượt chuyển tiền đó là nội bộ trong VPBank và ít khi thất bại, tác động đến khối lượng công việc của chính FundLok là không lớn — khoảng 0.28 so với 0.21 của một vị trí tại tháng 12 — nhưng tác động đến việc xử lý của VPBank thì không nhỏ, và yêu cầu D5 của Mục 3.3 tồn tại để kiểm nghiệm điều đó.

---

## 3.6.6 Các nội dung cần xác nhận

| # | Nội dung | Vì sao quan trọng đối với mục này | Bên phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | Câu trả lời cho câu hỏi nêu tại Mục 3.3.2 | Làm dịch chuyển dự toán Giai đoạn 1 trong khoảng từ 26.5 đến 86.5 người-ngày. Đây là yếu tố bất định lớn nhất trong mục này | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 2 | Đánh giá của chính VPBank về khối lượng công việc đối với từng thành phần trong 3.6.1 | Các số liệu của FundLok chỉ mang tính tham khảo; số liệu của chính VPBank mới là số liệu chi phối | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 3 | Những thành phần Giai đoạn 2 nào thuộc phạm vi triển khai Circular 64 của VPBank | Xác định bao nhiêu phần trong khoảng 69–125 người-ngày của Giai đoạn 2 là thực sự phát sinh thêm | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 4 | Hình thức và quy mô của đề xuất đồng tài trợ tại 3.6.4 | FundLok đã nêu những hạng mục sẽ góp phần chi trả nhưng chưa nêu mức đóng góp; đây là một quyết định thương mại | Loc, cùng Edward và Huy | 2026-08-07 |
| 5 | Cấu trúc tài khoản được lựa chọn tại Mục 1.8 | Làm dịch chuyển khối lượng lượt chuyển tiền tại 3.6.5 khoảng tám lần, tuy không làm thay đổi kết luận về nhân sự cho chương trình thử nghiệm (pilot) | Loc + Edward | 2026-08-12 |
| 6 | Bảng điều khiển vận hành (N7) có thuộc phạm vi chương trình thử nghiệm (pilot) hay không | Sẽ giảm 5–8 người-ngày khỏi 3.6.3 nếu được hoãn lại | Edward | 2026-08-12 |
| 8 | Xác nhận của Phat về tình trạng của việc tích hợp T-VAN | Dự toán 7–12 người-ngày của N10 giả định rằng chưa có gì tồn tại. Không có nội dung nào xuất hiện trong kho mã nguồn tại thời điểm 5 August 2026 | Edward, cùng Phat | 2026-08-12 |
| 7 | Việc thẩm định các dự toán của FundLok tại 3.6.3 do Huy thực hiện | Ý kiến thẩm định độc lập về giả định tốc độ triển khai trước khi các số liệu được công bố ra bên ngoài | Huy, cùng Edward | 2026-08-07 |

---

*Phụ thuộc: Mục 3.3 (Giai đoạn 1) và Mục 3.4 (Giai đoạn 2). Thống nhất với Mục 3.5 (phần xây dựng của FundLok) và Mục 3.7 (tích hợp và kiểm thử).*
