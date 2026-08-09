# 3.4 Những nội dung VPBank cần xây dựng — Giai đoạn 2

*[NỘI DUNG — Edward. Bản thảo tiếng Anh phục vụ rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

## 3.4.1 Trạng thái: tạm hoãn và không bắt buộc đối với chương trình thử nghiệm

**Không có nội dung nào trong mục này là điều kiện bắt buộc để chương trình thử nghiệm (pilot) có thể vận hành.** Chương trình thử nghiệm hoạt động hoàn toàn dựa trên các năng lực Giai đoạn 1 nêu tại Mục 3.3 — một kênh gửi lệnh thanh toán theo lô an toàn, cơ chế phê duyệt kép và một bản sao kê hằng ngày ở định dạng máy đọc được. Giai đoạn 2 được ghi nhận tại đây để hai bên cùng thấy được hướng phát triển của thoả thuận nếu chương trình thử nghiệm thành công, và để không bên nào bị bất ngờ về sau. Đây không phải là một yêu cầu và không kèm theo bất kỳ mốc thời gian nào.

Giai đoạn 2 được kích hoạt bởi **khối lượng giao dịch**, không phải theo lịch. Ngưỡng kích hoạt được nêu bằng một con số cụ thể tại 3.4.3, và 3.4.4 trình bày các phép tính cho thấy vì sao Giai đoạn 1 vẫn khả thi ngay cả khi khối lượng vượt xa phạm vi chương trình thử nghiệm.

Một điểm bối cảnh đáng được nêu rõ: **Giai đoạn 2 phần lớn trùng lặp với năng lực mà VPBank vốn đã cam kết xây dựng.** Circular 64/2024/TT-NHNN, có hiệu lực từ ngày 1 March 2025, yêu cầu triển khai các tiêu chuẩn API mở trong lĩnh vực ngân hàng trước ngày **1 March 2027** (nguồn: State Bank of Vietnam, Circular 64/2024/TT-NHNN). Các yêu cầu Giai đoạn 2 của FundLok đều là những năng lực ngân hàng mở (open banking) thông thường — phê duyệt API dựa trên token, khởi tạo thanh toán, truy vấn số dư và sao kê, cùng thông báo sự kiện — do đó trong phần lớn các trường hợp, Giai đoạn 2 chỉ yêu cầu FundLok sử dụng những năng lực mà VPBank dù sao cũng sẽ xây dựng, thay vì yêu cầu phát triển riêng theo đặt hàng.

---

## 3.4.2 Các thành phần

| Mã | Thành phần | Nội dung được thay thế từ Giai đoạn 1 | Nội dung mang lại |
|---|---|---|---|
| P1 | API lệnh thanh toán — gửi một lệnh và nhận kết quả cho từng lượt chuyển tiền | Kênh tệp theo lô (3.3 B1) | Loại bỏ chu trình xử lý lô thủ công. Lệnh thanh toán được thực hiện trong ngày và theo từng sự kiện thay vì theo từng lô |
| P2 | Truy vấn trạng thái lệnh thanh toán theo mã tham chiếu riêng của FundLok | Kết quả theo từng dòng trên tệp lô được trả về (3.3 B3) | Cho phép FundLok xử lý một lệnh thanh toán bị hết thời gian chờ mà không gặp rủi ro thanh toán trùng lặp |
| P3 | Chống trùng lặp lệnh dựa trên khoá do phía khách hàng cung cấp, được thực thi bởi API | Tính duy nhất của mã tham chiếu trên kênh tệp (3.3 B5) | Đưa cơ chế chống trùng lặp lệnh trở thành một thuộc tính của giao diện thay vì phụ thuộc vào kỷ luật vận hành |
| P4 | Thông báo tức thời về các khoản ghi có đến | Truy xuất sao kê hằng ngày (3.3 C1) | Loại bỏ tới 24 giờ chậm trễ giữa thời điểm một bên thanh toán và thời điểm FundLok xác nhận khoản thanh toán đó. Đây là thành phần cải thiện nhiều nhất trải nghiệm của nhà đầu tư và bên đi vay |
| P5 | Truy vấn số dư và sao kê theo yêu cầu | Tệp sao kê hằng ngày (3.3 C1, C4) | Cho phép công tác đối chiếu diễn ra liên tục thay vì mỗi ngày một lần, nhờ đó một sai lệch được phát hiện trong vài phút |
| P6 | Mở và đóng tài khoản ký quỹ tự động | Quy trình mở tài khoản theo phương thức vận hành thủ công (3.3 A5) | Cần thiết khi số lượng tài khoản mới mỗi tháng vượt quá khả năng xử lý thuận lợi của một quy trình vận hành |
| P7 | Số tài khoản ảo cho từng người trả tiền, ở quy mô lớn | Đối sánh theo mã tham chiếu thanh toán (3.3 D2, D3) | Giúp việc quy thuộc các khoản tiền đến trở nên xác định và loại bỏ lỗi đối sánh mã tham chiếu như một loại trường hợp ngoại lệ |
| P8 | Phê duyệt API dựa trên token có cơ chế làm mới, cùng hồ sơ chấp thuận trong trường hợp tài khoản của chính người dùng cuối được truy cập | Quyền hạn theo người dùng đích danh trên kênh ngân hàng (3.3 E1) | Lớp kiểm soát truy cập mà bất kỳ hoạt động tích hợp API nào cũng đòi hỏi |
| P9 | Tài khoản riêng cho từng nhà đầu tư và từng bên đi vay | Cấu trúc tài khoản ký quỹ theo từng khoản vay | **Chỉ áp dụng nếu Mục 1.8 lựa chọn Phương án A khi ra mắt và chuyển đổi sang Phương án B về sau.** Nếu Phương án B được áp dụng ngay từ đầu, đây là công việc của Giai đoạn 1 chứ không phải của Giai đoạn 2 |
| P10 | Phân bổ nội bộ theo lô ở quy mô lớn, có kết quả cho từng dòng | Lô phân bổ hằng ngày trên kênh thông thường (3.3 D5) | Theo Phương án B, việc phân bổ hằng ngày là luồng có khối lượng lớn nhất trong thoả thuận — vào khoảng 10,600 lượt chuyển tiền mỗi tháng với 60 khoản vay đang hoạt động. Đây là thành phần giúp giảm tải xử lý nhiều nhất cho chính phía VPBank |

P1 đến P5 là phần cốt lõi của Giai đoạn 2. P6 và P8 mang tính hỗ trợ. P7 là hạng mục đơn lẻ có giá trị cao nhất và cũng được đề xuất như một năng lực tuỳ chọn của Giai đoạn 1 tại Mục 3.3 (D3), bởi nếu VPBank có thể cung cấp năng lực này sớm thì sẽ giảm được khối lượng công việc cho cả hai bên. P9 phụ thuộc hoàn toàn vào Mục 1.8 và chỉ được nêu ra để lưu ý chứ không phải để đề nghị.

---

## 3.4.3 Ngưỡng kích hoạt

**Giai đoạn 2 được kích hoạt khi tổng số sự kiện thanh toán hằng tháng trên toàn bộ các tài khoản ký quỹ vượt 1,000 trong hai tháng liên tiếp.**

Theo Phương án B của Mục 1.8, ngưỡng này gần như bị vượt qua ngay lập tức, bởi chỉ riêng việc phân bổ hằng ngày đã tạo ra 880–1,760 lượt chuyển tiền trong tháng đầu tiên. Trường hợp Phương án B được áp dụng, ngưỡng kích hoạt nêu trên cần được hiểu là áp dụng cho các lượt chuyển tiền *được thanh toán ra bên ngoài* — nhà đầu tư nạp vốn, giải ngân và rút tiền — còn khối lượng phân bổ nội bộ sẽ được xử lý theo yêu cầu D5 của Mục 3.3 và thành phần P10 nêu trên. Theo Phương án A, ngưỡng này được áp dụng đúng như đã nêu.

Một sự kiện thanh toán là một khoản ghi có đến hoặc một lượt chuyển tiền đi. Đơn vị này được lựa chọn vì đây chính là yếu tố thực sự tạo ra khối lượng công việc — một lô gồm 200 lượt chuyển tiền có chi phí phê duyệt tương đương một lô gồm 20 giao dịch, nhưng 200 lượt chuyển tiền lại mang theo khối lượng trường hợp ngoại lệ gấp mười lần.

Các ngưỡng ở cấp độ từng thành phần, dành cho những trường hợp một năng lực trở nên đáng triển khai trước khi đạt tới ngưỡng kích hoạt tổng thể:

| Mã | Thành phần | Kích hoạt khi |
|---|---|---|
| P7 | Tài khoản ảo cho từng người trả tiền | Các khoản ghi có đến không thể quy thuộc vượt 30 mỗi tháng trong hai tháng liên tiếp |
| P4 | Thông báo tức thời về khoản ghi có | Các khoản ghi có đến vượt 500 mỗi tháng, hoặc độ chậm trễ trong việc xác nhận cho nhà đầu tư trở thành một chủ đề khiếu nại có căn cứ |
| P1, P2, P3 | API lệnh thanh toán và chống trùng lặp lệnh | Số lô lệnh thanh toán vượt 20 mỗi tháng — tức là với tần suất dày hơn hằng tuần |
| P6 | Mở tài khoản tự động | Số tài khoản ký quỹ mới vượt 25 mỗi tháng |
| P5 | Truy vấn số dư và sao kê theo yêu cầu | Số tài khoản ký quỹ hoạt động đồng thời vượt 100 |
| P9 | Tài khoản riêng cho từng người dùng | Chỉ khi cấu trúc đó được lựa chọn tại Mục 1.8, với ngưỡng khối lượng riêng được nêu tại mục đó |

Ngưỡng chuyển đổi tại Mục 1.8 cần được thiết lập thống nhất với bảng này thay vì được thiết lập một cách độc lập.

---

## 3.4.4 Vì sao nội dung này được tạm hoãn thay vì được lên lịch triển khai

FundLok đã mô hình hoá khối lượng công việc thủ công mà Giai đoạn 1 đòi hỏi, để nhận định "Giai đoạn 1 là đủ" có thể được kiểm chứng chứ không chỉ là một khẳng định.

**Các giả định.** Toàn bộ số liệu là ước tính nội bộ của FundLok, lập ngày 5 August 2026: 5–10 khoản vay được cấp vốn mỗi tháng; trung bình tám nhà đầu tư tham gia mỗi khoản vay, suy ra từ đặc điểm nhà đầu tư văn phòng gia đình của FundLok; kỳ hạn trung bình giả định là 12 tháng; 22 ngày làm việc mỗi tháng; thu nợ theo chia sẻ doanh thu hằng ngày. Tỷ lệ trường hợp ngoại lệ được phân tách theo hình thức thanh toán — **3% đối với các lượt chuyển tiền được thanh toán ra bên ngoài** (chuyển tiền liên ngân hàng đến các tài khoản do một bên thứ ba cung cấp) và **0.2% đối với các lượt chuyển tiền nội bộ trong VPBank** giữa những tài khoản do chính VPBank mở và FundLok đã đăng ký trước, là các trường hợp có tỷ lệ thất bại thấp hơn nhiều. Hai mươi phút để rà soát và phê duyệt kép một lô lệnh thanh toán, 15 phút cho mỗi lần mở tài khoản, 10 phút cho mỗi lần đóng tài khoản, 12 phút cho mỗi trường hợp ngoại lệ, và 5 phút mỗi ngày làm việc để rà soát bản tổng hợp đối chiếu tự động. Một đơn vị tương đương toàn thời gian (FTE) bằng 160 giờ làm việc mỗi tháng.

| Kỳ | Lượt chuyển dịch / tháng, Phương án A | Lượt chuyển dịch / tháng, Phương án B | Số điểm can thiệp thủ công / tháng | Giờ nhân sự / tháng | Đơn vị tương đương toàn thời gian |
|---|---|---|---|---|---|
| Tháng 1 | 168–336 | 1,158–2,316 | 62–78 | 14.1–17.6 | 0.09–0.11 |
| Tháng 3 | 414–829 | 3,384–6,769 | 69–101 | 15.6–22.2 | 0.10–0.14 |
| Tháng 6 | 784–1,568 | 6,724–13,448 | 81–135 | 17.8–29.0 | 0.11–0.18 |
| Tháng 12 | 1,523–3,046 | 13,403–26,806 | 108–213 | 23.1–44.3 | 0.14–0.28 |

Các khoảng giá trị về điểm can thiệp thủ công, giờ nhân sự và FTE bao trùm cả hai phương án — giới hạn dưới là Phương án A với 5 khoản vay mỗi tháng, giới hạn trên là Phương án B với 10 khoản vay mỗi tháng.

Kết luận là Giai đoạn 1 không sụp đổ tại điểm kích hoạt — mà suy giảm dần. Ngay cả ở tháng 12 theo Phương án B, khối lượng công việc thủ công vào khoảng 28–44 giờ nhân sự mỗi tháng, tương đương một phần tư một vị trí toàn thời gian. **Do đó, Giai đoạn 2 được biện giải bằng độ chậm trễ và bằng việc giảm thiểu rủi ro, chứ không phải bằng nhu cầu nhân sự**, cho đến khi khối lượng vượt xa mức của chương trình thử nghiệm. Theo mô hình này, FundLok sẽ chưa cần bổ sung trọn một nhân sự cho đến khi các lượt chuyển tiền được thanh toán ra bên ngoài đạt khoảng 24,000 mỗi tháng — cao hơn một bậc độ lớn so với mức của chương trình thử nghiệm.

Có hai rủi ro tăng nhanh hơn so với những gì các con số về khối lượng công việc gợi ra, và đó chính là lý do thực sự cho sự tồn tại của Giai đoạn 2. Thứ nhất, độ chậm trễ xác nhận 24 giờ vốn có của phương thức truy xuất sao kê hằng ngày sẽ trở thành một vấn đề về sản phẩm trước khi trở thành một vấn đề về nhân sự, bởi một nhà đầu tư đã chuyển tiền nhưng không thấy khoản tiền đó được ghi có sẽ liên hệ với bộ phận hỗ trợ. Thứ hai, khối lượng trường hợp ngoại lệ tăng tuyến tính theo số sự kiện, trong khi hậu quả của một trường hợp ngoại lệ *bị bỏ sót* thì không — một khoản ghi có chưa được quy thuộc nằm trong tài khoản ký quỹ chỉ là một bất tiện nhỏ, còn ba mươi khoản như vậy là một thất bại của kiểm soát đối chiếu.

---

## 3.4.5 Mức độ phụ thuộc vào cấu trúc tài khoản

Cấu trúc tài khoản hiện vẫn chưa được quyết định (Mục 1.8). Yếu tố này có ảnh hưởng trực tiếp và đáng kể đến thời điểm Giai đoạn 2 được kích hoạt.

| Tần suất | Thời điểm đạt 1,000 sự kiện / tháng, trường hợp thấp | Thời điểm đạt 1,000 sự kiện / tháng, trường hợp cao |
|---|---|---|
| Phương án A — phân bổ là một bút toán sổ sách | Tháng 9 | Tháng 4 |
| Phương án B — phân bổ là một lượt chuyển tiền qua ngân hàng hằng ngày | Tháng 1 | Tháng 1 |

Chính cấu trúc tài khoản, chứ không phải tần suất thu nợ, là yếu tố làm thay đổi điều này. Việc thu nợ hằng ngày chỉ bổ sung khoản thanh toán của chính bên đi vay — một lượt chuyển tiền cho mỗi khoản vay trong mỗi ngày làm việc. Chính việc *phân bổ* hằng ngày theo Phương án B mới là yếu tố nhân khối lượng lên, bởi mỗi khoản tiền thu về được chia toả tới từng nhà đầu tư của khoản vay đó. Do đó, FundLok kiến nghị quyết định xong Mục 1.8 trước khi chương trình thử nghiệm bắt đầu, và đồng thời xác nhận yêu cầu D5 với VPBank.

---

## 3.4.6 Các hạng mục cần xác nhận

| # | Hạng mục | Vì sao quan trọng đối với mục này | Bên phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | Cấu trúc tài khoản được lựa chọn tại Mục 1.8 | Quyết định thời điểm đạt tới ngưỡng kích hoạt, theo 3.4.5. Đây là biến số lớn nhất trong mục này | Loc + Edward | 2026-08-12 |
| 2 | Cấu trúc tài khoản được lựa chọn tại Mục 1.8, và ngưỡng chuyển đổi riêng của cấu trúc đó | Quyết định liệu P9 có nằm trong phạm vi công việc hay không, và ngưỡng đó phải được thiết lập thống nhất với 3.4.3 | Loc + Edward | 2026-08-07 |
| 3 | Những thành phần Giai đoạn 2 nào VPBank dự kiến sẽ có sẵn theo lộ trình triển khai Circular 64 của mình trước ngày 1 March 2027, và những thành phần nào sẽ là bổ sung ngoài lộ trình đó | Quyết định phần nào của Giai đoạn 2 thực sự là công việc phát sinh thêm đối với VPBank, thay vì chỉ là việc sử dụng năng lực đã cam kết | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 4 | Liệu VPBank có muốn đưa P7 lên Giai đoạn 1 dưới dạng năng lực 3.3 D3 hay không | Sẽ loại bỏ được một loại trường hợp ngoại lệ khỏi chính chương trình thử nghiệm và giảm tải vận hành cho cả hai bên | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 5 | Thời điểm rà soát ngưỡng kích hoạt — liệu ngưỡng 1,000 sự kiện có được hai bên cùng rà soát theo một chu kỳ cố định hay không | Tránh tranh chấp về sau liên quan đến việc ngưỡng kích hoạt đã được đáp ứng hay chưa | Edward, cùng với VPBank | Chờ VPBank xác nhận |

---

*Phụ thuộc: Mục 3.3 (Giai đoạn 1) và Mục 1.8 (cấu trúc tài khoản). Ước tính khối lượng công việc cho từng thành phần nêu trên được trình bày tại Mục 3.6.*
