# FundLok — Phản hồi Đề xuất Hợp tác VPBank

**Bản tiếng Việt · Ngày: 5 August 2026 · Phần phụ trách: Edward Wong**

---

## Cách sử dụng tài liệu này

Tài liệu này chứa nội dung cho **mười mục** của đề xuất VPBank. Mỗi mục bắt đầu bằng một dải phân
cách nêu rõ mục đó cần dán vào đâu trong tài liệu gốc, thay cho dòng `[CONTENT — …]`.

Ba mục có kèm sơ đồ — bốn sơ đồ tổng cộng — được cung cấp thành tệp riêng và cần chèn vào vị trí đã ghi trong mục đó:

- **1.4** — sơ đồ dòng tiền bốn giai đoạn
- **1.4** — sơ đồ phân luồng trách nhiệm vòng kín, kèm cơ chế kiểm soát phí của VPBank
- **1.5** — sơ đồ dòng dữ liệu ba vùng
- **3.1** — sơ đồ phân luồng trách nhiệm chín bước

Hai mục còn lại (Phụ lục C và E) đang chờ quyết định về phạm vi.

> **Lưu ý cho người rà soát.** Đây là bản dịch từ bản thảo tiếng Anh, đã được chuẩn hoá thuật ngữ
> theo bảng thuật ngữ bắt buộc. Toàn bộ chữ số được giữ nguyên đúng như bản gốc tiếng Anh; định dạng
> số theo quy ước Việt Nam cần được điều chỉnh trong vòng rà soát của người bản ngữ.

---


<!-- ══════════════════ PASTE INTO SECTION 1.4 ══════════════════ -->

> ## ▼ Mục 1.4 — Dòng tiền
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 1.4.
> **Sơ đồ kèm theo:** `section-1.4-moneyflow (sơ đồ dòng tiền bốn giai đoạn) · section-1.4-closedloop-VI (sơ đồ phân luồng trách nhiệm vòng kín kèm cơ chế kiểm soát phí)`


# 1.4 Dòng tiền

*[NỘI DUNG — Edward. Bản thảo tiếng Anh phục vụ rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

Trong cơ chế này, tiền chỉ dịch chuyển giữa các tài khoản ngân hàng của chính các bên và tài khoản ký quỹ bị hạn chế được mở tại VPBank. Không có bất kỳ thời điểm nào trong dòng tiền mà tiền được chuyển vào một tài khoản mà FundLok có thể chi tiêu từ đó. FundLok phát hành lệnh thanh toán cho mọi lượt chuyển tiền được mô tả dưới đây và không nắm giữ bất kỳ khoản tiền nào.

Toàn bộ chu trình bao gồm tám lượt chuyển tiền, chia thành bốn giai đoạn: các nhà đầu tư nộp tiền vào tài khoản ký quỹ, tài khoản ký quỹ giải ngân cho bên đi vay, bên đi vay trả nợ hằng ngày và các khoản thu đó được phân bổ, và nhà đầu tư rút tiền hoặc tái đầu tư. Từng luồng được trình bày riêng tại 1.4.2, và hai sơ đồ tại 1.4.5 thể hiện đồng thời cả tám luồng.

Cần đọc hai đặc tính của thiết kế này trước khi đi vào chi tiết, bởi mọi nội dung còn lại đều xuất phát từ đó.

**Vòng lặp là vòng kín.** Mọi khoản mà một nhà đầu tư nhận được chỉ có thể được chi trả về đúng tài khoản ngân hàng mà nhà đầu tư đó đã sử dụng để nộp tiền ban đầu. Tài khoản đó được ghi nhận tại thời điểm tiền của nhà đầu tư được chuyển đến, và trở thành tài khoản đích bên ngoài duy nhất khả dụng đối với nhà đầu tư đó trong suốt thời hạn khoản vay. Nội dung này được trình bày đầy đủ tại 1.4.3.

**Phí của FundLok không bao giờ là một lượt chuyển tiền độc lập.** Phí này được chuyển bên trong một lệnh thanh toán đồng thời chi trả cho một người thụ hưởng, dưới hình thức một tỷ lệ cố định của lệnh thanh toán đó, nhờ vậy VPBank có thể kiểm tra phí ngay trên bề mặt của lệnh thanh toán mà không cần biết bất kỳ thông tin nào về khoản vay. FundLok không thể rút tiền đang nằm nhàn rỗi trong tài khoản ký quỹ. Nội dung này được trình bày tại 1.4.4.

**Tình huống mẫu dùng để minh hoạ.** Một khoản vay 2.5 tỷ VND với tám nhà đầu tư tham gia và phí giải ngân 1%. Quy mô nhà đầu tư được suy ra từ hồ sơ nhà đầu tư mục tiêu của FundLok — các văn phòng gia đình giải ngân khoảng USD 200,000 mỗi đơn vị cho mười đến mười lăm bên đi vay — từ đó hàm ý khoảng năm đến tám nhà đầu tư cho một khoản vay có quy mô như vậy. Toàn bộ số liệu là ước tính nội bộ của FundLok, lập ngày 5 August 2026, và chỉ mang tính minh hoạ cho cơ chế vận hành, không phải là cam kết về giá.

---

## 1.4.1 Tám lượt chuyển tiền

| Mã | Luồng chuyển tiền | Từ | Đến | Thời điểm | Tiền tệ |
|---|---|---|---|---|---|
| M1 | Vốn gốc | Tài khoản ngân hàng đã đăng ký của chính từng nhà đầu tư | Tài khoản ký quỹ của dự án | Một lần, khi từng nhà đầu tư cam kết | VND |
| M2 | Vốn gốc sau khi trừ phí | Tài khoản ký quỹ của dự án | Tài khoản đã được xác minh của SME | Một lần, khi đạt mục tiêu huy động vốn | VND |
| M3 | Phí giải ngân | Tài khoản ký quỹ của dự án | Tài khoản phí của FundLok | Cùng lệnh thanh toán với M2 | VND |
| M4 | Chia sẻ doanh thu hằng ngày | SME | Tài khoản ký quỹ của dự án | Mỗi ngày làm việc | VND |
| M5 | Phân bổ | Tài khoản ký quỹ của dự án | Số dư nắm giữ (holding) của từng nhà đầu tư | Mỗi ngày làm việc | VND |
| M6 | Phí quản lý khoản vay | Tài khoản ký quỹ của dự án | Tài khoản phí của FundLok | Cùng lệnh thanh toán với M5 | VND |
| M7 | Rút tiền | Số dư nắm giữ của nhà đầu tư | Tài khoản ngân hàng đã đăng ký của chính nhà đầu tư | Theo yêu cầu của nhà đầu tư | VND |
| M8 | Tái đầu tư | Số dư nắm giữ của nhà đầu tư | Một tài khoản ký quỹ của dự án mới | Theo yêu cầu của nhà đầu tư | VND |

M3 và M6 là hai lượt chuyển tiền duy nhất đi đến FundLok, và không luồng nào trong hai luồng đó có thể được phát hành một cách độc lập.

---

## 1.4.2 Lần lượt từng lượt chuyển tiền

### Giai đoạn 1 — Huy động vốn

**M1 — Vốn gốc chuyển vào tài khoản ký quỹ.** Mỗi nhà đầu tư chuyển số tiền đã cam kết từ tài khoản ngân hàng đã đăng ký của chính mình vào tài khoản ký quỹ của dự án. VPBank ghi có vào tài khoản và thông báo cho FundLok; FundLok đối chiếu khoản ghi có với cam kết của nhà đầu tư đó và **ghi nhận tài khoản nguồn**. Chính việc ghi nhận tại bước này làm cho vòng kín có thể được thực thi về sau. Trong tình huống mẫu, tám nhà đầu tư góp khoảng 312.5 triệu VND mỗi nhà đầu tư để đạt mức 2.5 tỷ VND. Khoản ghi có không thể đối chiếu được với một cam kết sẽ được giữ ở trạng thái chưa phân bổ và được nêu như một trường hợp ngoại lệ, thay vì được áp dụng theo suy đoán.

### Giai đoạn 2 — Giải ngân

**M2 — Vốn gốc sau khi trừ phí chuyển cho SME.** Sau khi toàn bộ vốn gốc đã cam kết được nhận đủ và hợp đồng vay được ký kết, FundLok phát hành một lệnh thanh toán được phê duyệt theo cơ chế kiểm soát kép và VPBank chi trả vào tài khoản đã được xác minh của SME. Trong tình huống mẫu, SME nhận được 2.475 tỷ VND.

**M3 — Phí giải ngân chuyển cho FundLok.** Trong cùng lệnh thanh toán đó, 1% vốn gốc gộp được chuyển vào tài khoản phí của FundLok — tương ứng 25 triệu VND trong tình huống mẫu. **Khoản phí này do SME chi trả**, bởi nghĩa vụ trả nợ của SME được tính trên toàn bộ 2.5 tỷ VND gộp thay vì trên số tiền thực nhận. Do đó, các nhà đầu tư được bảo toàn trọn vẹn phần vốn của mình; không một phần vốn gốc nào của họ được dùng để chi trả cho FundLok. Đây chính là điểm quyết định tính công bằng của khoản phí, và nội dung này cần được đưa vào hợp đồng vay chứ không để suy diễn.

### Giai đoạn 3 — Thu nợ và phân bổ hằng ngày

**M4 — Chia sẻ doanh thu hằng ngày từ SME.** Việc trả nợ không theo một lịch trả góp cố định. Mỗi ngày làm việc, FundLok đọc doanh thu của ngày liền trước của SME từ dữ liệu hoá đơn điện tử thông qua một nhà cung cấp T-VAN được cấp phép, tính toán tỷ lệ phần trăm đã thống nhất, và phát hành cho SME một yêu cầu thanh toán qua nền tảng FundLok và kênh thông báo của nền tảng. SME thanh toán số tiền đó vào tài khoản ký quỹ của dự án, bằng VietQR hoặc chuyển khoản ngân hàng, kèm theo mã tham chiếu do FundLok cung cấp.

Do đó, việc trả nợ đi theo hoạt động kinh doanh thực tế của SME. Một tuần kinh doanh chậm sẽ tạo ra khoản thu nhỏ hơn và một tuần kinh doanh tốt sẽ tạo ra khoản thu lớn hơn, trong khi tổng nghĩa vụ không thay đổi. Đây là cơ chế làm cho sản phẩm phù hợp với các doanh nghiệp nhỏ có doanh thu biến động, và cũng là lý do dòng tiền diễn ra hằng ngày thay vì hằng tháng.

**M5 — Phân bổ cho từng nhà đầu tư.** Sau khi một khoản thu đã được xử lý xong, FundLok tính toán phần chia theo tỷ lệ của từng nhà đầu tư và phát hành một lệnh thanh toán được phê duyệt theo cơ chế kiểm soát kép; VPBank ghi có vào số dư nắm giữ của từng nhà đầu tư. Quyền lợi của từng nhà đầu tư được theo dõi riêng biệt tại mọi thời điểm; không có việc gộp chung vị thế của một nhà đầu tư với vị thế của nhà đầu tư khác.

**M6 — Phí quản lý khoản vay chuyển cho FundLok.** Trong cùng lệnh thanh toán với M5, phí quản lý của FundLok được chi trả vào tài khoản phí của FundLok dưới hình thức một tỷ lệ cố định của số tiền đang được phân bổ. **Khoản phí này do các nhà đầu tư chi trả** và được trích từ phần lợi nhuận, không bao giờ từ vốn gốc.

Trong trường hợp một khoản phân bổ đơn lẻ không thực hiện được — chẳng hạn do tài khoản đích không thể tiếp cận — các khoản phân bổ khác trong cùng lệnh thanh toán đó vẫn được quyết toán và số tiền không thực hiện được sẽ nằm lại trong tài khoản ký quỹ của dự án để thực hiện lại. Số tiền đó không bao giờ được chuyển hướng, không bao giờ được áp dụng cho một nhà đầu tư khác và không bao giờ được áp dụng cho một khoản vay khác.

### Giai đoạn 4 — Rút tiền hoặc tái đầu tư

**M7 — Rút tiền.** Nhà đầu tư yêu cầu chuyển tiền thông qua nền tảng FundLok, và VPBank chi trả số tiền đó về tài khoản ngân hàng đã đăng ký của chính nhà đầu tư đó — đúng tài khoản mà nhà đầu tư đã sử dụng để nộp tiền tại M1, và không phải tài khoản nào khác. Đây chính là vòng kín trong thực tế vận hành.

**M8 — Tái đầu tư.** Ngoài ra, nhà đầu tư có thể chỉ định chuyển số dư khả dụng của mình vào một khoản vay mới; trong trường hợp đó, số dư sẽ nộp vốn vào một tài khoản ký quỹ của dự án mới và chu trình lại bắt đầu từ M1. Do vậy, một số dư đang được nắm giữ tự thân là một nguồn vốn, bên cạnh khoản chuyển tiền đến từ tài khoản ngân hàng của nhà đầu tư.

---

## 1.4.3 Quy tắc vòng kín

**Tiền đã được nhận thay mặt cho một nhà đầu tư chỉ có thể rời khỏi cơ chế này để đi đến đúng tài khoản ngân hàng mà nhà đầu tư đó đã sử dụng để nộp tiền ban đầu.**

Quy tắc vận hành như sau. Tại M1, tài khoản ngân hàng nguồn của mỗi khoản tiền chuyển đến được ghi nhận gắn với nhà đầu tư tương ứng. Tài khoản đó, và chỉ tài khoản đó, được đăng ký là tài khoản đích bên ngoài được phép đối với nhà đầu tư đó. Tại M7, VPBank chi trả về tài khoản đã đăng ký; không có tài khoản đích nào khác khả dụng đối với nhà đầu tư đó, và một yêu cầu chỉ định tài khoản khác sẽ không được thực hiện. Việc thay đổi tài khoản đã đăng ký là một sự kiện có kiểm soát, đòi hỏi xác minh lại rằng tài khoản mới thuộc về đúng bên đã được xác minh, chứ không phải là một thay đổi do người dùng tự thực hiện.

Có hai hệ quả đáng được nêu rõ. FundLok không thể chỉ định chuyển tiền của nhà đầu tư cho một bên thứ ba, bởi không bên thứ ba nào có thể là tài khoản đích được phép. Và nhà đầu tư không thể sử dụng nền tảng để chuyển tiền đến một tài khoản chưa được xác minh là thuộc về chính mình, qua đó khép lại con đường lạm dụng rõ ràng nhất đối với một thị trường thuộc loại này.

Quy tắc này được áp dụng tương tự ở phía bên đi vay: SME chỉ nhận tiền tại tài khoản đã được xác minh của chính mình, được ghi nhận và xác minh trước khi giải ngân.

---

## 1.4.4 Cách FundLok được chi trả mà không nắm giữ tiền

Có hai khoản phí, và cả hai đều bị ràng buộc theo cùng một cách.

| | Phí giải ngân | Phí quản lý khoản vay |
|---|---|---|
| Mã tham chiếu | M3 | M6 |
| Mức xấp xỉ | 1% vốn gốc gộp | Cần xác nhận — xem 1.4.7 |
| Bên chi trả | SME | Các nhà đầu tư |
| Trích từ | Vốn gốc gộp, với nghĩa vụ của SME được tính trên số tiền gộp | Lợi nhuận, không bao giờ từ vốn gốc |
| Thời điểm | Bên trong lệnh thanh toán giải ngân (M2) | Bên trong mỗi lệnh thanh toán phân bổ (M5) |
| VPBank có thể kiểm tra dưới hình thức | Một tỷ lệ cố định của lệnh thanh toán mà nó đi kèm | Một tỷ lệ cố định của lệnh thanh toán mà nó đi kèm |

Bốn ràng buộc được áp dụng cho cả hai khoản phí, và cùng nhau chúng tạo thành cơ chế bảo vệ những người thụ hưởng trong khi vẫn cho phép FundLok được chi trả:

1. **Không bao giờ là một lượt chuyển tiền độc lập.** Một dòng phí chỉ được phép tồn tại bên trong một lệnh thanh toán đồng thời chi trả cho một người thụ hưởng trong cùng lệnh thanh toán đó. Một lệnh thanh toán chỉ bao gồm phí sẽ không được thực hiện.
2. **Không bao giờ trích từ số dư nhàn rỗi.** FundLok không thể rút từ số dư đang nằm trong tài khoản ký quỹ. Nếu không có người thụ hưởng nào được chi trả thì không có khoản phí nào được chuyển.
3. **Tỷ lệ có thể kiểm tra được bởi ngân hàng.** Khoản phí là một tỷ lệ cố định của lệnh thanh toán mà nó nằm trong đó, nhờ vậy VPBank kiểm tra phép tính ngay trên bề mặt của lệnh thanh toán thay vì dựa vào trình bày của FundLok. Một mức trần đã đăng ký được áp dụng như một biện pháp dự phòng.
4. **Tạm ngừng khi một tài khoản bị phong toả.** Trong trường hợp một tài khoản bị giữ theo cơ chế xử lý tranh chấp, quyền hưởng phí của FundLok bị tạm ngừng trong suốt thời gian đó. FundLok không tiếp tục thu phí đối với một khoản vay đang có tranh chấp hoặc đang vỡ nợ.

Kết quả là FundLok không thể vét sạch một tài khoản ký quỹ, không thể lấy bất cứ khoản nào trừ khi có một người thụ hưởng được chi trả trong cùng lượt chuyển tiền, và không thể chạm tới vốn của nhà đầu tư.

---

## 1.4.5 Các sơ đồ

Sơ đồ kèm theo thể hiện toàn bộ tám lượt chuyển tiền qua bốn giai đoạn, kèm chú giải phân biệt vốn gốc, phí của FundLok, việc trả nợ và phân bổ, cùng việc rút tiền và tái đầu tư. Sơ đồ được định kích thước để vẫn dễ đọc khi in ở khổ A4. Các mã tham chiếu M trên sơ đồ khớp với bảng liệt kê tại 1.4.1.

*[Chèn: `section-1.4-moneyflow` — sơ đồ dòng tiền bốn giai đoạn kèm chú giải.]*

Sơ đồ thứ hai trình bày đúng tám lượt chuyển tiền đó dưới dạng sơ đồ phân luồng trách nhiệm, mỗi bên một luồng, và diễn giải chi tiết cơ chế kiểm soát mà VPBank áp dụng đối với mọi lệnh thanh toán có chứa dòng phí của FundLok. Sơ đồ này đi kèm với 1.4.3 và 1.4.4: mục thứ nhất xác lập rằng vòng tiền là vòng kín, mục thứ hai xác lập rằng phí của FundLok bị giới hạn ngay trên mặt lệnh, không phụ thuộc vào cam kết của chính FundLok. Bốn bước kiểm tra được thể hiện — tài khoản đích được phép, ghép cặp với dòng chi trả người thụ hưởng, tỷ lệ và mức trần đã đăng ký, và tạm ngưng khi tài khoản bị tạm giữ — chính là bốn ràng buộc nêu tại 1.4.4, được diễn đạt thành các bước do VPBank thực hiện.

*[Chèn: `section-1.4-closedloop-VI` — sơ đồ phân luồng trách nhiệm vòng kín, kèm cơ chế kiểm soát của VPBank đối với lệnh thanh toán có dòng phí.]*

---

## 1.4.6 Tính khả dụng và việc chuyển tiền là hai vấn đề khác nhau

Các nhà đầu tư kỳ vọng lợi nhuận của mình khả dụng kịp thời, và chu trình thu nợ hằng ngày có nghĩa là giá trị được tích luỹ cho họ vào mỗi ngày làm việc. Cần nói chính xác điều đó có nghĩa gì về mặt vận hành, bởi "khả dụng hằng ngày" và "được chuyển hằng ngày" không phải là cùng một yêu cầu.

Số dư của một nhà đầu tư trở nên **khả dụng** ngay khi khoản phân bổ của ngày được hạch toán — hiển thị trên nền tảng FundLok và thuộc về nhà đầu tư đó. Số dư đó được **chuyển** về tài khoản ngân hàng của chính nhà đầu tư khi nhà đầu tư yêu cầu, tại M7. Do đó, tính khả dụng hằng ngày không đòi hỏi một khoản chi trả ra bên ngoài hằng ngày đến ngân hàng bên ngoài của mọi nhà đầu tư, điều sẽ làm khối lượng giao dịch tăng lên nhiều lần mà không cải thiện vị thế của nhà đầu tư.

Sự phân biệt này cũng quyết định nơi mà một số dư chưa được rút thực tế nằm lại, và đây chính là nội dung cốt lõi của lựa chọn cấu trúc tài khoản tại Mục 1.8, không được giải quyết trong mục này.

---

## 1.4.7 Khối lượng giao dịch

Số lượng lượt chuyển tiền phát sinh trực tiếp từ chu trình hằng ngày. Theo tình huống mẫu tám nhà đầu tư cho mỗi khoản vay, mỗi khoản vay đang hoạt động tạo ra mười lượt chuyển tiền mỗi ngày làm việc: một khoản thu chuyển đến, tám khoản phân bổ và một khoản phí.

| Số khoản vay đang hoạt động | Số lượt chuyển tiền mỗi ngày làm việc | Số lượt chuyển tiền mỗi tháng | Trong đó nội bộ VPBank |
|---|---|---|---|
| 10 | 100 | 2,200 | 1,980 |
| 30 | 300 | 6,600 | 5,940 |
| 60 | 600 | 13,200 | 11,880 |
| 120 | 1,200 | 26,400 | 23,760 |

Các giả định: tám nhà đầu tư cho mỗi khoản vay, 22 ngày làm việc mỗi tháng, một khoản thu chuyển đến và một luồng chuyển phí cho mỗi khoản vay mỗi ngày. Ước tính nội bộ của FundLok, lập ngày 5 August 2026.

Bảng này chỉ tính **chu trình hằng ngày** — M4, M5 và M6. Do đó bảng không bao gồm việc nộp vốn của nhà đầu tư (M1), giải ngân (M2, M3) và rút tiền (M7), là những giao dịch một lần hoặc theo yêu cầu. Các số tổng tại Mục 1.8.3, 3.4.4 và 3.6.5 bao gồm cả những giao dịch đó, và vì vậy cao hơn tương ứng.

Cột phân bổ giả định Phương án B của Mục 1.8, theo đó mỗi nhà đầu tư nắm giữ tài khoản ký quỹ riêng của mình. Theo Phương án A, M5 là một bút toán trong sổ sách của FundLok và không tạo ra lượt chuyển tiền qua ngân hàng, qua đó loại bỏ tám khoản phân bổ cho mỗi khoản vay mỗi ngày và chỉ còn lại hai luồng.

Lượt chuyển tiền nào được quyết toán **trong nội bộ** VPBank và lượt nào phải đi liên ngân hàng phụ thuộc vào việc mỗi bên mở tài khoản tại ngân hàng nào; không bên tham gia nào bắt buộc phải mở tài khoản tại VPBank (Mục 1.8.3).

| Lượt chuyển tiền | Quyết toán nội bộ tại VPBank nếu… | Trường hợp còn lại |
|---|---|---|
| M1 nhà đầu tư nộp vốn | nhà đầu tư mở tài khoản tại VPBank | tiền vào liên ngân hàng |
| M2 giải ngân · M3 phí | bên đi vay mở tài khoản tại VPBank; M3 nếu tài khoản phí của FundLok đặt tại VPBank | tiền ra liên ngân hàng |
| M4 chia sẻ doanh thu hằng ngày | bên đi vay mở tài khoản tại VPBank | tiền vào liên ngân hàng — **luồng ra bên ngoài lớn nhất**, khoảng 1,320 lượt mỗi tháng khi có 60 khoản vay đang hoạt động |
| M5 phân bổ · M6 phí | luôn là nội bộ theo Phương án B; theo Phương án A không phát sinh lượt chuyển tiền tại ngân hàng |  |
| M7 rút tiền | nhà đầu tư mở tài khoản tại VPBank | tiền ra liên ngân hàng |

Với giả định không bên nào mở tài khoản tại VPBank, tổng số lượt chuyển tiền quyết toán ra bên ngoài là khoảng **1,568 lượt mỗi tháng khi có 60 khoản vay đang hoạt động** — và con số này giống nhau ở cả Phương án A và Phương án B, vì toàn bộ phần tăng thêm của Phương án B đều là nội bộ. Từ đó có hai hệ quả. Chuyển khoản nội bộ có chi phí rất thấp đối với VPBank, nên số lượt chuyển tiền cao hơn của Phương án B phần lớn mang tính hạch toán chứ không phải một khoản chi phí thực. Và nếu bên đi vay mở tài khoản tại VPBank, 1,320 lượt thanh toán hằng tháng của M4 cũng trở thành nội bộ — đây là điểm nên nêu rõ với VPBank như một lợi ích thay vì để ngầm hiểu.

---

## 1.4.8 Các nội dung cần xác nhận

| # | Nội dung | Vì sao quan trọng đối với mục này | Bên phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | Mức phí quản lý khoản vay, và việc phí này là một tỷ lệ của từng khoản phân bổ hay của lợi nhuận | Tỷ lệ của M6 phải được nêu rõ để VPBank kiểm tra được trên lệnh thanh toán | Loc, cùng Edward | 2026-08-12 |
| 2 | Tỷ lệ phần trăm chia sẻ doanh thu, và việc tỷ lệ này có thay đổi theo hạng tín nhiệm hay không | Quyết định quy mô của M4 và do đó quyết định toàn bộ chu trình hằng ngày | Loc + Edward | 2026-08-12 |
| 3 | Nơi mà số dư chưa được rút của nhà đầu tư thực tế nằm lại — một tài khoản ở cấp nhà đầu tư tại VPBank, hay tài khoản ký quỹ của dự án với quyền lợi được theo dõi trong sổ sách của FundLok | Quyết định việc M5 là một lượt chuyển tiền qua ngân hàng hay một bút toán sổ sách, và làm thay đổi khối lượng lượt chuyển tiền hằng tháng khoảng mười lần | Loc + Edward (Mục 1.8) | 2026-08-12 |
| 4 | Việc VPBank có thể thực hiện khối lượng phân bổ nội bộ ở mức thể hiện tại 1.4.7 hay không, và cách VPBank định giá các giao dịch đó | Quyết định việc phân bổ hằng ngày tại M5 có khả thi như thiết kế hay không | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 5 | Cách xử lý trường hợp SME thanh toán vượt mức hoặc một khoản thu vượt quá số dư còn lại | Cần một tài khoản đích được xác định; bản thân quy tắc vòng kín không nêu rõ khoản dư thừa sẽ đi về đâu | Edward | 2026-08-12 |
| 6 | Việc tài khoản đích bên ngoài đã đăng ký có thể được thay đổi hay không, và theo thủ tục xác minh nào | Mục 1.4.3 giả định một quy trình xác minh lại có kiểm soát chứ không phải người dùng tự thực hiện | Edward, cùng VPBank | Chờ VPBank xác nhận |
| 7 | Các giá trị mức trần cho biện pháp dự phòng về phí tại ràng buộc 3 của 1.4.4 | VPBank cần một mức tối đa đã đăng ký, không chỉ là một tỷ lệ | Loc, cùng Edward | 2026-08-12 |

---

*Các phụ thuộc: Mục 1.3 (cấu trúc bốn bên). Nhất quán với Mục 1.5 (dòng dữ liệu), Mục 1.7 (giới hạn vai trò), Mục 1.8 (cấu trúc tài khoản) và Mục 3.1 (quy trình). Cơ chế chia sẻ doanh thu hằng ngày phụ thuộc vào tích hợp T-VAN được ghi nhận tại Mục 3.5.*


<!-- ══════════════════ PASTE INTO SECTION 1.5 ══════════════════ -->

> ## ▼ Mục 1.5 — Dòng dữ liệu
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 1.5.
> **Sơ đồ kèm theo:** `section-1.5-dataflow (three-zone data-flow diagram)`


# 1.5 Luồng dữ liệu

*[NỘI DUNG — Edward. Bản thảo tiếng Anh phục vụ rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

**FundLok luân chuyển dữ liệu và lệnh thanh toán, không luân chuyển tiền.** Tiền chỉ dịch chuyển giữa các tài khoản của chính các bên và tài khoản ký quỹ bị hạn chế được mở tại VPBank; không có bất kỳ thời điểm nào tiền đi qua một tài khoản do FundLok kiểm soát. Điều mà FundLok luân chuyển là thông tin: kết quả thẩm định làm phát sinh một khoản vay, lệnh thanh toán đề nghị ngân hàng chuyển tiền tới một tài khoản đích được phép, và việc đối chiếu chứng minh rằng hai bộ sổ sách khớp nhau.

Mục này trình bày mọi loại dữ liệu vượt qua ranh giới giữa FundLok và VPBank, theo chiều nào, và — quan trọng không kém — những gì chủ ý không bao giờ vượt qua ranh giới đó. Nguyên tắc chi phối là **tối thiểu cần thiết**: VPBank nhận những gì cần thiết để mở tài khoản, thực hiện một lệnh thanh toán và báo cáo những gì đã thực hiện, và không nhận gì ngoài phạm vi đó.

Ba đặc tính của thiết kế phát sinh từ nguyên tắc đó và được thể hiện rõ trong bảng kê dưới đây.

Thứ nhất, **thông tin tín dụng không bao giờ tới VPBank.** VPBank không đưa ra quyết định cho vay, do đó ngân hàng không có nhu cầu đối với điểm tín dụng, hạng tín nhiệm, bậc lãi suất hay báo cáo tài chính của SME, và ngân hàng không nhận bất kỳ thông tin nào trong số đó. Đây chính là điều làm cho tuyên bố "VPBank không chịu rủi ro tín dụng" trở thành một thực tế mang tính cấu trúc về mặt dữ liệu, chứ không chỉ là một thực tế mang tính hợp đồng.

Thứ hai, **dữ liệu thẩm định không đi qua FundLok.** Mỗi bên nộp hồ sơ mở tài khoản trực tiếp cho VPBank để phục vụ công tác thẩm định khách hàng (CDD) của chính ngân hàng. FundLok không thu thập bộ hồ sơ đó thay cho VPBank và cũng không truyền bộ hồ sơ đó, bởi việc đánh giá của ngân hàng là việc của chính ngân hàng và không được xây dựng trên hồ sơ của FundLok.

Thứ ba, **các lệnh thanh toán không mang theo dữ liệu cá nhân nhiều hơn mức mà một lượt chuyển tiền có ghi tên người nhận đòi hỏi** — số tài khoản, tên chủ tài khoản, số tiền và nội dung tham chiếu.

---

## 1.5.1 Ranh giới

| Vùng | Nắm giữ | Hành vi tại ranh giới |
|---|---|---|
| Các bên — nhà đầu tư và SME | Dữ liệu về danh tính, tài chính và tài khoản thanh toán của chính mình | Nộp dữ liệu nền tảng cho FundLok; nộp hồ sơ mở tài khoản trực tiếp cho VPBank |
| FundLok — bên thu xếp & vận hành | Hồ sơ nền tảng, kết quả thẩm định, sổ sách, lịch sử lệnh thanh toán, trạng thái đối chiếu | Gửi lệnh thanh toán và dữ liệu khởi tạo tài khoản cho VPBank; nhận xác nhận và sao kê. Không bao giờ nắm giữ tiền |
| VPBank — đơn vị lưu ký | Tài khoản ký quỹ, danh sách tài khoản đích được phép của tài khoản đó, và bản ghi những gì ngân hàng đã thực hiện | Nhận lệnh thanh toán; trả về kết quả, sao kê và số dư. Không nắm giữ thông tin tín dụng |

---

## 1.5.2 Bảng kê đầy đủ — dữ liệu trao đổi với VPBank

### FundLok → VPBank

| Mã | Nội dung trao đổi | Các trường dữ liệu |
|---|---|---|
| F1 | Yêu cầu khởi tạo tài khoản | Mã tham chiếu khoản vay · tên tài khoản đề nghị · danh sách tài khoản đích được phép, mỗi mục bao gồm số tài khoản đích, tên chủ tài khoản, mã định danh ngân hàng và loại tài khoản đích (tài khoản của bên đi vay đã được xác minh, hoặc tài khoản nguồn đã đăng ký của nhà đầu tư) · danh tính của người dùng được uỷ quyền gửi yêu cầu |
| F1a | Sửa đổi danh sách tài khoản đích được phép | Mã tham chiếu khoản vay · số tài khoản ký quỹ · mục cần bổ sung hoặc loại bỏ · những người dùng phê duyệt · mã lý do |
| F2 | Lệnh thanh toán, theo từng lượt chuyển tiền | Số tài khoản ký quỹ · số tài khoản đích và tên chủ tài khoản · số tiền · loại tiền (VND) · mã tham chiếu lệnh thanh toán duy nhất của FundLok · mã tham chiếu lô · ngày giá trị đề nghị · nội dung diễn giải hiển thị trên sao kê của người thụ hưởng · danh tính của hai người dùng phê duyệt |
| F3 | Quản trị kênh | Tên và vai trò của những người dùng được uỷ quyền · cấp độ quyền hạn (lập lệnh hoặc phê duyệt) · việc bổ sung, sửa đổi và thu hồi |
| F4 | Yêu cầu đóng tài khoản | Mã tham chiếu khoản vay · số tài khoản ký quỹ · xác nhận số dư bằng không · những người dùng phê duyệt |

### VPBank → FundLok

| Mã | Nội dung trao đổi | Các trường dữ liệu |
|---|---|---|
| B1 | Xác nhận khởi tạo tài khoản | Số tài khoản ký quỹ · tên tài khoản như đã đăng ký · trạng thái · ngày mở tài khoản |
| B2 | Kết quả xử lý lệnh thanh toán | Xác nhận tiếp nhận lô · trạng thái theo từng lượt chuyển tiền · mã tham chiếu của ngân hàng cho từng lượt chuyển tiền đã thực hiện · mã và nội dung lý do từ chối trong trường hợp áp dụng · dấu thời gian thực hiện |
| B3 | Sao kê hằng ngày, theo từng dòng | Mã định danh giao dịch của ngân hàng (không thay đổi qua các lần truy xuất) · ngày hạch toán · ngày giá trị · số tiền · chiều giao dịch, ghi có hoặc ghi nợ · tên đối tác · tài khoản đối tác · nội dung tham chiếu thanh toán hoặc nội dung diễn giải như đã nhận · số dư luỹ kế |
| B3a | Phần đầu sao kê | Số tài khoản ký quỹ · kỳ sao kê · số dư đầu kỳ và số dư cuối kỳ |
| B4 | Phản hồi truy vấn số dư | Số tài khoản ký quỹ · số dư · dấu thời gian |
| B5 | Sao kê cuối cùng khi đóng tài khoản | Toàn bộ lịch sử giao dịch của tài khoản · số dư cuối kỳ bằng không · ngày đóng tài khoản |

### Các bên → VPBank, trực tiếp

| Mã | Nội dung trao đổi | Các trường dữ liệu |
|---|---|---|
| V0 | Hồ sơ mở tài khoản phục vụ công tác thẩm định của chính ngân hàng | Theo quy định của VPBank — giấy tờ định danh, giấy chứng nhận đăng ký doanh nghiệp, thông tin về người thụ hưởng và những người được uỷ quyền ký. **FundLok không thu thập, không nắm giữ và không truyền bộ hồ sơ này thay cho VPBank** |

### Các bên ↔ FundLok — được ghi nhận để bảo đảm đầy đủ, không có nội dung nào vượt qua ranh giới sang VPBank

| Mã | Nội dung trao đổi | Các trường dữ liệu |
|---|---|---|
| P1 | Dữ liệu định danh và dữ liệu doanh nghiệp | Kết quả xác minh danh tính và các tài liệu chứng minh · dữ liệu đăng ký doanh nghiệp và dữ liệu giấy phép · danh tính người đại diện được uỷ quyền |
| P2 | Dữ liệu đầu vào tài chính và dữ liệu đầu vào thẩm định | Báo cáo tài chính · lịch sử kinh doanh · phân loại ngành · điều kiện bảo lãnh cá nhân |
| P3 | Tài khoản thanh toán và sự đồng ý | Thông tin tài khoản thanh toán, được lưu trữ dưới dạng che dấu · bản ghi sự đồng ý kèm dấu thời gian, phạm vi và trạng thái rút lại sự đồng ý |
| P4 | Thông tin trả lại cho các bên | Điều kiện khoản vay và lãi suất · số tiền hằng ngày được yêu cầu và đã thu · sao kê và số dư nắm giữ · xác nhận thanh toán |
| P5 | Dữ liệu bán hàng hằng ngày, qua một nhà cung cấp T-VAN được cấp phép | Bản ghi bán hàng ở cấp độ từng hoá đơn của ngày liền trước, từ đó tính ra số tiền chia sẻ doanh thu hằng ngày. Được lấy từ dữ liệu hoá đơn điện tử của bên đi vay với sự đồng ý của bên đi vay, không lấy từ VPBank |
| P6 | Yêu cầu thanh toán hằng ngày gửi tới bên đi vay | Số tiền đến hạn · tham chiếu tới báo giá · được phát hành thông qua nền tảng FundLok và kênh thông báo của nền tảng |


---

## 1.5.3 Những gì không bao giờ vượt qua ranh giới sang VPBank

- Điểm tín dụng, hạng tín nhiệm, bậc lãi suất, hoặc bất kỳ kết quả thẩm định hay tài liệu tính toán thẩm định nào.
- Báo cáo tài chính của SME hoặc tài liệu chứng minh kèm theo.
- Điều kiện bảo lãnh cá nhân hoặc bất kỳ chi tiết nào về việc thực thi bảo lãnh.
- Số dư nắm giữ trong danh mục của nhà đầu tư, ưu tiên phân bổ hoặc hành vi của nhà đầu tư trên nền tảng.
- Dữ liệu bán hàng và dữ liệu hoá đơn của bên đi vay thu thập được thông qua nhà cung cấp T-VAN, và mọi dữ liệu cá nhân của khách hàng của chính bên đi vay chứa trong dữ liệu đó.
- Giấy tờ định danh và bằng chứng xác minh do FundLok nắm giữ phục vụ quy trình tiếp nhận khách hàng của chính FundLok.
- Bất kỳ dữ liệu cá nhân nào ngoài số tài khoản, tên chủ tài khoản, số tiền và nội dung tham chiếu mà một lượt chuyển tiền có ghi tên người nhận đòi hỏi.

Danh sách này là một ràng buộc thiết kế, không phải một mong muốn. Hệ quả thực tiễn của danh sách này là việc giao diện kết nối FundLok–VPBank bị xâm phạm sẽ chỉ làm lộ các lệnh thanh toán và sao kê, chứ không làm lộ dữ liệu cá nhân và dữ liệu tín dụng của người dùng nền tảng.

---

## 1.5.4 Việc xử lý và cơ sở pháp lý

Dữ liệu cá nhân vượt qua ranh giới sang VPBank được giới hạn ở mức cần thiết để thực hiện hợp đồng vay và thoả thuận lưu ký. Sự đồng ý được thu thập từ mỗi bên tại thời điểm tài khoản thanh toán của bên đó được đăng ký, được ghi nhận kèm dấu thời gian và phạm vi, và có thể được rút lại. Đường truyền được mã hoá, quyền truy cập được giới hạn cho những người dùng được uỷ quyền có tên cụ thể với quyền hạn lập lệnh và quyền hạn phê duyệt được tách biệt, và mọi hoạt động trao đổi trong bảng kê nêu trên đều được ghi nhận vào tệp log ở cả hai phía. Thời hạn lưu trữ, tiêu chuẩn mã hoá, phương án ứng phó sự cố rò rỉ dữ liệu và cách xử lý đối với bất kỳ hoạt động xử lý dữ liệu nào ngoài lãnh thổ Việt Nam được quy định tại Mục 4.4.

---

## 1.5.5 Sơ đồ

Sơ đồ kèm theo thể hiện ba vùng, mọi luồng nêu tại 1.5.2 kèm mã tham chiếu của luồng đó, và khung dữ liệu không bao giờ vượt qua ranh giới. Luồng đi trực tiếp từ các bên tới VPBank được vẽ bằng nét đứt và đi vòng qua bên ngoài FundLok, nhằm thể hiện rõ rằng công tác thẩm định của ngân hàng không đi qua nền tảng. Luồng dữ liệu bán hàng từ T-VAN (P5) và yêu cầu thanh toán hằng ngày (P6) là các luồng thuộc phía FundLok, không vượt qua ranh giới VPBank, do đó chúng xuất hiện trong bảng kê nêu trên và trong khung dữ liệu không vượt qua ranh giới của sơ đồ, chứ không xuất hiện với tư cách các luồng qua ranh giới.

*[Chèn: `section-1.5-dataflow` — sơ đồ luồng dữ liệu ba vùng kèm mã tham chiếu các luồng và tập dữ liệu không vượt qua ranh giới.]*

---

## 1.5.6 Các nội dung cần xác nhận

| # | Nội dung | Ý nghĩa đối với mục này | Đơn vị phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | Bộ trường dữ liệu và định dạng mà VPBank yêu cầu đối với F1, F2 và F3 | Bảng kê nêu trên là đề xuất của FundLok; kênh của VPBank sẽ áp đặt cấu trúc dữ liệu riêng của kênh đó | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 2 | Độ dài tối đa của nội dung tham chiếu thanh toán được bảo toàn xuyên suốt, và liệu tên đối tác có luôn được trả về đối với các giao dịch ghi có đến hay không | Quyết định việc các giao dịch ghi có đến có thể được đối khớp tự động hay phải chuyển sang tra soát thủ công. Cùng một phụ thuộc như các nội dung C3 và D2 tại Mục 3.3 | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 3 | Liệu VPBank có yêu cầu bất kỳ thông tin nào về người thụ hưởng ngoài các mục trong danh sách tài khoản đích được phép tại F1 hay không | Nếu có, quan điểm tối thiểu hoá dữ liệu tại 1.5.3 cần được trình bày lại và Mục 4.4 cần bao quát bộ dữ liệu bổ sung | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 4 | Liệu hồ sơ mở tài khoản (V0) được nộp tại quầy giao dịch, thông qua kênh số của chính VPBank, hay theo một phương thức mà FundLok cần hướng dẫn | Ảnh hưởng tới trải nghiệm của các bên tại Bước 1 của Mục 3.1 nhưng không ảnh hưởng tới bản thân ranh giới dữ liệu | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 5 | Cấu trúc tài khoản được lựa chọn tại Mục 1.8 | Nếu áp dụng tài khoản riêng cho từng bên, F1 và B1 sẽ áp dụng theo từng bên thay vì theo từng khoản vay; các bộ trường dữ liệu không thay đổi | Loc + Edward | 2026-08-12 |
| 6 | Liệu dữ liệu ở cấp độ từng hoá đơn nhận được thông qua nhà cung cấp T-VAN có chứa dữ liệu cá nhân của khách hàng của chính bên đi vay hay không, và nếu có thì những dữ liệu nào được lưu giữ | Một loại dữ liệu cá nhân mới mà chưa mục nào xem xét trước đây. Liên quan trực tiếp tới Mục 4.4 | Edward, cùng với bộ phận pháp chế | 2026-08-14 |
| 7 | Kênh thông báo được sử dụng cho yêu cầu thanh toán hằng ngày, và những dữ liệu mà kênh đó truyền tải | Quyết định việc có thêm một đơn vị xử lý dữ liệu nằm trong luồng hay không và những nội dung mà Mục 4.4 phải bao quát | Edward | 2026-08-12 |

---

*Phụ thuộc: Mục 1.3 (cấu trúc bốn bên). Thống nhất với Mục 1.4 (luồng tiền), Mục 3.1 (quy trình), Mục 3.3 (yêu cầu Giai đoạn 1) và Mục 4.4 (bảo vệ dữ liệu).*


<!-- ══════════════════ PASTE INTO SECTION 1.8 ══════════════════ -->

> ## ▼ Mục 1.8 — Cấu trúc tài khoản
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 1.8.

# 1.8 Cấu trúc tài khoản — Phương án A và Phương án B

*[NỘI DUNG — Loc và Edward. Bản thảo tiếng Anh dùng để rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

Có hai cấu trúc tài khoản có thể triển khai thoả thuận được mô tả tại Mục 1.3, Mục 1.4 và Mục 3.1. Cả hai đều bảo đảm nguồn vốn của nhà đầu tư được tách biệt khỏi tiền của chính FundLok, cả hai đều cho phép thực hiện cùng tám luồng dịch chuyển tiền, và cả hai đều hỗ trợ quy tắc vòng kín. Hai cấu trúc khác nhau ở một điểm: **các tài khoản được đứng tên ai**, và do đó số dư chưa rút của nhà đầu tư thực tế nằm ở đâu.

- **Phương án A — FBO.** Một tài khoản ký quỹ bị hạn chế cho mỗi khoản vay, đứng tên FundLok *thay mặt và vì lợi ích của* SME và các nhà đầu tư của khoản vay đó. Các khoản tiền thu nợ tích luỹ trong tài khoản này và quyền lợi của từng nhà đầu tư được theo dõi trên sổ sách của FundLok. Khi có yêu cầu rút tiền, số dư được chuyển sang tài khoản thanh toán của chính nhà đầu tư.
- **Phương án B — Ký quỹ.** Mỗi nhà đầu tư nắm giữ tài khoản ký quỹ riêng của mình tại VPBank, được mở dưới tên của chính nhà đầu tư, cùng với một tài khoản ký quỹ của dự án đóng vai trò là điểm tập trung thu tiền cho mỗi khoản vay. Các khoản tiền thu nợ được phân bổ hằng ngày vào tài khoản ký quỹ của từng nhà đầu tư. Khi có yêu cầu rút tiền, số dư được chuyển từ đó sang tài khoản thanh toán của chính nhà đầu tư.

Cả hai phương án được trình bày dưới đây theo cùng bốn yếu tố, tiếp theo là một khuyến nghị và một ngưỡng kích hoạt chuyển đổi.

**Các giả định.** Số liệu ước tính nội bộ của FundLok ngày 5 August 2026: 5–10 khoản vay được cấp vốn mỗi tháng trong chương trình thử nghiệm; các nhà đầu tư là văn phòng gia đình, mỗi bên đầu tư khoảng USD 200,000 vào mười đến mười lăm bên đi vay, tương ứng năm đến tám nhà đầu tư trên một khoản vay 2.5 tỷ VND; 22 ngày làm việc mỗi tháng; thu chia sẻ doanh thu hằng ngày theo Mục 1.4.

---

## 1.8.1 Phương án A — FBO

### Mô tả

Một tài khoản ký quỹ bị hạn chế cho mỗi khoản vay, đứng tên FundLok thay mặt và vì lợi ích của những người thụ hưởng của khoản vay đó. Các nhà đầu tư cấp vốn vào tài khoản này, tài khoản này giải ngân cho SME và tiếp nhận các khoản trả nợ theo chia sẻ doanh thu hằng ngày. Phần của mỗi nhà đầu tư trong số tiền đã thu được ghi nhận trên sổ sách ghi kép (double-entry ledger) của FundLok chứ không phải dưới dạng một số dư ngân hàng riêng biệt. Khi một nhà đầu tư yêu cầu rút tiền, FundLok phát hành lệnh thanh toán chuyển tiền từ tài khoản ký quỹ sang tài khoản thanh toán đã đăng ký của chính nhà đầu tư đó. Số dư chưa rút vẫn nằm trong tài khoản ký quỹ và có thể được chuyển vào một khoản vay mới.

### Yêu cầu xây dựng

| Yếu tố | Yêu cầu |
|---|---|
| Số tài khoản cần mở | Một tài khoản cho mỗi khoản vay — 5–10 tài khoản mỗi tháng ở quy mô thử nghiệm |
| Năng lực cần có từ VPBank | Tài khoản bị hạn chế với danh sách tài khoản đích được phép do ngân hàng thực thi, kênh phát hành lệnh thanh toán có kiểm soát kép, sao kê hằng ngày ở dạng máy đọc được. Toàn bộ nằm trong Giai đoạn 1 như quy định tại Mục 3.3 |
| Mở tài khoản | Quy trình vận hành thủ công là đủ ở quy mô này; không cần tự động hoá |
| Phần FundLok phải xây dựng | Như đã quy định tại Mục 3.5. Sổ sách theo dõi quyền lợi của từng nhà đầu tư đã được xây dựng và đưa vào vận hành |
| Số lượt chuyển tiền hằng ngày trên mỗi khoản vay | Hai — một lượt tiền vào và một lượt phí. Phân bổ là một bút toán trên sổ sách, không phải một lệnh chuyển tiền |

### Ưu điểm

Đơn giản trong vận hành và chi phí thấp: khoảng 336 lượt chuyển tiền mỗi tháng với 10 khoản vay đang hoạt động và 1,568 lượt với 60 khoản vay, bởi phân bổ là một bút toán trên sổ sách và không phát sinh lệnh chuyển tiền qua ngân hàng. Việc mở tài khoản vẫn nằm trong phạm vi một quy trình vận hành thủ công trong suốt chương trình thử nghiệm và còn xa hơn nữa. Tái đầu tư diễn ra không có ma sát, vì số dư chưa rút đã nằm trong một tài khoản có thể cấp vốn cho một khoản vay mới. Ít tài khoản hơn nghĩa là danh sách tài khoản đích được phép ngắn hơn và phạm vi đối chiếu nhỏ hơn. Phương án này cũng đặt ra yêu cầu Giai đoạn 1 nhẹ hơn đối với VPBank, khiến đây là cấu trúc có thể đưa vào vận hành nhanh hơn.

### Nhược điểm

Điểm yếu mang tính quyết định là về pháp lý chứ không phải về vận hành. Do tài khoản đứng tên FundLok, việc bảo vệ nguồn vốn của nhà đầu tư trong trường hợp FundLok mất khả năng thanh toán phụ thuộc vào việc chỉ định *thay mặt và vì lợi ích của* có được công nhận hay không — tức là số tiền đó không phải là tài sản của FundLok và do đó không cấu thành bất kỳ phần nào của khối tài sản của FundLok. Đây là vấn đề thuộc pháp luật Việt Nam và thuộc cách thức chỉ định đó được ghi nhận trong hồ sơ, không phải vấn đề mà FundLok có thể tự khẳng định. Chính việc đứng tên như vậy cũng làm phát sinh một vấn đề kế toán: kiểm toán viên có thể yêu cầu ghi nhận số dư này trên bảng cân đối kế toán của FundLok kèm một khoản nợ phải trả đối ứng, thay vì được xử lý hoàn toàn ngoài bảng cân đối kế toán.

Do đó, VPBank buộc phải dựa một phần vào sổ sách của FundLok đối với nhận định rằng phần của mỗi nhà đầu tư đúng như FundLok tuyên bố. Sổ sách này chỉ cho phép ghi thêm (append-only), không thể thay đổi ở tầng cơ sở dữ liệu và được đối chiếu hằng ngày với sao kê của chính VPBank — nhưng đó vẫn là bản ghi của FundLok về một sự phân chia không có biểu hiện độc lập nào trong hệ thống ngân hàng. Quyền yêu cầu của nhà đầu tư là một quyền lợi, không phải một số dư ngân hàng đứng tên chính họ.

---

## 1.8.2 Phương án B — Ký quỹ

### Mô tả

Mỗi nhà đầu tư nắm giữ một tài khoản ký quỹ tại VPBank đứng tên chính mình, được mở một lần và sử dụng lại cho mọi khoản vay mà nhà đầu tư đó tham gia. Một tài khoản ký quỹ của dự án cho mỗi khoản vay đóng vai trò điểm tập trung thu tiền: các nhà đầu tư cấp vốn vào tài khoản này, tài khoản này giải ngân cho SME và tiếp nhận các khoản trả nợ theo chia sẻ doanh thu hằng ngày. Mỗi khoản tiền về đã hoàn tất thanh toán đều được phân bổ ngay trong ngày vào tài khoản ký quỹ của từng nhà đầu tư. Một lệnh rút tiền chuyển tiền từ tài khoản ký quỹ của nhà đầu tư sang tài khoản thanh toán đã đăng ký của chính nhà đầu tư đó. Tái đầu tư chuyển số dư từ tài khoản ký quỹ của nhà đầu tư vào một tài khoản ký quỹ của dự án mới.

### Yêu cầu xây dựng

| Yếu tố | Yêu cầu |
|---|---|
| Số tài khoản cần mở | Một tài khoản cho mỗi khoản vay, cộng với một tài khoản cho mỗi nhà đầu tư được duy trì thường xuyên. Ở quy mô thử nghiệm, khoảng 1–10 tài khoản nhà đầu tư mới mỗi tháng, bởi các văn phòng gia đình có quy mô giao dịch lớn và mỗi tài khoản được sử dụng lại cho mười đến mười lăm khoản vay |
| Năng lực cần có từ VPBank | Toàn bộ như Phương án A, cộng thêm năng lực thực hiện phân bổ nội bộ hằng ngày giữa các tài khoản nhà đầu tư, và một danh sách tài khoản đích được phép đủ lớn để chứa n+2 mục cho mỗi dự án |
| Mở tài khoản | Quy trình vận hành thủ công là đủ ở quy mô thử nghiệm; cần tự động hoá khi số tài khoản nhà đầu tư mới vượt khoảng 25 tài khoản mỗi tháng, đây chính là ngưỡng kích hoạt đã được đặt ra cho hạng mục P6 tại Mục 3.4 |
| Phần FundLok phải xây dựng | Như Mục 3.5, cộng thêm việc lệnh phân bổ trở thành một lô xử lý hằng ngày thay vì một bút toán trên sổ sách |
| Số lượt chuyển tiền hằng ngày trên mỗi khoản vay | Mười lượt theo trường hợp tính toán giả định — một lượt tiền vào, tám lượt phân bổ và một lượt phí. Số lượt chuyển tiền tại Mục 1.8.3 cũng bao gồm việc nhà đầu tư cấp vốn, giải ngân và rút tiền, do đó cao hơn các số liệu chu kỳ hằng ngày tại Mục 1.4.7 |

### Ưu điểm

Tiền của nhà đầu tư nằm trong một tài khoản đứng tên chính nhà đầu tư. Trong trường hợp FundLok mất khả năng thanh toán, số tiền này hoàn toàn không thuộc khối tài sản của FundLok, do đó vấn đề liệu một chỉ định có được công nhận hay không sẽ không phát sinh. VPBank có thể chứng minh việc tách biệt nguồn vốn từ hồ sơ của chính mình mà không cần dựa vào sổ sách của FundLok, và vấn đề kế toán cũng theo đó mà không còn. Số dư của mỗi nhà đầu tư là một số dư ngân hàng, được chứng minh bằng sao kê đứng tên chính họ — điều này vừa là một vị thế pháp lý vững chắc hơn, vừa là điều tốt hơn để có thể trình bày với nhà đầu tư. Đây cũng là cấu trúc mà theo hiểu biết hiện có, VPBank ưu tiên lựa chọn, chính vì những lý do nêu trên.

### Nhược điểm

Nhiều tài khoản hơn và số lượt chuyển tiền lớn hơn đáng kể: khoảng 13,400 lượt mỗi tháng với 60 khoản vay đang hoạt động so với 1,570 lượt theo Phương án A, và gần như toàn bộ phần chênh lệch là giao dịch nội bộ trong VPBank. Điều này khiến FundLok tốn thêm rất ít thời gian nhân sự — khoảng 0.28 so với 0.21 của một vị trí toàn thời gian tại tháng thứ 12 — nhưng đó là khối lượng xử lý thực tế về phía VPBank, và việc VPBank có thể đáp ứng được hay không, cũng như định giá ra sao, hiện vẫn chưa được xác định. Việc tự động hoá mở tài khoản trở nên cần thiết sớm hơn so với Phương án A. Tái đầu tư đòi hỏi một lệnh chuyển tiền trở lại thay vì chỉ là một bút toán trên sổ sách. Và danh sách tài khoản đích được phép phải chứa được mười mục cho mỗi dự án theo trường hợp tính toán giả định, tức khoảng 600 mục đang hoạt động với 60 khoản vay đang hoạt động, đây là một yêu cầu về quy mô mà chưa ai xác nhận sản phẩm của VPBank có hỗ trợ hay không.

---

## 1.8.3 So sánh song song hai phương án

| | Phương án A — FBO | Phương án B — Ký quỹ |
|---|---|---|
| Chủ tài khoản đứng tên | FundLok, thay mặt và vì lợi ích của những người thụ hưởng | Mỗi nhà đầu tư, đứng tên chính mình |
| Số tài khoản ở quy mô thử nghiệm | 5–10 tài khoản mỗi tháng, một tài khoản cho mỗi khoản vay | 5–10 tài khoản cho mỗi khoản vay mỗi tháng, cộng với 1–10 tài khoản nhà đầu tư mới mỗi tháng |
| Số dư của nhà đầu tư là | Một quyền lợi trên sổ sách của FundLok | Một số dư ngân hàng đứng tên chính nhà đầu tư |
| Số lượt chuyển tiền mỗi tháng với 60 khoản vay đang hoạt động | ~1,570 | ~13,400 |
| Khối lượng vận hành của FundLok tại tháng thứ 12 | 0.14–0.21 FTE | 0.18–0.28 FTE |
| Bảo vệ khi mất khả năng thanh toán | Phụ thuộc vào việc chỉ định FBO có được công nhận hay không | Mang tính cấu trúc — nguồn vốn không thuộc khối tài sản của FundLok |
| Vấn đề kế toán | Kiểm toán viên có thể yêu cầu ghi nhận trên bảng cân đối kế toán kèm một khoản nợ phải trả đối ứng | Không phát sinh |
| VPBank phải dựa vào sổ sách của FundLok đối với việc phân chia | Có, ở một mức độ nhất định | Không |
| Có cần tự động hoá mở tài khoản | Không cần trong suốt chương trình thử nghiệm có thể dự kiến | Khi số tài khoản nhà đầu tư mới vượt ~25 tài khoản mỗi tháng |
| Yêu cầu Giai đoạn 1 đối với VPBank | Nhẹ hơn | Bổ sung năng lực phân bổ nội bộ và một danh sách tài khoản đích lớn hơn |

### Những tài khoản nào phải mở tại VPBank

**Không bên tham gia nào phải chuyển hoạt động ngân hàng hiện tại của mình sang VPBank.** Chỉ bản thân tài khoản ký quỹ là bắt buộc phải mở tại VPBank.

| Tài khoản | Phương án A — FBO | Phương án B — Ký quỹ |
|---|---|---|
| Tài khoản ký quỹ của dự án | **Bắt buộc tại VPBank** | **Bắt buộc tại VPBank** |
| Tài khoản thanh toán thường dùng của nhà đầu tư | Ngân hàng nào cũng được | Ngân hàng nào cũng được |
| Tài khoản ký quỹ riêng của nhà đầu tư | Không cần | **Bắt buộc tại VPBank** — mở một lần, dùng lại cho mọi khoản vay |
| Tài khoản của bên đi vay nhận giải ngân | Ngân hàng nào cũng được | Ngân hàng nào cũng được |
| Tài khoản của bên đi vay dùng để trả phần chia sẻ doanh thu hằng ngày | Ngân hàng nào cũng được | Ngân hàng nào cũng được |
| Tài khoản thu phí của FundLok | Ngân hàng nào cũng được; nên đặt tại VPBank | Ngân hàng nào cũng được; nên đặt tại VPBank |

Theo Phương án B, mỗi nhà đầu tư có thêm **một** tài khoản tại VPBank. Đây là điều kiện nội tại của Phương án B chứ không phải một sự ưu tiên: tài khoản ký quỹ của nhà đầu tư chỉ có thể tồn tại tại đơn vị lưu ký, và chính điều đó đặt số dư dưới tên của nhà đầu tư và nằm ngoài khối tài sản của FundLok. Tài khoản thanh toán thường dùng của nhà đầu tư — đồng thời là tài khoản đích rút tiền đã đăng ký — vẫn giữ nguyên tại ngân hàng hiện tại. Bên đi vay không cần tài khoản tại VPBank theo cả hai phương án.

**Điều này kéo theo một yêu cầu kỹ thuật dễ bị bỏ sót.** Vì các tài khoản đích nằm ở ngân hàng khác, tài khoản ký quỹ phải thực hiện được lệnh chuyển tiền liên ngân hàng và danh sách tài khoản đích được phép phải chấp nhận tài khoản mở tại ngân hàng khác. Một số sản phẩm tài khoản phong toả chỉ cho phép tài khoản đích trong cùng ngân hàng. Yêu cầu này được nêu tại Mục 3.3 A2b và được đặt thành phần thứ tư của câu hỏi tại Mục 3.3.2.

Tài khoản thu phí của FundLok nên được mở tại VPBank để lượt chuyển tiền phí được quyết toán nội bộ và xuất hiện trên cùng bản sao kê đang được đối chiếu, tuy nhiên cấu trúc này không bắt buộc điều đó.

---

## 1.8.4 Khuyến nghị

**FundLok khuyến nghị Phương án B.**

Lý do là bất lợi về vận hành thì nhỏ, còn lợi ích về pháp lý thì không nhỏ. Phương án A đơn giản hơn và chi phí vận hành thấp hơn, nhưng khoảng chênh lệch chỉ khoảng 0.07 của một vị trí toàn thời gian tại tháng thứ 12 cùng một phần khối lượng xử lý nội bộ tăng thêm tại VPBank — trong khi chênh lệch về mức độ bảo vệ nhà đầu tư là chênh lệch giữa một quyền yêu cầu phụ thuộc vào việc một chỉ định có vượt qua được sự soi xét pháp lý hay không và một quyền yêu cầu ngay từ đầu không bao giờ thuộc khối tài sản của FundLok. Đối với một nền tảng mà toàn bộ định vị là không nắm giữ vị thế nào và không bao giờ giữ tiền của khách hàng, cấu trúc khiến điều đó đúng theo nghĩa nguyên văn là xứng đáng với chi phí vận hành phát sinh.

Ba lý do bổ trợ. Phương án B loại bỏ vấn đề kế toán thay vì phải trả lời nó. Phương án B loại bỏ việc VPBank phải dựa vào sổ sách của FundLok đối với việc phân chia nguồn vốn, vốn là điều khó chấp nhận nhất đối với một đơn vị lưu ký. Và đây là định hướng mà theo hiểu biết hiện có, VPBank thiên về lựa chọn, do đó đây không phải là điểm mà FundLok phải đánh đổi uy tín để thu về rất ít.

Khuyến nghị này phụ thuộc vào hai xác nhận từ VPBank, mà FundLok không thể tự trả lời: rằng VPBank có thể thực hiện được khối lượng phân bổ nội bộ hằng ngày nêu tại Mục 1.8.3, và rằng danh sách tài khoản đích được phép có thể chứa ít nhất mười mục cho mỗi tài khoản dự án, kèm khả năng sửa đổi có kiểm soát trong suốt thời gian hiệu lực của tài khoản. Nếu một trong hai điều kiện không được đáp ứng, Phương án A là phương án dự phòng và không nên vì điều đó mà trì hoãn chương trình thử nghiệm — hai cấu trúc không khác biệt đến mức việc bắt đầu bằng Phương án A sẽ loại trừ khả năng chuyển sang Phương án B.

---

## 1.8.5 Chuyển đổi

Việc chuyển đổi liên quan đến hai tình huống khác biệt và không nên đồng nhất hai tình huống này với nhau.

**Tình huống 1 — một chương trình thử nghiệm với mức cam kết thấp hơn, sau đó tiến tới cấu trúc mục tiêu.** FundLok có thể bắt đầu với thoả thuận đơn giản nhất mà VPBank có thể hỗ trợ nhanh chóng — lệnh thanh toán thủ công, một tài khoản ký quỹ của dự án duy nhất cho mỗi khoản vay, không có tài khoản riêng cho từng nhà đầu tư — nhằm chứng minh luồng vận hành trên vài khoản vay đầu tiên trước khi cam kết theo một trong hai cấu trúc. Trên thực tế, đây chính là Phương án A, bất kể có được mô tả như vậy hay không.

**Tình huống 2 — từ Phương án A sang Phương án B.** Khi Phương án A được áp dụng làm cấu trúc khởi đầu và Phương án B là mục tiêu, việc chuyển đổi bao gồm mở một tài khoản ký quỹ cho từng nhà đầu tư hiện hữu, chuyển quyền lợi đã được theo dõi của từng nhà đầu tư từ tài khoản ký quỹ của dự án sang tài khoản mới của họ, và chuyển việc phân bổ từ một bút toán trên sổ sách sang một lệnh chuyển tiền hằng ngày. Các khoản vay hiện hữu tiếp tục không bị gián đoạn; các hợp đồng cho vay không bị ảnh hưởng, bởi cấu trúc tài khoản nằm bên dưới các hợp đồng đó.

**Ngưỡng kích hoạt, thể hiện bằng một con số về khối lượng.** Việc chuyển đổi từ Phương án A sang Phương án B được khởi động khi **số tài khoản nhà đầu tư mới vượt 25 tài khoản mỗi tháng**, duy trì liên tục trong hai tháng liền kề.

Con số này được chọn vì 25 tài khoản mỗi tháng xấp xỉ là mức mà một quy trình mở tài khoản thủ công không còn đáp ứng được khối lượng công việc — với 15 phút cho mỗi tài khoản, tương đương khoảng 6 giờ nhân sự mỗi tháng, và vượt quá mức đó thì chi phí tăng nhanh hơn lợi ích của việc trì hoãn. Đây là ngưỡng được cố ý đặt trùng với ngưỡng đã quy định cho việc tự động hoá mở tài khoản tại hạng mục P6 của Mục 3.4, để hai ngưỡng này không lệch nhau: thời điểm mà việc chuyển sang Phương án B trở nên đáng thực hiện chính là thời điểm mà dù thế nào VPBank cũng cần tự động hoá việc mở tài khoản.

Hai ngưỡng kích hoạt thứ cấp, mỗi ngưỡng đều có thể khiến việc chuyển đổi được thực hiện sớm hơn bất kể khối lượng: một nhà đầu tư hoặc luật sư tư vấn yêu cầu số dư phải được nắm giữ dưới tên của chính nhà đầu tư, hoặc một thay đổi trong cách xử lý kế toán đối với số dư theo Phương án A mà kiểm toán viên của FundLok không sẵn sàng chấp thuận.

**Không phải là một thời điểm ấn định.** Việc chuyển đổi không được lên lịch trước. Nếu ngưỡng kích hoạt về khối lượng không bao giờ đạt tới, Phương án A tiếp tục được duy trì vô thời hạn, và đó là một kết quả có thể chấp nhận chứ không phải một nghĩa vụ bị trì hoãn.

---

## 1.8.6 Các hạng mục cần xác nhận

| # | Hạng mục | Vì sao quan trọng đối với mục này | Bên phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | Liệu VPBank có thể thực hiện phân bổ nội bộ hằng ngày ở khối lượng nêu tại Mục 1.8.3 hay không, và định giá các giao dịch đó như thế nào | Khuyến nghị chọn Phương án B phụ thuộc vào điều này | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 2 | Số mục tối đa trên một danh sách tài khoản đích được phép cho mỗi tài khoản, và liệu có thể bổ sung thêm mục trong thời gian hiệu lực của tài khoản hay không | Phương án B cần ít nhất n+2 mục cho mỗi dự án, khoảng 600 mục đang hoạt động với 60 khoản vay đang hoạt động | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 3 | Liệu việc chỉ định FBO theo Phương án A có được công nhận theo hướng nguồn vốn nằm ngoài khối tài sản của FundLok hay không | Điểm yếu trọng tâm của Phương án A. Nếu luật sư tư vấn xác nhận điều này một cách vững chắc, Phương án A trở nên hấp dẫn hơn đáng kể | Edward, cùng luật sư tư vấn | 2026-08-14 |
| 4 | Cách xử lý kế toán đối với số dư theo Phương án A — ghi nhận trên bảng cân đối kế toán kèm một khoản nợ phải trả đối ứng, hoặc ngoài bảng cân đối kế toán kèm thuyết minh | Quyết định nội dung mà FundLok có thể nêu bằng văn bản với VPBank | Loc, cùng kế toán của FundLok | 2026-08-14 |
| 5 | Xác nhận rằng VPBank thực sự ưu tiên Phương án B, và trên cơ sở nào | Nội dung này được nêu như hiểu biết của FundLok chứ không phải như một thực tế đã được xác lập | Loc, cùng VPBank | Chờ VPBank xác nhận |
| 6 | Liệu một nhà đầu tư có thể nắm giữ một tài khoản ký quỹ duy nhất cho toàn bộ các khoản vay, hay VPBank yêu cầu một tài khoản cho mỗi khoản vay đối với mỗi nhà đầu tư | Nếu là trường hợp thứ hai, số lượng tài khoản của Phương án B tăng lên một bậc độ lớn và khuyến nghị sẽ thay đổi | VPBank, do Edward đề nghị | Chờ VPBank xác nhận |
| 7 | Tốc độ tiếp nhận nhà đầu tư mới dự kiến, sau khi các mục tiêu bán hàng được xác định | Ngưỡng kích hoạt chuyển đổi tại Mục 1.8.5 được thể hiện dựa trên chỉ số này | Loc | 2026-08-12 |

---

*Phụ thuộc: Mục 3.3 (các yêu cầu Giai đoạn 1). Thống nhất với Mục 1.3 (cấu trúc bốn bên), Mục 1.4 (luồng tiền), Mục 1.7 (giới hạn vai trò các bên), Mục 3.1 (quy trình) và Mục 3.4 (Giai đoạn 2, trong đó ngưỡng kích hoạt P6 dùng chung mức 25 tài khoản mỗi tháng). Việc mất khả năng thanh toán và cách xử lý kế toán được ghi nhận tại Mục 4.5.*


<!-- ══════════════════ PASTE INTO SECTION 3.1 ══════════════════ -->

> ## ▼ Mục 3.1 — Quy trình end-to-end
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.1.
> **Sơ đồ kèm theo:** `section-3.1-swimlane (nine-step swim-lane diagram)`


# 3.1 Quy trình đầu-cuối — chín bước từ tiếp nhận đến tất toán khoản vay

*[NỘI DUNG — Edward và Lộc. Bản thảo tiếng Anh phục vụ soát xét nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

Mục này trình bày toàn bộ quy trình vận hành của một khoản vay, từ khâu tiếp nhận các bên cho đến khi tất toán và giải toả tài khoản ký quỹ. Mục này chỉ định bên chịu trách nhiệm cho từng bước trong chín bước và thể hiện quy trình dưới dạng sơ đồ phân luồng trách nhiệm.

Có bốn bên tham gia, mỗi bên chỉ đảm nhiệm một vai trò duy nhất. **Nhà đầu tư** là **bên cho vay chính thức** và là chủ sở hữu khoản vay. **SME** là bên đi vay. **FundLok** là **bên thu xếp & vận hành**: thực hiện thẩm định, kết nối, phát hành lệnh thanh toán và đối chiếu, đồng thời không phải là một bên của hợp đồng cho vay. **VPBank** là **đơn vị lưu ký** trung lập: giữ tiền trong tài khoản ký quỹ có mục đích sử dụng bị hạn chế và thực hiện chuyển tiền đến các tài khoản đích đã được thống nhất trước theo lệnh.

Hai nguyên tắc chi phối toàn bộ quy trình và được thể hiện trong từng bước dưới đây. Thứ nhất, **FundLok chỉ luân chuyển lệnh và dữ liệu, không bao giờ luân chuyển tiền** — không có bước nào trao cho FundLok quyền chiếm giữ hoặc quyền rút tiền đối với vốn nằm trong tài khoản ký quỹ. Thứ hai, **vòng luân chuyển tiền là vòng kín**: tiền chỉ ra khỏi tài khoản ký quỹ để đến một tài khoản của bên đi vay đã được xác thực, đến chính tài khoản mà tiền của nhà đầu tư ban đầu chuyển đi, hoặc đến tài khoản thu phí của FundLok — và trong trường hợp cuối cùng này, chỉ dưới hình thức một tỷ lệ cố định của một lệnh thanh toán có chi trả cho người thụ hưởng trong cùng một giao dịch luân chuyển. FundLok không bao giờ có thể trích tiền từ một số dư đang nằm yên. Mục 1.4 trình bày đầy đủ nội dung này.

Một khoản vay có một bên đi vay và một hoặc nhiều nhà đầu tư. Khi một bước dưới đây đề cập đến "nhà đầu tư", nội dung đó áp dụng riêng cho từng nhà đầu tư tham gia, và quyền lợi của mỗi nhà đầu tư được theo dõi và hoàn trả một cách riêng biệt.

---

## 3.1.1 Tổng quan chín bước

| # | Bước | Nội dung thực hiện | Bên chịu trách nhiệm |
|---|---|---|---|
| 1 | Tiếp nhận nhà đầu tư & mở tài khoản | Nhà đầu tư được tiếp nhận vào nền tảng; VPBank độc lập hoàn tất công tác thẩm định khách hàng (CDD) của mình và mở tài khoản cho nhà đầu tư | VPBank — Tiếp nhận khách hàng (mở tài khoản) · FundLok — Vận hành tiếp nhận (đăng ký trên nền tảng) |
| 2 | Tiếp nhận, thẩm định & niêm yết SME | SME được FundLok tiếp nhận và thẩm định; ấn định bậc lãi suất; cơ hội đầu tư được công bố | FundLok — Tín dụng & Thẩm định cấp tín dụng |
| 3 | Thiết lập tài khoản ký quỹ | Tài khoản ký quỹ có mục đích sử dụng bị hạn chế cho khoản vay được mở và cấu hình cùng danh sách tài khoản đích được phép và kênh truyền lệnh thanh toán theo cơ chế kiểm soát kép | VPBank — Vận hành lưu ký |
| 4 | Ký kết hợp đồng cho vay | Hợp đồng cho vay được ký trực tiếp giữa nhà đầu tư và SME; hợp đồng uỷ quyền quản lý và điều khoản sử dụng nền tảng được ký kết | FundLok — Vận hành nền tảng & Pháp chế |
| 5 | Nộp vốn vào tài khoản ký quỹ | Mỗi nhà đầu tư nộp vốn vào tài khoản ký quỹ, từ tài khoản đã đăng ký của chính mình hoặc từ số dư đang có; tài khoản chuyển tiền nguồn được ghi nhận | Nhà đầu tư (chuyển tiền) · VPBank — Vận hành lưu ký (ghi có và thông báo) |
| 6 | Giải ngân cho SME | Các điều kiện giải ngân được kiểm tra; FundLok phát hành lệnh thanh toán theo cơ chế kiểm soát kép; VPBank giải ngân vào tài khoản đã được xác thực của SME | FundLok — Vận hành ngân quỹ (phát hành lệnh) · VPBank — Vận hành lưu ký (thực hiện) |
| 7 | Thu chia sẻ doanh thu hằng ngày | Mỗi ngày làm việc, FundLok tính số tiền phải trả căn cứ trên doanh thu ngày liền trước của SME và yêu cầu thanh toán; SME nộp tiền vào tài khoản ký quỹ | SME (thanh toán) · VPBank — Thu nợ (ghi có và thông báo) |
| 8 | Phân bổ và hoàn trả cho nhà đầu tư | FundLok tính quyền lợi của từng nhà đầu tư và phí của chính mình trong cùng một lệnh thanh toán; VPBank phân bổ cho nhà đầu tư và chi trả phí | FundLok — Vận hành ngân quỹ (phát hành lệnh) · VPBank — Vận hành lưu ký (thực hiện) |
| 9 | Tất toán & giải toả tài khoản ký quỹ | Các khoản cuối cùng được hoàn trả, số dư được đối chiếu về không, sao kê được phát hành, tài khoản ký quỹ được giải toả | FundLok — Đối chiếu & Báo cáo · VPBank — Vận hành lưu ký (giải toả) |

Không có bước nào thiếu bên chịu trách nhiệm. Khi có hai bên chịu trách nhiệm được nêu, bên thứ nhất chịu trách nhiệm khởi tạo bước đó và bên thứ hai chịu trách nhiệm thực hiện; trách nhiệm không được chuyển giao.

---

## 3.1.2 Chi tiết từng bước

### Bước 1 — Tiếp nhận nhà đầu tư và mở tài khoản

Nhà đầu tư đăng ký trên nền tảng FundLok, tại đó FundLok ghi nhận các thông tin cần thiết để vận hành quan hệ với nhà đầu tư và để thực hiện công việc theo hợp đồng uỷ quyền quản lý. Một cách riêng biệt và độc lập, VPBank thực hiện công tác thẩm định khách hàng (CDD) của riêng mình đối với nhà đầu tư và mở tài khoản cho nhà đầu tư theo cấu trúc được áp dụng tại Mục 1.8.

**Hai quy trình này là riêng biệt và không quy trình nào thay thế cho quy trình kia.** Việc tiếp nhận của FundLok phục vụ quan hệ trên nền tảng. Công tác thẩm định khách hàng của VPBank là công tác của chính ngân hàng, được thực hiện theo tiêu chuẩn của chính ngân hàng và trên cơ sở đánh giá của chính ngân hàng, và FundLok không đề nghị VPBank dựa vào quy trình hoặc hồ sơ của FundLok.

*Bên chịu trách nhiệm: VPBank — Tiếp nhận khách hàng (mở tài khoản) · FundLok — Vận hành tiếp nhận (đăng ký trên nền tảng).*

### Bước 2 — Tiếp nhận, thẩm định và niêm yết SME

SME đăng ký, cung cấp hồ sơ tài chính và hồ sơ pháp lý doanh nghiệp, và cung cấp bảo lãnh cá nhân của chủ doanh nghiệp. FundLok thực hiện thẩm định tín dụng, ấn định bậc lãi suất và công bố cơ hội đầu tư tới các nhà đầu tư.

VPBank không thực hiện thẩm định, không đưa ra đánh giá tín dụng và không tham gia vào quyết định cho vay. Quyết định cho vay thuộc về nhà đầu tư một cách duy nhất. Rủi ro tín dụng do nhà đầu tư gánh chịu và không bao giờ chuyển sang VPBank.

*Bên chịu trách nhiệm: FundLok — Tín dụng & Thẩm định cấp tín dụng.*

### Bước 3 — Thiết lập tài khoản ký quỹ

Trước khi có bất kỳ dòng tiền nào, tài khoản ký quỹ có mục đích sử dụng bị hạn chế cho khoản vay được mở tại VPBank. Tài khoản này được cấu hình với hai cơ chế kiểm soát không mang tính tuỳ chọn: một **danh sách tài khoản đích được phép**, để tiền chỉ có thể được giải toả tới một tài khoản của bên đi vay đã được xác thực hoặc tới một tài khoản chuyển tiền nguồn đã đăng ký của nhà đầu tư; và một **kênh truyền lệnh thanh toán theo cơ chế kiểm soát kép**, để không một cá nhân đơn lẻ nào tại FundLok có thể tạo ra một lượt chuyển tiền. Yêu cầu đối với cả hai cơ chế được quy định tại Mục 3.3.

FundLok đề nghị mở tài khoản và cung cấp danh sách tài khoản đích. VPBank mở và cấu hình tài khoản.

*Bên chịu trách nhiệm: VPBank — Vận hành lưu ký, theo đề nghị của FundLok.*

### Bước 4 — Ký kết hợp đồng cho vay

Hợp đồng cho vay được ký kết trực tiếp giữa nhà đầu tư và SME; nhà đầu tư trở thành bên cho vay chính thức và chủ sở hữu khoản vay. Song song, nhà đầu tư ký hợp đồng uỷ quyền quản lý với FundLok, và SME chấp thuận các điều khoản sử dụng nền tảng. VPBank không phải là một bên của hợp đồng cho vay.

FundLok tạo lập bộ hợp đồng và ghi nhận cam kết của nhà đầu tư đối với khoản vay.

*Bên chịu trách nhiệm: FundLok — Vận hành nền tảng & Pháp chế.*

### Bước 5 — Nộp vốn vào tài khoản ký quỹ

Mỗi nhà đầu tư nộp phần cam kết của mình vào tài khoản ký quỹ của khoản vay đó, bằng cách chuyển tiền từ **tài khoản đã đăng ký của chính mình** hoặc từ số dư đang có từ một khoản vay trước đó (Mục 1.4, giao dịch luân chuyển M8). VPBank ghi có vào tài khoản và thông báo cho FundLok; FundLok đối chiếu khoản ghi có với phần cam kết và ghi nhận tài khoản chuyển tiền nguồn.

Việc ghi nhận tài khoản chuyển tiền nguồn tại bước này là cơ sở khiến vòng kín có thể được thực thi về sau: tài khoản mà tiền đã chuyển đến từ đó là tài khoản duy nhất mà tiền có thể được hoàn trả về.

Các khoản tiền được ghi có vào tài khoản ký quỹ nhưng không thể quy thuộc cho một phần cam kết nào sẽ được giữ ở trạng thái chưa phân bổ và được báo cáo như một trường hợp ngoại lệ, thay vì được xử lý theo suy đoán.

*Bên chịu trách nhiệm: Nhà đầu tư (chuyển tiền) · VPBank — Vận hành lưu ký (ghi có và thông báo).*

### Bước 6 — Giải ngân cho SME

Việc giải ngân chỉ được tiến hành khi toàn bộ các điều kiện sau đây được thoả mãn: hợp đồng cho vay đã được ký, toàn bộ số vốn gốc đã cam kết đã được nhận vào tài khoản ký quỹ, và tài khoản nhận tiền của SME đã được xác thực và có trong danh sách tài khoản đích được phép. FundLok kiểm tra các điều kiện này và phát hành một lệnh thanh toán theo cơ chế kiểm soát kép. VPBank kiểm tra các điều kiện theo tiêu chuẩn riêng của mình và giải ngân vào tài khoản đã được xác thực của SME.

Phí giải ngân, khoảng 1% vốn gốc trước phí, được luân chuyển bên trong chính lệnh thanh toán này dưới hình thức một tỷ lệ mà VPBank có thể kiểm chứng. Phí này do SME chi trả, và nghĩa vụ trả nợ của SME được tính trên vốn gốc trước phí — nhờ đó nhà đầu tư được bảo toàn trọn vẹn phần vốn của mình.

Việc giải ngân chỉ trích từ số dư ký quỹ thuộc về khoản vay đó. Không có số dư gộp chung giữa các khoản vay, do đó một khoản vay không bao giờ có thể tài trợ cho một khoản vay khác.

*Bên chịu trách nhiệm: FundLok — Vận hành ngân quỹ (phát hành lệnh) · VPBank — Vận hành lưu ký (thực hiện).*

### Bước 7 — Thu chia sẻ doanh thu hằng ngày

Việc trả nợ là **chia sẻ doanh thu hằng ngày, không phải một lịch trả góp cố định.** Mỗi ngày làm việc, FundLok đọc doanh thu ngày liền trước của SME từ dữ liệu hoá đơn điện tử thông qua một nhà cung cấp T-VAN được cấp phép, tính tỷ lệ phần trăm đã thống nhất và phát hành cho SME một yêu cầu thanh toán qua nền tảng. SME nộp số tiền đó vào tài khoản ký quỹ bằng VietQR hoặc chuyển khoản ngân hàng, kèm mã tham chiếu do FundLok cung cấp. VPBank ghi có vào tài khoản và thông báo cho FundLok; FundLok quy thuộc khoản tiền nhận được và thực hiện đối chiếu.

Vì số tiền biến động theo hoạt động kinh doanh thực tế, một tuần kinh doanh chậm sẽ tạo ra số tiền thu nhỏ hơn và một tuần kinh doanh tốt sẽ tạo ra số tiền thu lớn hơn, trong khi tổng nghĩa vụ không thay đổi. Đây là yếu tố khiến sản phẩm khả dụng đối với các doanh nghiệp nhỏ có doanh thu biến động, và cũng là lý do chu kỳ được thiết lập theo ngày thay vì theo tháng.

Các khoản tiền nhận được không thể quy thuộc sẽ được giữ ở trạng thái chưa phân bổ và được báo cáo như một trường hợp ngoại lệ, thay vì được xử lý theo suy đoán. Cách xử lý phần vượt quá số dư còn phải trả là một nội dung cần xác nhận tại Mục 1.4.

*Bên chịu trách nhiệm: SME (thanh toán) · VPBank — Thu nợ (ghi có và thông báo).*

### Bước 8 — Phân bổ và hoàn trả cho nhà đầu tư

FundLok tính quyền lợi của từng nhà đầu tư từ các khoản tiền đã thu được và phát hành một lệnh thanh toán theo cơ chế kiểm soát kép. VPBank chuyển tiền tới **tài khoản chuyển tiền nguồn của từng nhà đầu tư, và chỉ tới tài khoản đó**. Đây chính là quy tắc vòng kín trong thực tiễn vận hành. **Khả dụng và chuyển tiền là hai việc khác nhau**: phần của nhà đầu tư trở nên khả dụng ngay khi phần phân bổ của ngày được hạch toán, và được chuyển tới tài khoản ngân hàng bên ngoài của nhà đầu tư khi nhà đầu tư yêu cầu. Tính khả dụng hằng ngày không đòi hỏi phải thực hiện một khoản chi trả ra ngoài mỗi ngày tới ngân hàng của từng nhà đầu tư.

Trường hợp việc chuyển tiền cho một nhà đầu tư không thành công, các lượt chuyển tiền còn lại vẫn được hoàn tất và số tiền không chuyển được vẫn nằm trong tài khoản ký quỹ để thực hiện lại. Số tiền đó không bao giờ được chuyển hướng, không bao giờ được áp dụng cho một nhà đầu tư khác và không bao giờ được áp dụng cho một khoản vay khác.

Phí quản lý khoản vay của FundLok được luân chuyển **bên trong chính lệnh thanh toán này**, dưới hình thức một tỷ lệ cố định của số tiền đang được phân bổ, để VPBank có thể kiểm chứng ngay trên nội dung của lệnh. Phí này do các nhà đầu tư chi trả và được trích từ phần lợi nhuận, không bao giờ trích từ vốn gốc. Loại phí còn lại của FundLok — phí giải ngân, do SME chi trả — được luân chuyển bên trong lệnh giải ngân tại Bước 6. Không loại phí nào có thể được phát hành như một giao dịch luân chuyển độc lập, và không loại phí nào có thể trích từ một số dư đang nằm yên. Mục 1.4.4 trình bày đầy đủ bốn điều kiện ràng buộc.

*Bên chịu trách nhiệm: FundLok — Vận hành ngân quỹ (phát hành lệnh) · VPBank — Vận hành lưu ký (thực hiện).*

### Bước 9 — Tất toán và giải toả tài khoản ký quỹ

Khi các khoản tiền cuối cùng đã được thu và hoàn trả, FundLok thực hiện công tác đối chiếu tất toán. Tài khoản ký quỹ phải được đối chiếu về số dư bằng không, được thống nhất giữa hồ sơ của FundLok và sao kê của VPBank, trước khi được giải toả. VPBank phát hành sao kê cuối cùng và giải toả tài khoản; FundLok đóng hồ sơ khoản vay và lưu giữ sao kê, kết quả đối chiếu và toàn bộ lịch sử lệnh thanh toán để phục vụ kiểm toán.

Trường hợp một tranh chấp hoặc một sự kiện vi phạm nghĩa vụ trả nợ khiến việc tất toán thông thường không thể thực hiện, tài khoản sẽ được giữ theo cơ chế nêu tại Mục 4.1 thay vì được giải toả.

*Bên chịu trách nhiệm: FundLok — Đối chiếu & Báo cáo · VPBank — Vận hành lưu ký (giải toả).*

---

## 3.1.3 Sơ đồ phân luồng trách nhiệm

Sơ đồ kèm theo mục này thể hiện chín bước theo hàng và bốn bên theo cột, với bên chịu trách nhiệm được nêu tên tương ứng với từng bước. Các ô được vẽ bằng đường viền nét gãy nêu rõ điều mà một bên chủ ý **không** thực hiện, nhờ đó ranh giới của từng vai trò có thể được nhận biết chỉ từ sơ đồ. Sơ đồ được thiết kế để vẫn dễ đọc ở khổ A4.

*[Chèn: `section-3.1-swimlane` — sơ đồ phân luồng chín bước, bốn bên, bên chịu trách nhiệm theo từng bước.]*

---

## 3.1.4 Các cơ chế kiểm soát được duy trì ở mọi bước

| Cơ chế kiểm soát | Cách thức hoạt động | Nơi quy định |
|---|---|---|
| Tài khoản đích được phép | Tiền chỉ ra khỏi tài khoản ký quỹ để đến một tài khoản của bên đi vay đã được xác thực, một tài khoản chuyển tiền nguồn đã đăng ký của nhà đầu tư, hoặc tài khoản thu phí của FundLok. | Mục 1.7, Mục 1.4.4, Mục 3.3 |
| Phí không bao giờ đứng độc lập | Một dòng phí chỉ được phép nằm bên trong một lệnh thanh toán có chi trả cho người thụ hưởng trong cùng một giao dịch luân chuyển, dưới hình thức một tỷ lệ mà VPBank có thể kiểm chứng. Phí không thể trích từ số dư nằm yên, và bị tạm ngừng trong thời gian tài khoản bị phong toả. | Mục 1.4.4 |
| Vòng kín | Phần hoàn trả của mỗi nhà đầu tư chỉ đi đến tài khoản mà nhà đầu tư đó đã chuyển tiền đi. | Mục 1.4 |
| Kiểm soát kép | Không một cá nhân đơn lẻ nào của FundLok có thể tạo ra một lượt chuyển tiền; mọi lệnh thanh toán đều cần hai bên được uỷ quyền. | Mục 3.3 |
| Tách biệt theo từng khoản vay | Tiền của mỗi khoản vay được giữ riêng biệt; không có số dư gộp chung và không bù trừ giữa các khoản vay. | Mục 1.8 |
| Ra lệnh, không chiếm giữ | FundLok phát hành lệnh thanh toán trong phạm vi các điều kiện do ngân hàng thực thi; FundLok không có quyền rút tiền. | Mục 1.3 |
| Thẩm định độc lập | VPBank thực hiện công tác thẩm định khách hàng của riêng mình và không được đề nghị dựa vào công tác thẩm định của FundLok. | Mục 1.7 |
| Dấu vết kiểm toán đầy đủ | Mọi lệnh thanh toán, khoản tiền nhận được và lượt chuyển tiền đều được ghi nhận và có thể đối chiếu với sao kê của VPBank. | Mục 3.5, Phụ lục C |
| Xử lý trường hợp ngoại lệ | Các khoản tiền nhận được không thể quy thuộc và các lượt chuyển tiền không thành công đều được giữ lại và báo cáo lên cấp trên, không bao giờ được xử lý theo suy đoán. | Mục 3.7 |

---

## 3.1.5 Các nội dung cần xác nhận

Theo quy tắc chung, không nội dung nào dưới đây được phỏng đoán. Mỗi nội dung đều có một bên chịu trách nhiệm được nêu tên và một thời hạn.

| # | Nội dung | Lý do quan trọng đối với mục này | Bên chịu trách nhiệm | Thời hạn |
|---|---|---|---|---|
| 1 | Tỷ lệ phần trăm chia sẻ doanh thu, và việc tỷ lệ này có thay đổi theo hạng hay không | Quyết định quy mô của từng lần thu tại Bước 7 | Lộc + Edward | 2026-08-12 |
| 2 | Mức phí quản lý khoản vay, và mức trần đã đăng ký đối với cả hai loại phí | Bước 6 và Bước 8 quy định các loại phí dưới hình thức tỷ lệ có thể kiểm chứng; các giá trị này phải được nêu rõ để VPBank thực thi | Lộc, cùng Edward | 2026-08-12 |
| 3 | Cấu trúc tài khoản được áp dụng — Phương án A hoặc Phương án B của Mục 1.8 | Quyết định việc phân bổ tại Bước 8 là một lượt chuyển tiền ngân hàng hay một bút toán hạch toán | Lộc + Edward (Mục 1.8) | 2026-08-12 |
| 4 | Sản phẩm tài khoản phong toả hiện có của VPBank có thể được sử dụng làm tài khoản ký quỹ có mục đích sử dụng bị hạn chế hay không, hoặc cần một cấu hình mới | Quyết định Bước 3 là cấu hình hay xây mới | Edward, cùng VPBank (Mục 3.3) | Chờ VPBank xác nhận |
| 5 | Hình thức của kênh truyền lệnh thanh toán theo cơ chế kiểm soát kép cho chương trình thử nghiệm | Bước 6 và Bước 8 phụ thuộc vào nội dung này | Edward (Mục 3.3) | Chờ VPBank xác nhận |
| 6 | Thời điểm chốt giao dịch, ngày giá trị và cách xử lý ngày không phải ngày làm việc | Quyết định những gì FundLok có thể cam kết với nhà đầu tư và SME về mặt thời gian tại Bước 6, Bước 7 và Bước 8 | Edward (Phụ lục C) | Chờ VPBank xác nhận |
| 7 | Định nghĩa "đã được xác thực" đối với tài khoản nhận tiền của SME và tài khoản chuyển tiền nguồn của nhà đầu tư | Cơ chế kiểm soát tài khoản đích được phép tại Bước 3 phụ thuộc vào định nghĩa này | Edward, cùng VPBank | 2026-08-07 |

---

*Các phụ thuộc: mục này phụ thuộc vào Mục 1.4 (dòng tiền) và Mục 1.5 (luồng dữ liệu), và phải luôn nhất quán với các Mục 1.3, 1.7, 1.8, 3.3 và 3.4.*


<!-- ══════════════════ PASTE INTO SECTION 3.3 ══════════════════ -->

> ## ▼ Mục 3.3 — VPBank cần xây — Giai đoạn 1
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.3.

# 3.3 Những nội dung VPBank cần xây dựng — Giai đoạn 1

*[NỘI DUNG — Edward. Bản thảo tiếng Anh phục vụ rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

Mục này trình bày, theo từng thành phần, những gì VPBank cần chuẩn bị sẵn sàng để chương trình thử nghiệm có thể vận hành. Phạm vi được giới hạn một cách có chủ đích: **Giai đoạn 1 không đòi hỏi bất kỳ hoạt động tích hợp API nào.** Mọi yêu cầu dưới đây đều có thể được đáp ứng bằng một kênh truyền lệnh thanh toán theo lô an toàn và một bản sao kê hằng ngày ở định dạng máy đọc được, cả hai đều là những năng lực thông thường của dịch vụ ngân hàng doanh nghiệp. Các phần công việc liên quan đến API, thông báo tức thời và đối chiếu tự động được quy định riêng tại Mục 3.4 và **không** phải là yêu cầu đối với chương trình thử nghiệm.

FundLok đã nắm được chương trình Open API mà VPBank đã công bố và không đề nghị sử dụng chương trình đó trong Giai đoạn 1. Chủ trương là khởi động quan hệ hợp tác trên những năng lực mà VPBank rất có thể đã đang vận hành, chứng minh luồng vận hành bằng dòng tiền thực ở khối lượng thấp, và chỉ sau đó mới quyết định liệu khối lượng có đủ để triển khai Giai đoạn 2 hay không.

Mỗi hạng mục được đánh dấu là **CẤU HÌNH** — năng lực hiện có được thiết lập để FundLok sử dụng — hoặc **XÂY MỚI** — nội dung mà VPBank sẽ cần phát triển. Các đánh dấu này là đánh giá của FundLok về những gì thường có sẵn trong hoạt động ngân hàng doanh nghiệp tại Việt Nam, không phải là khẳng định về hệ thống của VPBank; VPBank được đề nghị xác nhận hoặc điều chỉnh từng hạng mục. Trường hợp việc đánh dấu phụ thuộc vào câu trả lời cho câu hỏi tại 3.3.2, điều đó đã được nêu rõ.

Không có nội dung nào trong mục này đề nghị VPBank nhận rủi ro tín dụng, đưa ra hoặc rà soát bất kỳ quyết định cho vay nào, hoặc dựa vào các bước kiểm tra khách hàng của riêng FundLok. Việc thẩm định đối với các chủ tài khoản luôn thuộc trách nhiệm của chính VPBank.

---

## 3.3.1 Khối lượng mà Giai đoạn 1 được thiết kế để đáp ứng

Toàn bộ số liệu là ước tính nội bộ của FundLok cho chương trình thử nghiệm, lập ngày 5 August 2026, trên các giả định sau: 5–10 khoản vay được cấp vốn mỗi tháng; trung bình tám nhà đầu tư tham gia mỗi khoản vay, được suy ra từ nhóm khách hàng mục tiêu của FundLok là các văn phòng gia đình giải ngân khoảng USD 200,000 mỗi đơn vị cho mười đến mười lăm bên đi vay; kỳ hạn trung bình giả định là 12 tháng; và 22 ngày làm việc mỗi tháng.

Việc trả nợ được thực hiện theo hình thức **chia sẻ doanh thu hằng ngày**, không theo lịch trả nợ theo kỳ cố định: mỗi ngày làm việc, FundLok tính toán số tiền đến hạn dựa trên doanh số bán hàng của ngày trước đó của bên đi vay và yêu cầu thanh toán, và bên đi vay nộp tiền vào tài khoản ký quỹ (Mục 1.4). Do vậy, chu kỳ là hằng ngày kể từ khoản vay đầu tiên.

| Kỳ | Khoản vay đang hoạt động | Số lần ghi có tiền góp vốn của nhà đầu tư / tháng | Số lệnh giải ngân / tháng | Số lần ghi có trả nợ hằng ngày / tháng | Số biến động phân bổ / tháng | Số biến động phí / tháng |
|---|---|---|---|---|---|---|
| Tháng 1 | 5–10 | 40–80 | 5–10 | 110–220 | 880–1,760 | 110–220 |
| Tháng 3 | 15–30 | 40–80 | 5–10 | 330–660 | 2,640–5,280 | 330–660 |
| Tháng 6 | 30–60 | 40–80 | 5–10 | 660–1,320 | 5,280–10,560 | 660–1,320 |

Từ các số liệu này có thể rút ra ba điểm, và chúng định hình toàn bộ Giai đoạn 1.

Thứ nhất, **phân bổ là luồng duy nhất có khối lượng lớn.** Mọi luồng khác đều duy trì ở mức vài trăm trong suốt chương trình thử nghiệm. Ngoài ra, phân bổ chỉ phát sinh *lượt chuyển tiền tại ngân hàng* trong trường hợp Phương án B của Mục 1.8, theo đó mỗi nhà đầu tư có tài khoản ký quỹ riêng; theo Phương án A, đây chỉ là một bút toán trên sổ sách của FundLok và không phát sinh lượt chuyển tiền nào tại ngân hàng. Do đó, cột phân bổ nêu trên là trường hợp Phương án B, và yêu cầu D5 dưới đây chỉ tồn tại đối với phương án này.

Thứ hai, **lưu lượng thanh toán ra bên ngoài là nhỏ.** Tiền góp vốn của nhà đầu tư, giải ngân và rút tiền của nhà đầu tư cộng lại vẫn duy trì ở mức vài trăm mỗi tháng. Tất cả phần còn lại là lượt chuyển tiền giữa các tài khoản do chính VPBank quản lý.

Thứ ba, do FundLok soạn lập mỗi lô một cách tự động bằng chương trình, **số dòng trong một lô gây tốn kém không đáng kể cho VPBank; chính số lượng lô mới là yếu tố tiêu tốn công sức.** Một lô phân bổ hằng ngày vẫn chỉ là một lô, bất kể lô đó chứa 80 dòng hay 800 dòng.

Đó là lý do một kênh truyền lệnh theo lô an toàn là đủ cho Giai đoạn 1, và là lý do ngưỡng khởi động Giai đoạn 2 tại Mục 3.4 được biểu thị theo số lượt chuyển tiền mỗi tháng thay vì theo số khoản vay.

---

## 3.3.2 Câu hỏi quyết định phạm vi của toàn bộ các nội dung dưới đây

**Sản phẩm tài khoản phong toả hiện có của VPBank có thể được sử dụng làm tài khoản ký quỹ với mục đích sử dụng bị giới hạn hay không — và sản phẩm đó có thể thực thi danh sách tài khoản đích được phép ở phía ngân hàng hay không?**

Đây là câu hỏi then chốt trong đề xuất này. Nếu câu trả lời là có đối với cả hai nội dung, phần lớn phần A dưới đây chỉ là cấu hình và chương trình thử nghiệm có thể khởi động nhanh chóng. Nếu sản phẩm có tồn tại nhưng không thể giới hạn tài khoản đích, thì biện pháp kiểm soát quan trọng nhất trong cấu trúc này sẽ phải được xây mới, và điều đó thay đổi cả tiến độ lẫn vị thế rủi ro.

FundLok đề nghị VPBank trả lời cụ thể ba nội dung sau:

1. Có tồn tại sản phẩm tài khoản phong toả hoặc tài khoản ký quỹ hiện hữu có thể giữ tiền cho một mục đích bị giới hạn, tách biệt khỏi các tài khoản hoạt động của chính FundLok hay không?
2. Sản phẩm đó có thể được cấu hình để tiền chỉ được giải toả tới một danh sách tài khoản đích đã được xác định, với việc giới hạn do ngân hàng thực thi thay vì phụ thuộc vào tính kỷ luật trong việc phát hành lệnh thanh toán của FundLok hay không?
3. Danh sách tài khoản đích đó có thể được sửa đổi theo một quy trình có kiểm soát trong suốt thời gian tồn tại của tài khoản hay không, xét việc các nhà đầu tư tham gia một khoản vay theo thời gian?
4. Tài khoản ký quỹ có thực hiện được lệnh chuyển tiền **liên ngân hàng** tới tài khoản đích mở tại ngân hàng khác, và danh sách tài khoản đích được phép có chấp nhận các tài khoản đó hay không? Không bên tham gia nào bắt buộc phải mở tài khoản tại VPBank, nên nếu sản phẩm chỉ cho phép tài khoản đích trong cùng ngân hàng thì cơ chế này không thể vận hành.

---

## 3.3.3 A — Cấu hình tài khoản ký quỹ

Giả định mỗi khoản vay có một tài khoản ký quỹ bị giới hạn. Nếu Mục 1.8 lựa chọn một cấu trúc tài khoản khác, số lượng tài khoản sẽ thay đổi nhưng các yêu cầu dưới đây thì không.

| Ref | Yêu cầu | Cấu hình hay xây mới | Lý do cần thiết |
|---|---|---|---|
| A1 | Một tài khoản có mục đích sử dụng bị giới hạn cho mỗi khoản vay, giữ tiền của nhà đầu tư tách biệt khỏi các tài khoản hoạt động của chính FundLok và khỏi các khoản vay khác | CẤU HÌNH nếu sản phẩm tài khoản phong toả hiện có đáp ứng yêu cầu · nếu không thì XÂY MỚI — phụ thuộc vào 3.3.2 | Việc tách biệt theo từng khoản vay là nền tảng cấu trúc của toàn bộ thoả thuận; không có số dư gộp chung nghĩa là một khoản vay không bao giờ có thể cấp vốn cho khoản vay khác |
| A2 | Một danh sách tài khoản đích được phép do ngân hàng thực thi, theo đó tiền chỉ có thể ra khỏi tài khoản để chuyển tới (a) tài khoản của bên đi vay đã được xác minh, (b) tài khoản gốc của nhà đầu tư đã đăng ký, hoặc (c) tài khoản thu phí của FundLok — trường hợp cuối chỉ được thực hiện dưới hình thức một phần tỷ lệ của một lệnh thanh toán có chi trả cho người thụ hưởng trong cùng biến động đó | CẤU HÌNH nếu sản phẩm hiện có hỗ trợ · nếu không thì XÂY MỚI — phụ thuộc vào 3.3.2 | Đây là biện pháp kiểm soát khiến việc FundLok không thể sử dụng nguồn tiền nhàn rỗi trở thành một thực tế được ngân hàng thực thi thay vì chỉ là một lời cam kết. Mục 1.4.4 quy định các giới hạn về phí |
| A2a | Khả năng lưu tối thiểu **12 tài khoản đích cho mỗi tài khoản dự án**, và tối thiểu 700 tài khoản đích đang hiệu lực trên toàn danh mục ở mức khối lượng của chương trình thử nghiệm | CẤU HÌNH, hoặc XÂY MỚI nếu sản phẩm giới hạn số lượng tài khoản đích | Theo trường hợp tính toán tám nhà đầu tư, một dự án cần tám tài khoản đích của nhà đầu tư cộng với tài khoản của bên đi vay, tài khoản thu phí của FundLok và phần dự phòng. Một sản phẩm giới hạn số lượng tài khoản đích ở mức thấp sẽ phá vỡ mô hình một cách âm thầm |
| A2b | Danh sách tài khoản đích được phép phải chấp nhận **tài khoản mở tại ngân hàng khác**, và tài khoản ký quỹ phải thực hiện được lệnh chuyển tiền liên ngân hàng tới các tài khoản đó | CẤU HÌNH, hoặc XÂY MỚI nếu sản phẩm hiện có chỉ cho phép chuyển tiền trong cùng ngân hàng | Nhà đầu tư và bên đi vay giữ nguyên ngân hàng hiện tại của họ (Mục 1.8.3). Một số sản phẩm tài khoản phong toả chỉ cho phép chuyển tiền tới tài khoản trong cùng ngân hàng. Nếu sản phẩm của VPBank như vậy thì mô hình hoàn toàn không vận hành được — đó là lý do câu hỏi này được đặt cùng với 3.3.2 thay vì để phát hiện trong quá trình tích hợp |
| A3 | Việc sửa đổi có kiểm soát đối với danh sách tài khoản đích trong suốt thời gian tồn tại của tài khoản, với mỗi lần sửa đổi đều được phê duyệt và ghi nhận vào sổ ghi nhật ký | CẤU HÌNH | Các nhà đầu tư cam kết tham gia một khoản vay trong khoảng nhiều ngày hoặc nhiều tuần, do đó danh sách các tài khoản đích hoàn trả hợp lệ sẽ tăng lên trước khi hoàn tất việc cấp vốn |
| A4 | Cách đặt tên tài khoản phản ánh đúng tính chất bị giới hạn và tách biệt của tài khoản | CẤU HÌNH | Giúp thoả thuận này được thể hiện rõ ràng trên các bản sao kê cũng như trong bất kỳ hoạt động kiểm toán hoặc tranh chấp nào |
| A5 | Việc mở tài khoản cho một nhóm khoản vay, và việc đóng tài khoản có số dư bằng không khi khoản vay tất toán | CẤU HÌNH — mang tính quy trình hơn là hệ thống ở mức khối lượng của chương trình thử nghiệm | Ở mức 5–10 tài khoản dự án mỗi tháng, cộng với khoảng 1–10 tài khoản của nhà đầu tư mỗi tháng theo Phương án B, việc mở tài khoản có thể được xử lý như một quy trình vận hành. Việc tự động hoá chưa cần thiết cho đến khi số tài khoản mở mới vượt khoảng 25 tài khoản mỗi tháng (Mục 3.4, P6) |
| A6 | Không thấu chi, không hạn mức tín dụng và không bù trừ đối với tài khoản ký quỹ | CẤU HÌNH | Nguồn tiền này không thuộc về FundLok, do đó không được sử dụng để bảo đảm hoặc bù trừ cho bất kỳ nghĩa vụ nào |

---

## 3.3.4 B — Kênh truyền lệnh thanh toán và kiểm soát kép

| Ref | Yêu cầu | Cấu hình hay xây mới | Lý do cần thiết |
|---|---|---|---|
| B1 | Một kênh an toàn để FundLok gửi một lô lệnh thanh toán đối với một tài khoản ký quỹ được chỉ định cụ thể | CẤU HÌNH — kênh ngân hàng doanh nghiệp hiện có là đủ | Chuyển tải hoạt động giải ngân (Bước 6) và phân phối (Bước 8). Không cần API ở mức khối lượng của chương trình thử nghiệm |
| B2 | Cơ chế phê duyệt hai người đối với mọi lệnh thanh toán, với hai vai trò do hai cá nhân được chỉ định khác nhau tại FundLok đảm nhiệm | CẤU HÌNH — quyền hạn tiêu chuẩn trong dịch vụ ngân hàng doanh nghiệp | Bảo đảm không một cá nhân nào tại FundLok có thể tự mình khiến dòng tiền dịch chuyển. Đây là biện pháp kiểm soát do VPBank thực thi, không phải do FundLok tự chứng nhận |
| B3 | Xác nhận đã tiếp nhận mỗi lô, và kết quả theo từng lượt chuyển tiền cho mọi dòng trong lô đó | CẤU HÌNH | Một lô gồm 200 lượt chuyển tiền trong đó có ba giao dịch thất bại phải phân biệt được với một lô mà tất cả đều thành công; FundLok phải biết ba giao dịch đó là những giao dịch nào |
| B4 | Lý do từ chối ở cấp độ từng dòng, theo một hệ thống mã thống nhất | CẤU HÌNH | Quyết định việc FundLok sẽ gửi lại lệnh, chỉnh sửa tài khoản đích, hay chuyển vụ việc lên cấp cao hơn |
| B5 | Chống trùng lặp lệnh — một lô hoặc một dòng được gửi lại với cùng số tham chiếu của FundLok không được phát sinh khoản thanh toán thứ hai | XÂY MỚI nếu kênh hiện tại chưa thực thi tính duy nhất đối với số tham chiếu của khách hàng | Đây là dạng lỗi duy nhất không có biện pháp khắc phục trọn vẹn. Một khoản phân phối bị trùng lặp sẽ chuyển tiền của nhà đầu tư hai lần và không thể thu hồi đơn phương |
| B6 | Các lượt chuyển tiền thất bại phải để lại nguồn tiền trong tài khoản ký quỹ | CẤU HÌNH | Một khoản hoàn trả thất bại phải được giữ khoanh vùng để thực hiện lại, tuyệt đối không được chuyển hướng hoặc sử dụng cho mục đích khác |

---

## 3.3.5 C — Luồng cung cấp sao kê

| Ref | Yêu cầu | Cấu hình hay xây mới | Lý do cần thiết |
|---|---|---|---|
| C1 | Một bản sao kê hằng ngày cho mỗi tài khoản ký quỹ ở định dạng máy đọc được, có thể truy xuất mà không cần can thiệp thủ công | CẤU HÌNH | Cơ sở cho hoạt động đối chiếu hằng ngày của FundLok. Nếu không có, việc đối chiếu sẽ phải làm thủ công và sai sót sẽ chỉ bộc lộ muộn |
| C2 | Một mã nhận dạng giao dịch duy nhất và ổn định trên mỗi dòng sao kê, không thay đổi qua các lần truy xuất | CẤU HÌNH, hoặc XÂY MỚI nếu mã nhận dạng không ổn định | FundLok phải có khả năng nhận ra cùng một giao dịch vào hai ngày khác nhau mà không tính trùng giao dịch đó |
| C3 | Tên người chuyển tiền, tài khoản người chuyển tiền và toàn bộ nội dung tham chiếu thanh toán được giữ nguyên trên mọi khoản ghi có đến | CẤU HÌNH, hoặc XÂY MỚI nếu nội dung tham chiếu bị cắt ngắn | Đây là cách một khoản thanh toán đến được quy thuộc cho đúng nhà đầu tư và đúng khoản vay. Nếu nội dung tham chiếu bị cắt ngắn hoặc thông tin người chuyển tiền bị loại bỏ, việc quy thuộc sẽ thất bại và tiền sẽ nằm lại mà không được phân bổ |
| C4 | Số dư của từng tài khoản ký quỹ, khả dụng tối thiểu theo tần suất hằng ngày | CẤU HÌNH | Được kiểm tra trước mỗi lệnh giải ngân và được đối chiếu với sổ sách của FundLok |
| C5 | Việc truy xuất sao kê theo một khoảng thời gian được yêu cầu, không chỉ riêng ngày gần nhất | CẤU HÌNH | Cần thiết để đối chiếu lại một kỳ sau bất kỳ điều chỉnh nào, và để cung cấp chứng cứ trong trường hợp có tranh chấp |

Hạng mục C3 cần được nhấn mạnh. Trong tất cả các nội dung của mục này, một nội dung tham chiếu thanh toán bị cắt ngắn hoặc thiếu thông tin người chuyển tiền là yêu cầu mà sự thiếu hụt sẽ gây ra khó khăn vận hành hằng ngày lớn nhất, bởi mỗi khoản ghi có không thể quy thuộc đều trở thành một vụ việc phải điều tra thủ công trong khi nhà đầu tư đang chờ được xác nhận.

---

## 3.3.6 D — Thu nợ qua VietQR

| Ref | Yêu cầu | Cấu hình hay xây mới | Lý do cần thiết |
|---|---|---|---|
| D1 | Thu tiền qua VietQR vào một tài khoản ký quỹ được chỉ định | CẤU HÌNH | Phương thức thực tiễn để một SME trả nợ, và để các nhà đầu tư góp vốn, mà không phải nhập lệnh chuyển tiền thủ công |
| D2 | Một số tham chiếu do FundLok cung cấp được chuyển tải xuyên suốt khoản thanh toán VietQR và được giữ nguyên vẹn trên dòng sao kê | CẤU HÌNH, hoặc XÂY MỚI nếu trường tham chiếu không được chuyển tiếp | Nếu không có, một khoản thu qua VietQR không thể được quy thuộc cho một khoản vay và một kỳ trả nợ, điều này làm mất hoàn toàn ý nghĩa của việc sử dụng VietQR |
| D3 | Số tài khoản ảo riêng cho từng người thanh toán bên dưới một tài khoản ký quỹ, để mỗi nhà đầu tư và mỗi bên đi vay thanh toán vào một số tài khoản riêng biệt | XÂY MỚI — rất đáng mong muốn, nhưng không thiết yếu đối với Giai đoạn 1 | Giúp việc quy thuộc trở nên tất định và loại bỏ hoàn toàn lỗi đối sánh nội dung tham chiếu. Theo đánh giá của FundLok, đây là năng lực có giá trị cao nhất trong toàn bộ hoạt động tích hợp, và nó sẽ giảm tải vận hành cho cả hai bên |
| D4 | Thông báo tức thời về một khoản ghi có đến | KHÔNG YÊU CẦU TRONG GIAI ĐOẠN 1 — xem Mục 3.4 | Ở mức khối lượng của chương trình thử nghiệm, việc truy xuất bản sao kê hằng ngày là đủ. Cái giá phải trả là khoảng thời gian trễ giữa lúc nhà đầu tư thanh toán và lúc nhà đầu tư thấy cam kết của mình được xác nhận |
| D5 | Khả năng thực hiện một **lô phân bổ nội bộ hằng ngày** giữa các tài khoản của nhà đầu tư mở tại VPBank — ở mức khoảng 2,200 biến động mỗi tháng khi có 10 khoản vay đang hoạt động, tăng lên 13,200 khi có 60 khoản vay | CẤU HÌNH nếu kênh truyền lệnh theo lô không có giới hạn số dòng trên thực tế · nếu không thì XÂY MỚI | Chỉ cần thiết nếu áp dụng Phương án B của Mục 1.8, theo đó mỗi nhà đầu tư có tài khoản ký quỹ riêng. Theo Phương án A, việc phân bổ chỉ là một bút toán trên sổ sách và không phát sinh lượt chuyển tiền nào tại ngân hàng |

---

## 3.3.7 E — Truy cập, an toàn thông tin và kiểm soát

| Ref | Yêu cầu | Cấu hình hay xây mới | Lý do cần thiết |
|---|---|---|---|
| E1 | Các người dùng FundLok được chỉ định danh tính và được cấp quyền tách biệt, để người lập lệnh và người phê duyệt không thể là cùng một người | CẤU HÌNH | Làm cho biện pháp kiểm soát kép tại B2 trở nên thực chất thay vì chỉ mang tính hình thức thủ tục |
| E2 | Việc thu hồi kịp thời quyền hạn của một người dùng khi FundLok thông báo về thay đổi nhân sự | CẤU HÌNH | Một nhân viên thôi việc phải mất khả năng phê duyệt một lượt chuyển tiền ngay trong cùng ngày |
| E3 | Vết kiểm toán ở phía ngân hàng đối với mọi lệnh thanh toán được tiếp nhận, được phê duyệt, được thực hiện hoặc bị từ chối | CẤU HÌNH | Cung cấp bản ghi độc lập để đối chiếu với vết kiểm toán của chính FundLok, và bộ chứng cứ trong trường hợp có tranh chấp |
| E4 | Kênh truyền lệnh thanh toán và việc truy xuất sao kê được mã hoá trên đường truyền | CẤU HÌNH | Dữ liệu cá nhân và dữ liệu tài chính đang trên đường truyền, theo Mục 4.4 |
| E5 | Hoạt động thẩm định khách hàng (CDD) của chính VPBank đối với các chủ tài khoản, theo tiêu chuẩn của chính VPBank | CẤU HÌNH — quy trình hiện có của VPBank | Các bước kiểm tra của FundLok phục vụ mục đích của FundLok và không được đưa ra để thay thế cho các bước kiểm tra của ngân hàng |

---

## 3.3.8 Tóm lược

| Đánh dấu | Số lượng | Các hạng mục |
|---|---|---|
| CẤU HÌNH | 18 | A3, A4, A5, A6, B1, B2, B3, B4, B6, C1, C4, C5, D1, E1, E2, E3, E4, E5 — trong đó A5 mang tính quy trình hơn là hệ thống |
| CẤU HÌNH hoặc XÂY MỚI, tuỳ thuộc vào năng lực hiện có | 2 | A2a (dung lượng danh sách tài khoản đích), D5 (năng lực phân bổ nội bộ hằng ngày — chỉ áp dụng cho Phương án B) |
| CẤU HÌNH hoặc XÂY MỚI, tuỳ thuộc vào câu trả lời cho 3.3.2 | 2 | A1, A2 |
| CẤU HÌNH hoặc XÂY MỚI, tuỳ thuộc vào năng lực hiện hữu | 3 | C2, C3, D2 |
| XÂY MỚI | 2 | B5 (chống trùng lặp lệnh), D3 (tài khoản ảo riêng cho từng người thanh toán — đáng mong muốn, không thiết yếu) |
| Không yêu cầu trong Giai đoạn 1 | 1 | D4 (thông báo tức thời) |

Tổng cộng: 28 yêu cầu.

Bản chất của đề nghị: **phần lớn tuyệt đối các nội dung của Giai đoạn 1 là việc cấu hình những năng lực mà một ngân hàng doanh nghiệp đã đang vận hành.** Hai hạng mục có thể trở thành công việc xây mới đáng kể là danh sách tài khoản đích được phép (A2) và cơ chế chống trùng lặp lệnh (B5), và cả hai đều là những biện pháp kiểm soát bảo vệ VPBank không kém gì bảo vệ FundLok.

---

## 3.3.9 Những nội dung FundLok không đề nghị trong Giai đoạn 1

Được nêu rõ ràng để phạm vi của đề nghị không gây bất kỳ sự mơ hồ nào:

- Không có bất kỳ hình thức tích hợp API nào.
- Không có thông báo tức thời hoặc thông báo đẩy về các khoản ghi có đến.
- Không có hoạt động đối chiếu tự động ở phía VPBank — FundLok thực hiện việc đối chiếu, dựa trên bản sao kê của VPBank.
- Không có tài khoản riêng cho từng nhà đầu tư hoặc từng bên đi vay, trừ khi Mục 1.8 lựa chọn cấu trúc đó.
- Không có hoạt động đánh giá tín dụng, thẩm định giá, xếp hạng tín nhiệm hoặc quyết định cho vay.
- Không có hoạt động thu hồi nợ, cưỡng chế bảo lãnh hoặc hành động pháp lý đối với bên đi vay.
- Không có hoạt động phân xử tranh chấp.
- Không có khoản đóng góp nào vào chi phí xây dựng hoặc chi phí vận hành của chính FundLok.

---

## 3.3.10 Các nội dung cần xác nhận

| # | Nội dung | Ý nghĩa đối với mục này | Bên phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | Liệu VPBank có thể thực hiện phân bổ nội bộ hằng ngày ở các mức khối lượng nêu tại 3.3.1, và mức giá áp dụng | Quyết định việc yêu cầu D5 có khả thi hay không, và do đó quyết định Phương án B của Mục 1.8 có khả dụng hay không | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 2 | Câu trả lời cho câu hỏi bốn phần tại 3.3.2 | Quyết định A1 và A2 là cấu hình hay xây mới, và do đó quyết định tiến độ Giai đoạn 1 | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 3 | Liệu kênh ngân hàng doanh nghiệp hiện có có hỗ trợ tính duy nhất đối với số tham chiếu do khách hàng cung cấp | Quyết định B5 là cấu hình hay xây mới | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 4 | Định dạng sao kê, tính ổn định của mã nhận dạng giao dịch, và độ dài tối đa của nội dung tham chiếu thanh toán được giữ nguyên | Quyết định C2, C3 và D2 là cấu hình hay xây mới | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 5 | Liệu tài khoản ảo riêng cho từng người thanh toán (D3) có khả thi hay không, và thuộc giai đoạn nào | Theo đánh giá của FundLok, đây là năng lực có giá trị cao nhất hiện có; rất nên biết sớm ngay cả khi được lùi lại sau | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 6 | Cấu trúc tài khoản được lựa chọn tại Mục 1.8 | Quyết định liệu yêu cầu D5 có được áp dụng hay không, và số lượng tài khoản cần mở | Loc + Edward | 2026-08-12 |
| 7 | Số lượng tài khoản đích tối đa cho mỗi tài khoản (yêu cầu A2a) | Với tám nhà đầu tư, một dự án cần mười hai tài khoản đích; một sản phẩm giới hạn ở mức năm sẽ phá vỡ mô hình một cách âm thầm | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 8 | Thời điểm ngừng nhận lệnh, việc xác định ngày giá trị và cách xử lý ngày không phải ngày làm việc đối với kênh truyền lệnh thanh toán | Quyết định những gì FundLok có thể cam kết với các nhà đầu tư và các bên đi vay về mặt thời gian | VPBank, theo đề nghị của Edward — được ghi nhận tại Phụ lục C | Chờ VPBank xác nhận |

---

*Các nội dung phụ thuộc: sự xác nhận của VPBank, theo 3.3.2. Nhất quán với Mục 3.1 (quy trình), Mục 1.7 (giới hạn vai trò), Mục 1.8 (cấu trúc tài khoản) và Mục 3.4 (Giai đoạn 2). Ước tính khối lượng công việc cho từng thành phần nêu trên được trình bày tại Mục 3.6.*


<!-- ══════════════════ PASTE INTO SECTION 3.4 ══════════════════ -->

> ## ▼ Mục 3.4 — VPBank cần xây — Giai đoạn 2
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.4.

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


<!-- ══════════════════ PASTE INTO SECTION 3.5 ══════════════════ -->

> ## ▼ Mục 3.5 — FundLok xây & chi trả
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.5.

# 3.5 FundLok xây dựng những gì — và chi trả cho những gì

*[NỘI DUNG — Edward. Bản thảo tiếng Anh phục vụ rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

Toàn bộ phần thuộc phía FundLok trong quan hệ đối tác này đều do FundLok xây dựng, vận hành và chi trả. VPBank chỉ được đề nghị cung cấp dịch vụ lưu ký và thanh toán (được quy định tại Mục 3.3) và không có nội dung nào khác: không phát triển nền tảng, không phát triển tích hợp thay cho FundLok, và không góp phần vào chi phí xây dựng hoặc chi phí vận hành của FundLok.

Mục này liệt kê các cấu phần thuộc trách nhiệm của FundLok, được phân tách thành **những cấu phần đã tồn tại và đang hoạt động hiện nay** và **những cấu phần FundLok sẽ xây dựng cho quan hệ đối tác này**. Sự phân biệt này có ý nghĩa quan trọng vì nó cho thấy phần nền tảng đã đi vào vận hành đến mức nào: những bộ phận của hệ thống mang rủi ro về tính chính xác cao nhất — bộ máy thẩm định, quy trình xác minh danh tính và sổ sách ghi kép — đều đã được xây dựng, kiểm thử và hợp nhất mã nguồn, chứ không chỉ ở trạng thái dự kiến. Phần còn lại phải xây dựng chủ yếu là công việc kết nối giữa sổ sách hiện có của FundLok và tài khoản lưu ký của VPBank.

---

## 3.5.1 Đã xây dựng và đang vận hành

| # | Cấu phần | Chức năng | Tình trạng |
|---|---|---|---|
| 1 | API nền tảng & cổng thông tin cho nhà đầu tư / SME | Đăng ký, xác thực, kiểm soát truy cập theo vai trò, quản lý hồ sơ người dùng và hồ sơ doanh nghiệp, bộ phận hỗ trợ vận hành nội bộ dành cho quản trị viên | Đã đưa vào hoạt động chính thức. Xác thực dựa trên mã thông báo (token) có cơ chế làm mới và thu hồi, băm mật khẩu bằng Argon2, phân quyền theo vai trò trên toàn bộ các điểm cuối (endpoint) |
| 2 | Xác minh danh tính — KYC và KYB | Xác minh danh tính nhà đầu tư, xác minh doanh nghiệp bao gồm đăng ký doanh nghiệp, mã giấy phép và kiểm tra người đại diện theo pháp luật, thu nhận tài liệu và đối sánh khuôn mặt, thông qua một đơn vị cung cấp dịch vụ xác minh bên thứ ba đã được tích hợp | Đã đưa vào hoạt động chính thức. Là phân hệ đơn lẻ lớn nhất trong nền tảng; được xây dựng theo bản đặc tả riêng |
| 3 | Bộ máy thẩm định & xếp hạng tín dụng | Chấm điểm tất định theo nhiều yếu tố đối với từng đơn đề nghị của SME, cho ra hạng tín nhiệm, bậc lãi suất và mức giá, cùng với dữ liệu tham chiếu theo ngành, các tham số hiệu chuẩn và một lượt chấm điểm được khoá lại để các điều kiện không thể thay đổi sau khi phê duyệt | Đã đưa vào hoạt động chính thức. Được bảo đảm bằng một bộ dữ liệu kiểm thử chuẩn cố định (golden set) và một bảng tham chiếu theo ngành gồm 105 giá trị |
| 4 | Sổ sách ghi kép | Bản ghi chỉ bổ sung (append-only) đối với mọi lượt chuyển tiền, số dư được tính bằng cách tổng hợp thay vì lưu trữ, tính bất biến được cưỡng chế cả ở lớp cơ sở dữ liệu lẫn trong mã ứng dụng, nguồn vốn được tách biệt theo từng khoản vay và việc bù trừ chéo giữa các khoản vay bị chính mã nguồn từ chối | Đã đưa vào hoạt động chính thức. Việc chỉnh sửa được thực hiện bằng cách ghi một bút toán đảo; không bản ghi nào có thể bị sửa hoặc xoá |
| 5 | Sàn giao dịch, sổ lệnh & hợp đồng cho vay | Công bố các cơ hội đã được thẩm định, ghi nhận cam kết của nhà đầu tư, tạo lập hợp đồng và quản lý trạng thái chu kỳ sống của khoản vay | Đã đưa vào hoạt động chính thức |
| 6 | Quản lý tài liệu | Tải lên, lưu trữ và truy xuất tài liệu một cách an toàn phục vụ xác minh và lập hồ sơ khoản vay, sử dụng cơ chế truy cập được ký trước (pre-signed) vào bộ lưu trữ đối tượng | Đã đưa vào hoạt động chính thức |
| 7 | Ghi nhật ký kiểm toán | Vết kiểm toán được ghi lại đối với các hành vi quản trị và hành vi tài chính, được lưu giữ để phục vụ kiểm tra | Đã đưa vào hoạt động chính thức |
| 8 | Bộ kiểm thử tự động & quy trình triển khai | Các bài kiểm thử hồi quy được chạy đối với mọi thay đổi, cùng với việc dựng bản và triển khai tự động lên hạ tầng đám mây được quản lý và các thông tin bí mật được lưu giữ trong một kho bí mật được quản lý | Đã đưa vào hoạt động chính thức |

---

## 3.5.2 Sẽ xây dựng cho quan hệ đối tác này

Mỗi cấu phần dưới đây đều được gắn với bước cụ thể trong quy trình đầu-cuối (Mục 3.1) mà cấu phần đó phục vụ, để danh sách này có thể được kiểm chứng đối chiếu với quy trình thay vì phải tin tưởng vô điều kiện.

| # | Cấu phần | Chức năng | Phục vụ bước |
|---|---|---|---|
| 1 | Bộ máy xử lý lệnh thanh toán có kiểm soát kép | Lập và truyền lệnh thanh toán tới VPBank, cưỡng chế phê duyệt kép để không một cá nhân đơn lẻ nào có thể tạo ra một lượt chuyển tiền, kèm khoá chống trùng lặp lệnh trên mọi lệnh thanh toán để một lệnh được gửi lặp lại không bao giờ có thể tạo ra khoản thanh toán thứ hai | 6, 8 |
| 2 | Mở và quản lý chu kỳ sống của tài khoản ký quỹ | Đề nghị mở tài khoản ký quỹ bị hạn chế cho từng khoản vay, ghi nhận tài khoản đó gắn với khoản vay, quản lý danh sách tài khoản đích được phép, và đóng tài khoản khi khoản vay tất toán — với một chốt phê duyệt nội bộ trước khi tài khoản được đưa vào sử dụng | 3, 9 |
| 3 | Bản ghi thanh toán qua ngân hàng & đối chiếu tự động | Liên kết mọi bút toán trên sổ sách với giao dịch thanh toán tương ứng tại ngân hàng, đối chiếu sao kê của VPBank với sổ sách của FundLok theo một chu kỳ đã xác định, và ghi nhận mọi chênh lệch thành trường hợp ngoại lệ thay vì điều chỉnh sổ sách cho khớp | 5, 7, 9 |
| 4 | Đối sánh thu nợ | Đối sánh từng khoản tiền về với khoản vay và ngày chính xác, đối chiếu khoản đó với số tiền đã yêu cầu, và chuyển các khoản tiền về không thể quy thuộc sang danh sách trường hợp ngoại lệ thay vì hạch toán theo phỏng đoán | 7 |
| 5 | Bộ máy phân phối | Tính phần quyền lợi theo tỷ lệ của từng nhà đầu tư, lập lô lệnh thanh toán tương ứng, theo dõi từng lượt chuyển tiền một cách riêng biệt, và giữ lại số tiền chuyển không thành công trong tài khoản ký quỹ để thực hiện lại thay vì chuyển hướng số tiền đó | 8 |
| 6 | Đăng ký & xác minh tài khoản thanh toán | Đăng ký tài khoản ngân hàng riêng hoặc ví điện tử được cấp phép của từng bên, ghi nhận tài khoản chuyển tiền nguồn giúp vòng kín có thể được cưỡng chế, và xác nhận tài khoản thuộc về bên đã được xác minh trước khi tài khoản đó trở thành một tài khoản đích được phép | 2, 5, 8 |
| 7 | Bảng điều khiển vận hành & đối chiếu | Cung cấp cho nhân sự vận hành của FundLok khả năng theo dõi trực tiếp số dư ký quỹ, trạng thái lệnh thanh toán, tình trạng đối chiếu và các trường hợp ngoại lệ còn tồn, để một sai lệch được nhìn thấy ngay trong ngày phát sinh | Tất cả |
| 8 | Phân hệ dư nợ & báo cáo | Theo dõi dư nợ còn lại của từng bên đi vay trên các khoản vay và tạo lập các báo cáo vận hành và báo cáo danh mục mà FundLok yêu cầu | 2, 9 |
| 9 | Các biện pháp kiểm soát bảo vệ dữ liệu | Ghi nhận việc thu thập sự đồng ý và việc rút lại sự đồng ý, cưỡng chế thời hạn lưu giữ, cùng các bằng chứng về kiểm soát truy cập và ghi nhật ký được yêu cầu theo Mục 4.4 | 1, 2 |
| 10 | Tích hợp T-VAN | Thu nhận hằng ngày dữ liệu bán hàng ở cấp hoá đơn của từng bên đi vay từ một đơn vị cung cấp T-VAN được cấp phép, đây chính là nguồn của con số doanh thu dùng để tính khoản trả nợ hằng ngày | 7 |
| 11 | Bộ máy chia sẻ doanh thu hằng ngày | Tính số tiền phải trả của từng bên đi vay từ doanh thu của ngày liền trước, phát hành yêu cầu thanh toán thông qua nền tảng và kênh thông báo của nền tảng, và theo dõi nghĩa vụ còn lại so với vốn gốc trước phí | 7 |

Sổ sách hiện có của FundLok là nền móng mà cả mười một cấu phần đều đặt trên đó. Các cấu phần từ 1 đến 5 là công việc kết nối giữa sổ sách đó và tài khoản lưu ký của VPBank; các cấu phần từ 6 đến 9 thuộc phạm vi nội bộ của FundLok; các cấu phần 10 và 11 triển khai cơ chế chia sẻ doanh thu hằng ngày được quy định tại Mục 1.4 và là phần bổ sung đơn lẻ lớn nhất vào khối lượng xây dựng của FundLok.

Các cấu phần 10 và 11 cần được lưu ý riêng. Cơ chế trả nợ là một **hình thức chia sẻ doanh thu hằng ngày, không phải một lịch trả góp** — số tiền phải trả mỗi ngày được suy ra từ doanh số bán hàng thực tế của ngày liền trước của bên đi vay, chứ không được ấn định ngay khi phát sinh khoản vay. Điều đó khiến việc tích hợp T-VAN trở thành một điều kiện phụ thuộc của chính dòng tiền, chứ không chỉ là một tiện ích phục vụ báo cáo: không có nó thì không có con số nào để thu nợ. Cả hai cấu phần đều chưa được khởi động.

---

## 3.5.3 Chi phí

**FundLok chịu toàn bộ chi phí của mọi cấu phần trong cả hai bảng nêu trên** — xây dựng, kiểm thử, triển khai, lưu trữ vận hành (hosting), phí xác minh của bên thứ ba, cùng chi phí vận hành và hỗ trợ thường xuyên. FundLok không đề nghị VPBank đóng góp, chia sẻ chi phí hay cung cấp nguồn lực phát triển cho bất kỳ nội dung nào trong đó.

Phần xây dựng của chính VPBank được quy định riêng tại Mục 3.3 và 3.4, và VPBank tự định giá phần công việc đó. Các ước tính khối lượng công việc cho những cấu phần nêu trên được trình bày tại Mục 3.6.

---

## 3.5.4 Cơ sở của các nội dung trình bày tại mục này

Theo quy tắc chung rằng mọi số liệu đều phải có nguồn: các số lượng và mô tả tình trạng tại Mục 3.5.1 được lấy từ việc kiểm tra trực tiếp kho mã nguồn của FundLok ngày 4 August 2026. Nền tảng bao gồm 23 phân hệ ứng dụng và khoảng 8,200 dòng mã ứng dụng, được bao phủ bởi 160 bài kiểm thử tự động, cùng 14 lượt di trú cơ sở dữ liệu đã được áp dụng. "Đã đưa vào hoạt động chính thức" nghĩa là đã được hợp nhất vào nhánh chính, được bộ kiểm thử tự động bao phủ, và được triển khai qua quy trình tự động — không phải ở dạng nguyên mẫu.

---

## 3.5.5 Các nội dung cần xác nhận

| # | Nội dung | Ý nghĩa đối với mục này | Bên phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | Bảng điều khiển vận hành (cấu phần 7) là bắt buộc đối với chương trình thử nghiệm (pilot) hay có thể triển khai sau chương trình thử nghiệm (pilot) | Ở quy mô khối lượng của chương trình thử nghiệm (pilot), việc xử lý các trường hợp ngoại lệ có thể được thực hiện từ các màn hình quản trị hiện có, điều này sẽ loại bỏ một cấu phần khỏi phạm vi của chương trình thử nghiệm (pilot) | Edward | 2026-08-07 |
| 2 | Phân hệ dư nợ và báo cáo (cấu phần 8) thuộc phạm vi của chương trình thử nghiệm (pilot) hay được hoãn lại | Phụ thuộc vào các báo cáo mà VPBank mong muốn nhận được trong thời gian chương trình thử nghiệm (pilot) | Edward, cùng với VPBank | Chờ VPBank xác nhận |
| 3 | Khu vực lưu trữ vận hành đối với dữ liệu cá nhân, và quan điểm về việc xử lý dữ liệu trong nước | Được nêu tại Mục 4.4; ảnh hưởng đến hạng mục hạ tầng của mục này. Việc triển khai hiện nay đặt tại một địa điểm đám mây trong khu vực nhưng ngoài lãnh thổ Việt Nam, do đó một cam kết xử lý trong nước là một cuộc di dời hạ tầng chứ không phải sự mô tả hiện trạng | Edward | 2026-08-07 |

---

*Điều kiện phụ thuộc: không có. Thống nhất với Mục 3.1 (quy trình), Mục 3.3 và 3.4 (phần xây dựng của VPBank), Mục 3.6 (khối lượng công việc) và Mục 4.4 (bảo vệ dữ liệu).*


<!-- ══════════════════ PASTE INTO SECTION 3.6 ══════════════════ -->

> ## ▼ Mục 3.6 — Ước lượng khối lượng & chi phí
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.6.

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

---

*Phụ thuộc: Mục 3.3 (Giai đoạn 1) và Mục 3.4 (Giai đoạn 2). Thống nhất với Mục 3.5 (phần xây dựng của FundLok) và Mục 3.7 (tích hợp và kiểm thử).*


<!-- ══════════════════ PASTE INTO SECTION 3.7 ══════════════════ -->

> ## ▼ Mục 3.7 — Tích hợp & kiểm thử
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 3.7.

# 3.7 Tích hợp và kiểm thử

*[NỘI DUNG — Edward. Bản thảo tiếng Anh để rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

Mục này trình bày phương thức đưa hoạt động tích hợp giữa FundLok và VPBank vào vận hành: các giai đoạn phải trải qua, các giao dịch cụ thể được sử dụng để kiểm thử, phương pháp chứng minh tính đúng đắn của công tác đối chiếu, và các tiêu chí phải được đáp ứng trước khi dòng tiền thật được chuyển ở quy mô của chương trình thử nghiệm (pilot).

Cách tiếp cận được thiết kế theo hướng thận trọng. Do Giai đoạn 1 sử dụng kênh gửi lệnh thanh toán theo lô và sao kê hằng ngày thay vì API (Mục 3.3), phía VPBank hầu như không có phần tích hợp phần mềm nào cần kiểm thử — nỗ lực kiểm thử được dành cho việc chứng minh rằng các **chốt kiểm soát** hoạt động đúng như đặc tả, đặc biệt là hai chốt kiểm soát có hệ quả lớn nhất: tiền không thể được giải toả tới một tài khoản đích nằm ngoài danh sách tài khoản đích được phép, và một lệnh thanh toán bị gửi lặp lại không thể tạo ra khoản thanh toán thứ hai.

Công tác kiểm thử chủ ý bao gồm cả các **tình huống phủ định**. Một bộ kiểm thử chỉ chứng minh được rằng tiền được chuyển khi cần chuyển thì không phải là bằng chứng về một chốt kiểm soát đang hoạt động; các phép kiểm thử có ý nghĩa là những phép kiểm thử chứng minh rằng tiền *không* được chuyển khi không được phép chuyển.

---

## 3.7.1 Các giai đoạn

| Giai đoạn | Nội dung thực hiện | Mức tiền chịu rủi ro | Điều kiện hoàn thành |
|---|---|---|---|
| 0 — Xác nhận | VPBank trả lời các câu hỏi tại Mục 3.3, và hai bên thống nhất hạng mục nào là CẤU HÌNH và hạng mục nào là XÂY MỚI. Định dạng trường dữ liệu của kênh gửi lệnh thanh toán và của sao kê được trao đổi giữa hai bên | Không có | Danh mục yêu cầu đã được nghiệm thu, trong đó từng hạng mục của Mục 3.3 được đánh dấu là đã xác nhận, đã điều chỉnh hoặc không khả dụng |
| 1 — Thiết lập & kết nối | Một tài khoản ký quỹ được mở để phục vụ kiểm thử. Người dùng được uỷ quyền của FundLok được cấp quyền với sự tách biệt giữa quyền lập lệnh và quyền phê duyệt. Việc truy xuất sao kê được thiết lập và được hệ thống đối chiếu của FundLok phân tích dữ liệu | Không có | FundLok có thể truy xuất và phân tích dữ liệu sao kê của tài khoản kiểm thử mà không cần can thiệp thủ công |
| 2 — Kiểm thử chốt kiểm soát | Các tình huống kiểm thử phủ định và kiểm thử chốt kiểm soát tại 3.7.2 được thực hiện trên tài khoản kiểm thử với số tiền tượng trưng | Chỉ ở mức tượng trưng | Toàn bộ các tình huống kiểm thử chốt kiểm soát đều đạt, trong đó các phép kiểm thử về danh sách tài khoản đích được phép và về lệnh thanh toán trùng lặp phải đạt tuyệt đối, không có ngoại lệ |
| 3 — Khoản vay thật đầu tiên | Một khoản vay thật được vận hành trọn vẹn từ đầu đến cuối: nhà đầu tư thật, SME thật, tiền thật, được giám sát chặt chẽ, với từng bước được kiểm tra thủ công đối chiếu với Mục 3.1 | Một khoản vay | Khoản vay hoàn tất và tài khoản ký quỹ đối chiếu về số dư bằng không, không còn bút toán nào chưa được giải thích |
| 4 — Vận hành có giám sát | Các khoản vay được vận hành ở quy mô của chương trình thử nghiệm (pilot) với công tác đối chiếu hằng ngày do một cá nhân được chỉ định rà soát, thay vì chỉ rà soát theo trường hợp ngoại lệ | Quy mô chương trình thử nghiệm (pilot) | Ba mươi ngày liên tục không có hạng mục nào chưa được đối chiếu quá một ngày làm việc |
| 5 — Chương trình thử nghiệm ổn định | Vận hành bình thường. Công tác đối chiếu được rà soát theo trường hợp ngoại lệ; khối lượng giao dịch được theo dõi đối chiếu với điều kiện kích hoạt Giai đoạn 2 tại Mục 3.4 | Quy mô chương trình thử nghiệm (pilot) | — |

Các Giai đoạn 0 đến 2 không liên quan đến tiền của khách hàng. Giai đoạn 3 chủ ý giới hạn mức phơi nhiễm ở một khoản vay duy nhất, để bất kỳ khiếm khuyết nào trong bộ chốt kiểm soát cũng được phát hiện khi số tiền chịu rủi ro chỉ là một khoản vay thay vì cả một danh mục.

---

## 3.7.2 Các giao dịch kiểm thử

Toàn bộ số tiền kiểm thử đều mang tính tượng trưng: VND 10,000 cho mỗi lượt chuyển tiền kiểm thử, được chọn là giá trị nhỏ nhất cho phép thực hiện một lượt chuyển tiền thực sự thay vì chỉ là một phép kiểm tra tính hợp lệ với giá trị bằng không. Trong trường hợp phép kiểm thử cần đến tài khoản thứ hai, FundLok sử dụng chính tài khoản thanh toán vận hành của mình làm bên đối ứng, để không có khách hàng nào liên quan tới một tình huống kiểm thử bị thất bại.

### Kiểm thử chốt kiểm soát và kiểm thử phủ định — Giai đoạn 2

| Mã | Phép kiểm thử | Kết quả kỳ vọng |
|---|---|---|
| T1 | Tên tài khoản và sự tách biệt — kiểm tra tên đăng ký của tài khoản đã mở và xác nhận tài khoản này được tách biệt khỏi các tài khoản thanh toán vận hành của FundLok | Tên tài khoản khớp với định dạng đã thống nhất; tài khoản không được liên kết với các tài khoản của chính FundLok để bù trừ hoặc gom tiền tự động |
| T2 | **Thực thi danh sách tài khoản đích được phép** — gửi lệnh thanh toán chuyển tiền tới một tài khoản không nằm trong danh sách tài khoản đích được phép | **Lệnh thanh toán bị VPBank từ chối.** Không có lượt chuyển tiền nào phát sinh. Lý do từ chối được trả về và FundLok có thể đọc được |
| T3 | Tài khoản đích được phép, hợp lệ — gửi lệnh thanh toán chuyển tiền tới một tài khoản nằm trong danh sách | Được thực hiện. Xuất hiện trên sao kê kèm một mã nhận dạng ổn định |
| T4 | **Kiểm soát kép** — gửi một lệnh thanh toán chỉ được một người dùng của FundLok phê duyệt | **Lệnh thanh toán không được thực hiện.** Bị từ chối hoặc bị treo chờ phê duyệt thứ hai |
| T5 | Kiểm soát kép, tách biệt nhiệm vụ — thử để cùng một cá nhân vừa lập lệnh vừa phê duyệt | Không được phép theo cấu hình cấp quyền của kênh |
| T6 | **Lệnh thanh toán trùng lặp** — gửi cùng một mã tham chiếu lệnh thanh toán hai lần | **Chỉ phát sinh đúng một khoản thanh toán.** Lần gửi thứ hai bị từ chối hoặc trả về kết quả của lần gửi đầu tiên |
| T7 | Quy thuộc tiền vào — nộp tiền vào tài khoản ký quỹ qua VietQR có nêu mã tham chiếu của FundLok | Khoản ghi có xuất hiện trên sao kê với mã tham chiếu còn nguyên vẹn, kèm tên và số tài khoản của người chuyển tiền |
| T8 | Quy thuộc tiền vào, độ dài mã tham chiếu — nộp tiền có nêu mã tham chiếu ở độ dài tối đa mà FundLok dự kiến sử dụng | Mã tham chiếu được giữ nguyên, không bị cắt bớt |
| T9 | Quy thuộc tiền vào không thành công — nộp tiền không có mã tham chiếu, hoặc có mã tham chiếu không đúng định dạng | Khoản ghi có xuất hiện; hệ thống đối chiếu của FundLok đánh dấu khoản này là không thể quy thuộc và đưa vào trường hợp ngoại lệ thay vì hạch toán vào một khoản vay |
| T10 | Lô lệnh có một dòng lỗi — gửi một lô lệnh trong đó có một tài khoản đích không hợp lệ và các tài khoản đích còn lại đều hợp lệ | Các dòng hợp lệ được thực hiện; dòng không hợp lệ bị từ chối ở cấp độ từng dòng kèm lý do; **số tiền của dòng bị lỗi vẫn nằm trong tài khoản ký quỹ** |
| T11 | Tính ổn định của mã nhận dạng trên sao kê — truy xuất cùng một kỳ sao kê hai lần vào hai ngày khác nhau | Mọi mã nhận dạng giao dịch đều không thay đổi giữa hai lần truy xuất |
| T12 | Khoảng thời gian của sao kê — yêu cầu một khoảng thời gian trong quá khứ thay vì ngày gần nhất | Toàn bộ kỳ dữ liệu được trả về đầy đủ |
| T13 | Khớp số dư — so sánh số dư do VPBank báo cáo với số dư trên sổ sách của FundLok đối với tài khoản kiểm thử | Các số liệu khớp chính xác |
| T14 | Thu hồi quyền — FundLok thông báo loại bỏ một người dùng được uỷ quyền, sau đó người dùng này thử phê duyệt | Việc phê duyệt bị từ chối |
| T15 | Hành vi tại thời điểm cắt ngày — gửi một lệnh thanh toán ngay sau thời điểm cắt ngày hằng ngày | Ngày giá trị được áp dụng theo quy tắc VPBank đã nêu; hành vi khớp với nội dung được ghi nhận tại Phụ lục C |
| T16 | Thấu chi và bù trừ — thử gửi một lệnh thanh toán có số tiền vượt quá số dư của tài khoản ký quỹ | Bị từ chối. Không phát sinh thấu chi, không có việc bù trừ với bất kỳ số dư nào khác |
| T17 | Tất toán với số dư bằng không — đóng tài khoản kiểm thử | Sao kê cuối cùng được phát hành; tài khoản được đóng; số dư bằng không |

T2, T4, T6 và T10 là những phép kiểm thử phải đạt tuyệt đối, không kèm bất kỳ điều kiện nào. Một giải pháp thay thế tạm thời hoặc một câu trả lời "đúng, nhưng…" đối với bất kỳ phép kiểm thử nào trong bốn phép kiểm thử này đều có nghĩa là chốt kiểm soát chưa được thiết lập, và Giai đoạn 3 sẽ không được bắt đầu.

### Kiểm thử trọn vẹn từ đầu đến cuối — Giai đoạn 3

Khoản vay thật đầu tiên phải thực hiện toàn bộ chín bước của Mục 3.1 theo đúng trình tự, với từng bước được kiểm tra trước khi bước tiếp theo bắt đầu: tiếp nhận các bên và mở tài khoản ngân hàng, thẩm định và niêm yết, thiết lập tài khoản ký quỹ, ký kết hợp đồng vay, huy động vốn từ toàn bộ nhà đầu tư tham gia, giải ngân cho SME, ít nhất hai lần thu nợ, ít nhất hai chu kỳ phân bổ cho toàn bộ nhà đầu tư, và tất toán với số dư bằng không. Việc phân bổ được kiểm tra để bảo đảm tiền đã tới tài khoản chuyển tiền nguồn của từng nhà đầu tư và không tới bất kỳ tài khoản nào khác.

---

## 3.7.3 Phương pháp kiểm chứng công tác đối chiếu

Công tác đối chiếu được chứng minh bằng **sự khớp đúng ba chiều** trong một kỳ được xác định, đối với từng tài khoản ký quỹ:

1. **Sổ sách của FundLok** — mọi bút toán được ghi nhận đối với khoản vay.
2. **Sao kê của VPBank** — mọi dòng được hạch toán vào tài khoản.
3. **Sổ ghi nhận lệnh thanh toán của FundLok** — mọi lệnh thanh toán đã phát hành và kết quả được ghi nhận của lệnh đó.

Việc kiểm chứng được thực hiện như sau, và được lặp lại hằng ngày kể từ Giai đoạn 2 trở đi.

Mỗi dòng trên sao kê phải khớp với đúng một bút toán trên sổ sách, và mỗi bút toán trên sổ sách thể hiện một lượt chuyển tiền ra bên ngoài phải khớp với đúng một dòng trên sao kê. Mỗi khoản ghi nợ trên sao kê phải truy vết được về đúng một lệnh thanh toán trong sổ ghi nhận lệnh thanh toán với kết quả tương ứng. Số dư cuối kỳ theo VPBank phải bằng số dư do FundLok tính toán đối với tài khoản đó. Số lượng hạng mục không khớp ở cả hai phía phải bằng không tại thời điểm kết thúc kỳ kiểm chứng.

Hai đặc tính khiến kết quả này có ý nghĩa thực chất thay vì mang tính vòng vo. Sổ sách của FundLok chỉ cho phép ghi thêm và không thể sửa, do đó mọi sai lệch đều được xử lý bằng cách ghi một bút toán điều chỉnh kèm lý do được ghi nhận — sổ sách không bao giờ được âm thầm chỉnh sửa để khớp với ngân hàng. Đồng thời, sổ ghi nhận lệnh thanh toán độc lập với cả sổ sách và sao kê, nên một khoản ghi nợ xuất hiện trên sao kê mà không có lệnh thanh toán đã được phê duyệt tương ứng đều có thể phát hiện được, và đây chính là tình huống quan trọng nhất.

**Kiểm thử phát hiện sai lệch.** Việc kiểm chứng không được chấp nhận nếu chỉ dựa trên dữ liệu sạch. FundLok chủ động đưa một sai lệch có chủ đích vào chính dữ liệu đầu vào của công tác đối chiếu trong Giai đoạn 2 — một số tiền bị thay đổi và một dòng bị bỏ sót — và quy trình kiểm chứng phải phát hiện được cả hai. Một quy trình đối chiếu chưa từng phát hiện lỗi là một quy trình chưa được chứng minh là hoạt động.

---

## 3.7.4 Tiêu chí nghiệm thu

Giai đoạn 3 chỉ được bắt đầu khi toàn bộ các hạng mục dưới đây đã được đáp ứng.

| # | Tiêu chí | Bằng chứng |
|---|---|---|
| 1 | Mọi hạng mục tại Mục 3.3 đều được đánh dấu là đã xác nhận, đã điều chỉnh theo thoả thuận, hoặc được nêu rõ là không khả dụng kèm hệ quả được ghi nhận | Danh mục yêu cầu đã được nghiệm thu từ Giai đoạn 0 |
| 2 | Các phép kiểm thử chốt kiểm soát T2, T4, T6 và T10 đã đạt tuyệt đối, không kèm điều kiện và không có giải pháp thay thế tạm thời | Kết quả kiểm thử kèm các bản trích xuất sao kê |
| 3 | Toàn bộ các phép kiểm thử còn lại của Giai đoạn 2 đã đạt, hoặc có sai khác được ghi nhận và được chấp thuận | Kết quả kiểm thử |
| 4 | Việc truy xuất và phân tích dữ liệu sao kê hoạt động mà không cần can thiệp thủ công | Kết quả đối chiếu của tài khoản kiểm thử |
| 5 | Công tác đối chiếu ba chiều cho kết quả không có hạng mục không khớp trong ít nhất năm ngày làm việc liên tục | Các báo cáo đối chiếu |
| 6 | Phép kiểm thử phát hiện sai lệch đã phát hiện được cả hai sai lệch được đưa vào | Sổ ghi nhận trường hợp ngoại lệ của công tác đối chiếu |
| 7 | Thời điểm cắt ngày, việc xác định ngày giá trị và hành vi trong ngày không phải ngày làm việc đều được lập thành văn bản và khớp với hành vi đã quan sát được | Phụ lục C, đã hoàn thiện |
| 8 | Người dùng được uỷ quyền của FundLok được cấp quyền với sự tách biệt giữa quyền lập lệnh và quyền phê duyệt, và việc thu hồi quyền đã được chứng minh | Bản ghi cấp quyền và kết quả T14 |
| 9 | Việc xử lý trường hợp ngoại lệ được quy định rõ với người chịu trách nhiệm được chỉ định và thời gian phản hồi theo từng loại trường hợp ngoại lệ | Quy trình vận hành của FundLok |
| 10 | Mỗi bên đều có một cá nhân được chỉ định chịu trách nhiệm về chương trình thử nghiệm (pilot), kèm lộ trình leo thang xử lý đã được thống nhất | Được ghi nhận trong bộ tài liệu hợp tác |

**Các bên ký nghiệm thu.** FundLok: Edward Wong, Giám đốc Công nghệ, đối với các tiêu chí về kỹ thuật và đối chiếu; Loc, Tổng Giám đốc, đối với việc khởi động vận hành thật. VPBank: các cá nhân phụ trách tương ứng về vận hành lưu ký và về kỹ thuật, sẽ được chỉ định.

Việc chuyển từ Giai đoạn 4 sang Giai đoạn 5 đòi hỏi tiêu chí 5 được duy trì trong ba mươi ngày liên tục thay vì năm ngày, và không có hạng mục nào chưa được đối chiếu quá một ngày làm việc.

---

## 3.7.5 Các hạng mục cần xác nhận

| # | Hạng mục | Ý nghĩa đối với mục này | Bên phụ trách | Thời hạn |
|---|---|---|---|---|
| 1 | VPBank có thể cung cấp môi trường kiểm thử hoặc môi trường phi sản xuất hay không, hoặc Giai đoạn 2 có buộc phải thực hiện trên một tài khoản thật với số tiền tượng trưng hay không | Quyết định việc Giai đoạn 2 có phát sinh mức phơi nhiễm thực tế nào hay không. Kế hoạch của FundLok giả định sử dụng một tài khoản thật với số tiền tượng trưng, phương án này khả thi trong cả hai trường hợp | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 2 | Các đầu mối liên hệ được chỉ định về kỹ thuật và về vận hành lưu ký tại VPBank cho các Giai đoạn 0 đến 2 | Không thể đáp ứng tiêu chí 10 nếu thiếu các đầu mối này | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 3 | VPBank có mong muốn chứng kiến hoặc cùng ký xác nhận kết quả kiểm thử chốt kiểm soát của Giai đoạn 2 hay không | FundLok mong muốn VPBank cùng ký xác nhận T2, T4, T6 và T10, bởi đây là các chốt kiểm soát do VPBank thực thi | Edward, cùng với VPBank | Chờ VPBank xác nhận |
| 4 | Thời lượng cần dự trù cho các Giai đoạn 0 đến 2 | Phụ thuộc vào quy trình quản lý thay đổi nội bộ của VPBank, mà FundLok không thể ước lượng | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 5 | Tần suất trả nợ | Quyết định thời lượng của Giai đoạn 3, bởi giai đoạn này đòi hỏi ít nhất hai chu kỳ thu nợ và phân bổ | Loc + Edward | 2026-08-07 |

---

*Phụ thuộc: Mục 3.3 (yêu cầu của Giai đoạn 1). Nhất quán với Mục 3.1 (quy trình), Mục 3.5 (phần xây dựng của FundLok) và Phụ lục C (SLA và các thời điểm cắt ngày). Khối lượng công việc thuộc phía FundLok được nêu tại Mục 3.6.*


<!-- ══════════════════ PASTE INTO SECTION 4.4 ══════════════════ -->

> ## ▼ Mục 4.4 — Bảo vệ dữ liệu & an toàn thông tin
>
> Dán khối bên dưới thay cho `[CONTENT — …]` tại mục 4.4.

# 4.4 Bảo vệ dữ liệu và an toàn thông tin

*[NỘI DUNG — Edward. Bản thảo tiếng Anh phục vụ rà soát nội bộ; bản tiếng Việt sẽ được cung cấp sau.]*

---

FundLok xử lý dữ liệu cá nhân của các nhà đầu tư và của người đại diện các doanh nghiệp đi vay. Mục này trình bày khuôn khổ pháp lý mà FundLok hoạt động theo, các biện pháp kiểm soát đã được thiết lập, và các biện pháp kiểm soát còn phải hoàn thành trước khi vận hành chính thức (go-live).

Văn bản điều chỉnh là **Luật số 91/2025/QH15 về Bảo vệ dữ liệu cá nhân**, có hiệu lực từ ngày **1 January 2026** (nguồn: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15, Quốc hội, 2025). Luật này hiện đã có hiệu lực, không còn ở trạng thái chờ áp dụng. Hai quy định của Luật có liên quan trực tiếp đến thoả thuận này: việc thông báo vi phạm dữ liệu phải được thực hiện **trong vòng 72 giờ kể từ khi phát hiện**, và đối với một tổ chức cung cấp dịch vụ tài chính, nghĩa vụ thông báo này mở rộng đến các chủ thể dữ liệu bị ảnh hưởng chứ không chỉ đến cơ quan quản lý. Luật cũng đặt ra các biện pháp bảo vệ riêng cho hoạt động tài chính, ngân hàng và tín dụng, với các nội dung chi tiết sẽ được quy định trong các văn bản hướng dẫn thi hành.

Không có nội dung nào trong mục này yêu cầu VPBank nhận trách nhiệm đối với các nghĩa vụ bảo vệ dữ liệu của FundLok, và FundLok không đưa ra các biện pháp kiểm soát của mình để thay thế cho bất kỳ hoạt động đánh giá nào mà VPBank tự thực hiện.

**Ở những chỗ mục này nêu một cam kết thay vì một trạng thái hiện tại, điều đó được nêu rõ.** Nội dung 3 và 4 của Mục 4.4.10 là các cam kết có điều kiện khởi phát, không phải mô tả hiện trạng.

---

## 4.4.1 Dữ liệu cá nhân được xử lý

| Nhóm dữ liệu | Ví dụ | Nguồn | Có chuyển sang VPBank |
|---|---|---|---|
| Dữ liệu định danh | Họ tên, ngày sinh, số định danh cá nhân, địa chỉ, thông tin liên hệ | Cá nhân đó | Chỉ họ tên, với tư cách là một phần của một mục trong danh sách tài khoản đích được phép hoặc của một lệnh chuyển tiền |
| Bằng chứng định danh | Hình ảnh giấy tờ định danh, và phép so sánh sinh trắc học khuôn mặt được thực hiện trong quá trình xác minh | Cá nhân đó, thông qua một đơn vị cung cấp dịch vụ xác minh là bên thứ ba | Không |
| Dữ liệu doanh nghiệp | Đăng ký doanh nghiệp, dữ liệu giấy phép, thông tin định danh của người đại diện được uỷ quyền | SME | Chỉ họ tên, như trên |
| Dữ liệu tài chính | Báo cáo tài chính, lịch sử kinh doanh, dữ liệu đầu vào và đầu ra của quá trình định giá | SME | Không |
| Dữ liệu thanh toán | Thông tin tài khoản ngân hàng hoặc ví điện tử, được lưu ở dạng che dấu | Cá nhân hoặc doanh nghiệp | Số tài khoản và tên chủ tài khoản, theo mức cần thiết cho một lượt chuyển tiền có ghi rõ tên người nhận |
| Dữ liệu nền tảng | Cam kết góp vốn, số dư nắm giữ, lịch sử trả nợ, nhật ký truy cập | Phát sinh trong quá trình sử dụng | Không |
| Dữ liệu bán hàng của bên đi vay | Dữ liệu bán hàng ở mức từng hoá đơn của ngày liền trước, lấy từ dữ liệu hoá đơn điện tử của bên đi vay thông qua một đơn vị cung cấp dịch vụ T-VAN được cấp phép, làm cơ sở tính số tiền trả nợ hằng ngày | Hồ sơ hoá đơn điện tử của bên đi vay, với sự đồng ý của bên đi vay | Không |
| Hồ sơ về sự đồng ý | Phạm vi, dấu thời gian, trạng thái rút lại sự đồng ý | Phát sinh trong quá trình sử dụng | Không |

Tập dữ liệu chuyển sang VPBank được giới hạn ở những gì mà một lượt chuyển tiền đến người nhận có định danh yêu cầu, và được quy định đầy đủ tại Mục 1.5.2. Phép so sánh sinh trắc học khuôn mặt được thực hiện trong quá trình xác minh là nhóm dữ liệu có tính nhạy cảm cao nhất mà FundLok xử lý; dữ liệu này không được chia sẻ với VPBank và được đề cập riêng tại Mục 4.4.5.

**Dữ liệu bán hàng của bên đi vay cần được xử lý theo cách riêng, và đây là nội dung mới.** Cơ chế chia sẻ doanh thu hằng ngày tại Mục 1.4 phụ thuộc vào việc đọc dữ liệu bán hàng của ngày liền trước của từng bên đi vay thông qua một đơn vị cung cấp dịch vụ T-VAN được cấp phép. Dữ liệu bán hàng ở mức từng hoá đơn về cơ bản là dữ liệu thương mại của chính bên đi vay, nhưng ở những trường hợp bên đi vay bán hàng cho cá nhân, các hồ sơ đó cũng có thể chứa dữ liệu cá nhân thuộc về **khách hàng của chính bên đi vay** — những người không có quan hệ nào với FundLok và không đưa ra sự đồng ý nào cho FundLok. Quan điểm của FundLok là FundLok chỉ cần doanh thu tổng hợp hằng ngày, không cần thông tin chi tiết về đối tác giao dịch, và do đó việc tích hợp hoặc là không nên yêu cầu các trường dữ liệu về đối tác giao dịch ở mức từng hoá đơn, hoặc là phải loại bỏ các trường đó khi tiếp nhận thay vì lưu trữ. Việc giao diện T-VAN có cho phép sự tách biệt đó hay không là một nội dung còn để mở tại Mục 4.4.10, và việc thiết kế loại bỏ ngay từ bây giờ có chi phí thấp hơn nhiều so với việc phải biện giải về sau.

---

## 4.4.2 Cơ chế lấy sự đồng ý

Sự đồng ý được lấy tại thời điểm thu thập dữ liệu, riêng biệt cho từng mục đích, và không bao giờ được gộp vào việc chấp thuận các điều khoản của nền tảng như một khối chung. Mỗi hồ sơ về sự đồng ý ghi nhận phạm vi, phiên bản của thông báo đã được trình bày, một dấu thời gian, và trạng thái rút lại sự đồng ý; các hồ sơ này được lưu trong nền tảng và có thể kiểm toán được.

Sự đồng ý được lấy riêng cho việc xác minh danh tính, bao gồm phép so sánh sinh trắc học, và cho việc đăng ký một tài khoản thanh toán cùng việc sử dụng tài khoản đó làm tài khoản đích nhận chuyển tiền. Một bên có thể rút lại sự đồng ý thông qua nền tảng. Trường hợp sự đồng ý bị rút lại đối với một mục đích là điều kiện tiên quyết của một khoản vay đang có hiệu lực, FundLok không thể tiếp tục hành động cho bên đó kể từ thời điểm đó, nhưng vẫn lưu giữ các hồ sơ mà khoản vay và pháp luật yêu cầu — xem Mục 4.4.4.

Không phải mọi hoạt động xử lý đều dựa trên sự đồng ý. Việc xử lý cần thiết để thực hiện hợp đồng vay và hợp đồng uỷ quyền quản lý dựa trên tính cần thiết theo hợp đồng đó, là căn cứ mà Luật 91/2025 công nhận là một căn cứ độc lập với sự đồng ý. Quan điểm của FundLok là đây là căn cứ đúng đắn cho việc phát hành lệnh thanh toán, việc đối chiếu và việc lưu giữ hồ sơ, và đây là một trong các nội dung cần luật sư tư vấn xác nhận tại Mục 4.4.10.

---

## 4.4.3 Kiểm soát truy cập

| Biện pháp kiểm soát | Cách thực hiện | Trạng thái |
|---|---|---|
| Kiểm soát truy cập theo vai trò | Mọi điểm cuối (endpoint) của nền tảng đều phân quyền theo vai trò của bên gọi; không có điểm cuối nào dựa vào việc hạn chế ở phía máy khách | Đang vận hành |
| Xác thực | Xác thực dựa trên token, với token truy cập và token làm mới tách biệt, và có cơ chế thu hồi ở phía máy chủ để có thể kết thúc một phiên làm việc | Đang vận hành |
| Lưu trữ thông tin xác thực | Mật khẩu được lưu bằng hàm băm Argon2; không lưu trữ thông tin xác thực ở dạng có thể giải mã ngược tại bất kỳ nơi nào | Đang vận hành |
| Đặc quyền tối thiểu | Quyền truy cập của nhân sự được cấp theo từng vai trò, và quyền truy cập dữ liệu cá nhân được giới hạn ở các vai trò có nhu cầu | Đang vận hành, cần lập tài liệu về quy trình rà soát chính thức |
| Phân tách nhiệm vụ đối với lượt chuyển tiền | Việc lập và việc phê duyệt một lệnh thanh toán do những cá nhân được nêu tên khác nhau đảm nhiệm, được cưỡng chế thực thi bằng cơ chế phân quyền trên kênh của VPBank thay vì bằng quy trình nội bộ của FundLok | Cần xây mới — Mục 3.5, hạng mục 1 |
| Thu hồi quyền | Quyền truy cập nền tảng và quyền trên kênh ngân hàng đều được thu hồi khi có thay đổi nhân sự, trong cùng ngày | Đang vận hành đối với nền tảng; kênh ngân hàng theo Mục 3.3 nội dung E2 |
| Quản lý khoá bí mật | Các khoá bí mật của ứng dụng được lưu trong một kho khoá bí mật được quản lý, không bao giờ lưu trong hệ thống quản lý mã nguồn hoặc trong các tệp cấu hình | Đang vận hành |
| Ghi nhật ký kiểm toán | Các hành vi quản trị và các hành vi liên quan đến tiền được ghi vào một nhật ký chỉ cho phép ghi thêm; bản thân sổ sách không thể bị sửa hoặc xoá ở tầng ứng dụng cũng như ở tầng cơ sở dữ liệu | Đang vận hành |

---

## 4.4.4 Thời hạn lưu giữ

FundLok lưu giữ hồ sơ khoản vay và hồ sơ giao dịch, cùng với dữ liệu cá nhân cần thiết để hiểu các hồ sơ đó, trong **mười năm kể từ khi khoản vay tất toán**. Thời hạn này được đặt ra để phù hợp với nghĩa vụ lưu giữ áp dụng cho hồ sơ kế toán và hồ sơ tài chính theo pháp luật Việt Nam; căn cứ pháp lý cụ thể cần luật sư tư vấn xác nhận.

Các nhóm dữ liệu được lưu giữ trong thời hạn ngắn hơn: bằng chứng định danh, bao gồm hình ảnh giấy tờ và kết quả so sánh sinh trắc học, chỉ được lưu giữ trong thời gian cần thiết để chứng minh rằng việc xác minh đã được thực hiện, và các hình ảnh gốc không được lưu giữ vượt quá nhu cầu đó. Nhật ký truy cập và nhật ký phiên làm việc được lưu giữ trong hai năm. Hồ sơ về sự đồng ý được lưu giữ trong suốt thời gian tồn tại của quan hệ cộng thêm thời hạn mười năm, bởi hồ sơ về sự đồng ý chính là bằng chứng cho thấy việc xử lý là hợp pháp và phải tồn tại lâu hơn bản thân việc xử lý đó.

Việc lưu giữ và việc xoá dữ liệu có tương tác với nhau, và quan điểm về vấn đề này cần được nêu rõ thay vì để ngầm hiểu. Khi một chủ thể dữ liệu yêu cầu xoá dữ liệu, FundLok xoá những gì mình đang lưu giữ trên cơ sở sự đồng ý và không còn cần đến. FundLok không xoá những hồ sơ mà pháp luật yêu cầu phải lưu giữ, hoặc những hồ sơ cần thiết để chứng minh một khoản vay đã từng tồn tại — một khoản vay đã hoàn tất không thể bị đảo ngược chỉ vì một bên sau đó yêu cầu xoá hồ sơ của khoản vay, và bên còn lại của khoản vay đó có lợi ích riêng của mình đối với hồ sơ. Do đó, phản hồi của FundLok đối với một yêu cầu xoá dữ liệu phân biệt hai tập dữ liệu này và giải thích rõ tập nào là tập nào.

Khi hết thời hạn lưu giữ, các hồ sơ được xoá, và việc xoá được ghi nhật ký.

---

## 4.4.5 Dữ liệu sinh trắc học và dữ liệu nhạy cảm

Quy trình xác minh bao gồm một phép so sánh khuôn mặt giữa hình ảnh được gửi lên và giấy tờ định danh. Việc này tạo ra dữ liệu sinh trắc học, là loại dữ liệu mà Luật 91/2025 áp dụng mức bảo vệ cao hơn — và đây cũng chính là một trong những nhóm dữ liệu mà khi có vi phạm thì phải thông báo cho các cá nhân bị ảnh hưởng, không chỉ cho cơ quan quản lý.

Quan điểm của FundLok: phép so sánh sinh trắc học được thực hiện bởi một đơn vị cung cấp dịch vụ xác minh chuyên biệt là bên thứ ba, hoạt động với tư cách bên xử lý dữ liệu theo chỉ dẫn của FundLok; kết quả so sánh được lưu giữ làm bằng chứng cho thấy việc xác minh đã diễn ra; các hình ảnh gốc không được lưu giữ vượt quá nhu cầu được mô tả tại Mục 4.4.4; và dữ liệu này không được chia sẻ với VPBank tại bất kỳ thời điểm nào.

**Có một vấn đề còn để mở và có tính trọng yếu.** Nếu đơn vị cung cấp dịch vụ xác minh thực hiện bất kỳ phần nào của việc xử lý đó ở ngoài Việt Nam, thì đó là một hoạt động chuyển dữ liệu sinh trắc học ra nước ngoài và đòi hỏi phải có đánh giá tác động của việc chuyển dữ liệu, đồng thời cũng tạo ra sự không tương thích với cam kết nội địa hoá tại Mục 4.4.6. FundLok đã nêu vấn đề này ra thay vì mặc định coi là đã được giải quyết — nội dung 5 của Mục 4.4.10.

---

## 4.4.6 Nội địa hoá dữ liệu

**Cam kết.** FundLok sẽ xử lý và lưu trữ dữ liệu cá nhân liên quan đến thoả thuận này trong phạm vi Việt Nam, và sẽ hoàn thành việc chuyển đổi sang hạ tầng lưu trữ trong nước **trước khi vận hành chính thức** — nghĩa là trước Giai đoạn 3 của Mục 3.7, tức khoản vay đầu tiên được thực hiện thực tế.

Xin nêu rõ, bởi một ngân hàng không nên phải tự suy luận điều này: nền tảng của FundLok hiện đang chạy trên một vùng đám mây được quản lý tại Đông Nam Á ở ngoài Việt Nam, với lưu trữ đối tượng (object storage) trên một nhà cung cấp phân tán toàn cầu. Đó là hiện trạng, và đó là lý do vì sao nội dung này được viết như một cam kết có điều kiện khởi phát chứ không phải như một mô tả. Việc chuyển đổi bao gồm môi trường chạy ứng dụng, cơ sở dữ liệu, lưu trữ đối tượng chứa các tài liệu được tải lên, và các bản sao lưu.

Bản thân Luật 91/2025 không áp đặt một yêu cầu nội địa hoá chung đối với toàn bộ dữ liệu cá nhân. Do đó, cam kết của FundLok được đưa ra với tư cách là một vấn đề chính sách và là sự bảo đảm đối với VPBank, và nhằm loại bỏ mọi thắc mắc về việc dữ liệu liên quan đến một thoả thuận lưu ký tại Việt Nam được lưu giữ ở đâu. Việc có bất kỳ nghĩa vụ nội địa hoá theo luật nào khác áp dụng cho hoạt động này hay không là nội dung cần luật sư tư vấn xác nhận.

---

## 4.4.7 Mã hoá

| Tầng | Tiêu chuẩn |
|---|---|
| Dữ liệu khi lưu trữ — cơ sở dữ liệu, lưu trữ đối tượng, bản sao lưu | **AES-256**, được nền tảng được quản lý áp dụng cho toàn bộ dữ liệu đã lưu và các bản sao lưu |
| Dữ liệu khi truyền — từ các bên đến nền tảng, từ nền tảng đến VPBank, từ nền tảng đến các bên xử lý dữ liệu | **TLS 1.2 hoặc cao hơn**, với các phiên bản giao thức và bộ mã hoá yếu hơn đã bị vô hiệu hoá |
| Thông tin xác thực | Băm mật khẩu bằng Argon2; các khoá bí mật của ứng dụng nằm trong một kho khoá bí mật được quản lý, được mã hoá khi lưu trữ |
| Thông tin tài khoản thanh toán | Được lưu ở dạng che dấu; số tài khoản đầy đủ được dùng để soạn một lệnh thanh toán và không được lưu lại ở dạng đầy đủ |
| Truy cập tài liệu | Truy cập vào lưu trữ đối tượng thông qua đường dẫn được ký trước và có giới hạn thời gian; tài liệu không được cung cấp qua các URL công khai tồn tại lâu dài |

---

## 4.4.8 Quy trình ứng phó vi phạm dữ liệu

Luật 91/2025 yêu cầu thông báo trong vòng **72 giờ kể từ khi phát hiện**, và đối với một tổ chức cung cấp dịch vụ tài chính thì nghĩa vụ này mở rộng đến các chủ thể dữ liệu bị ảnh hưởng. Quy trình của FundLok được xây dựng theo mốc thời gian đó, tính lùi từ mốc đó.

1. **Phát hiện và ghi nhận.** Mọi sự cố bị nghi ngờ đều được ghi nhận ngay khi phát hiện, kèm dấu thời gian phát hiện, là thời điểm bắt đầu tính thời hạn 72 giờ. Dấu thời gian được ghi nhận trước tiên, trước khi bắt đầu đánh giá, để mốc thời gian không bao giờ bị dựng lại sau khi sự việc đã xảy ra.
2. **Khoanh vùng ngăn chặn.** Các bước ngay lập tức để hạn chế mức độ phơi nhiễm — thu hồi thông tin xác thực hoặc token, vô hiệu hoá một kết nối tích hợp bị ảnh hưởng, cách ly một thành phần. Việc khoanh vùng ngăn chặn không chờ đến khi hoàn tất việc đánh giá.
3. **Đánh giá.** Trong vòng 24 giờ kể từ khi phát hiện: dữ liệu nào, của ai, số lượng bao nhiêu, nguyên nhân là gì, sự cố có còn đang tiếp diễn hay không. Mọi sự cố có liên quan đến dữ liệu sinh trắc học, bằng chứng định danh hoặc dữ liệu thanh toán đều được coi là thuộc diện phải thông báo, trừ khi việc đánh giá xác lập được một cách rõ ràng điều ngược lại.
4. **Thông báo.** Thông báo cho cơ quan quản lý trong vòng 72 giờ kể từ khi phát hiện. Thông báo cho các chủ thể dữ liệu bị ảnh hưởng trong cùng thời hạn đó nếu sự cố liên quan đến dữ liệu của họ, bằng ngôn ngữ dễ hiểu, mô tả điều gì đã xảy ra, dữ liệu nào có liên quan, FundLok đã làm gì, và cá nhân đó nên làm gì.
5. **Thông báo cho VPBank.** Trường hợp một sự cố ảnh hưởng đến tính toàn vẹn của dữ liệu lệnh thanh toán, đến thoả thuận ký quỹ hoặc đến bất kỳ dữ liệu nào được trao đổi với VPBank, FundLok thông báo cho VPBank mà không chờ đến thời hạn theo quy định pháp luật. FundLok đề nghị VPBank thực hiện tương ứng, để mốc 72 giờ của mỗi bên đều có thể được tuân thủ — nội dung 6 của Mục 4.4.10.
6. **Khắc phục và lưu hồ sơ.** Nguyên nhân gốc được xử lý, và sự cố, diễn biến thời gian, các quyết định cùng lý do của các quyết định đó đều được ghi nhận. Hồ sơ được lưu giữ bất kể sự cố có thuộc diện phải thông báo hay không, bởi bản thân quyết định không thông báo cũng phải có bằng chứng.
7. **Rà soát.** Mỗi sự cố được rà soát để xác định xem đánh giá tác động tại Mục 4.4.9 có cần được cập nhật hay không.

Một cá nhân được nêu tên chịu trách nhiệm điều hành quy trình này. Quy trình được kiểm thử chứ không chỉ được viết ra: FundLok tổ chức một buổi diễn tập trên giấy (tabletop exercise) đối với quy trình này trước khi vận hành chính thức.

---

## 4.4.9 Đánh giá tác động và trách nhiệm giải trình

Luật 91/2025 yêu cầu phải có đánh giá tác động xử lý dữ liệu, và đánh giá tác động của việc chuyển dữ liệu trong trường hợp dữ liệu cá nhân được chuyển ra ngoài biên giới, cùng với việc đánh giá lại khi hoạt động xử lý thay đổi. Luật cũng yêu cầu tổ chức phải chỉ định một bộ phận phụ trách bảo vệ dữ liệu, trong nội bộ hoặc thông qua một đơn vị cung cấp dịch vụ bên ngoài. Doanh nghiệp nhỏ và doanh nghiệp khởi nghiệp được miễn yêu cầu về đánh giá tác động trong thời hạn năm năm.

Quan điểm của FundLok:

- Một **đánh giá tác động xử lý dữ liệu** bao trùm nền tảng, đơn vị cung cấp dịch vụ xác minh và hoạt động trao đổi dữ liệu với VPBank sẽ được hoàn thành trước khi vận hành chính thức, và được rà soát khi có bất kỳ thay đổi trọng yếu nào đối với hoạt động xử lý.
- Một **đánh giá tác động của việc chuyển dữ liệu** sẽ được hoàn thành cho mọi hoạt động xử lý diễn ra ở ngoài Việt Nam, kể cả hoạt động do đơn vị cung cấp dịch vụ xác minh thực hiện, và sẽ được kết thúc bằng việc chuyển đổi hạ tầng tại Mục 4.4.6 ở những phần mà việc chuyển dữ liệu chấm dứt.
- Một **trách nhiệm bảo vệ dữ liệu được chỉ định** được giao cho một cá nhân được nêu tên, cùng với việc thuê luật sư tư vấn bên ngoài cho phần đánh giá pháp lý.
- FundLok sẽ **không dựa vào miễn trừ dành cho doanh nghiệp nhỏ** trừ khi luật sư tư vấn cho ý kiến rằng miễn trừ đó rõ ràng được áp dụng. Việc lập các đánh giá này là một kỷ luật hữu ích bất kể miễn trừ có được áp dụng hay không, và việc dựa vào một miễn trừ mà khả năng áp dụng còn chưa chắc chắn là một vị thế yếu khi trình bày trước một đối tác ngân hàng.

FundLok cũng lưu ý điều cấm trong Luật 91/2025 về việc mua bán dữ liệu cá nhân, và tuyên bố chính thức rằng FundLok không bán, không cấp phép sử dụng và không mua bán dữ liệu cá nhân dưới bất kỳ hình thức nào khác, và không sử dụng dữ liệu cá nhân của nhà đầu tư hoặc của bên đi vay cho bất kỳ mục đích nào ngoài việc vận hành nền tảng và các khoản vay trên nền tảng đó.

---

## 4.4.10 Các nội dung cần xác nhận

| # | Nội dung | Vì sao có ý nghĩa đối với mục này | Bên chịu trách nhiệm | Thời hạn |
|---|---|---|---|---|
| 1 | Căn cứ pháp lý cụ thể cho thời hạn lưu giữ mười năm | Được nêu tại Mục 4.4.4 là phù hợp với thời hạn lưu giữ hồ sơ kế toán; việc dẫn chiếu phải chính xác trước khi nội dung này được chuyển cho VPBank | Edward, cùng luật sư tư vấn | 2026-08-14 |
| 2 | Phân tích về căn cứ hợp pháp — hoạt động xử lý nào dựa trên sự đồng ý và hoạt động nào dựa trên tính cần thiết theo hợp đồng | Xác định việc rút lại sự đồng ý có thể làm dừng hoạt động xử lý cần thiết để phục vụ một khoản vay đang có hiệu lực hay không | Edward, cùng luật sư tư vấn | 2026-08-14 |
| 3 | Chuyển môi trường chạy ứng dụng, cơ sở dữ liệu, lưu trữ đối tượng và các bản sao lưu vào Việt Nam | Mục 4.4.6 là một cam kết, không phải hiện trạng. Phải hoàn thành trước Giai đoạn 3 của Mục 3.7 | Edward | Trước khi vận hành chính thức |
| 4 | Biện pháp kiểm soát phân tách nhiệm vụ đối với lệnh thanh toán | Được liệt kê là cần xây mới tại Mục 4.4.3; phụ thuộc vào việc phân quyền trên kênh ngân hàng tại Mục 3.3 nội dung E1 | Edward | Trước khi vận hành chính thức |
| 5 | Đơn vị cung cấp dịch vụ xác minh là bên thứ ba có xử lý dữ liệu định danh hoặc dữ liệu sinh trắc học ở ngoài Việt Nam hay không | Xác định có cần đánh giá tác động của việc chuyển dữ liệu đối với dữ liệu sinh trắc học hay không, và đơn vị cung cấp dịch vụ có phải bị thay thế hoặc phải chuyển địa điểm để đáp ứng Mục 4.4.6 hay không. **Đây là nội dung còn để mở có tính trọng yếu nhất trong mục này** | Edward, cùng luật sư tư vấn | 2026-08-14 |
| 6 | Cơ chế thông báo sự cố có tính tương hỗ với VPBank, và đầu mối liên hệ cho cơ chế đó | FundLok chịu mốc 72 giờ được tính từ thời điểm phát hiện, không phải từ thời điểm FundLok được biết về một sự cố phía ngân hàng | Edward, cùng VPBank | Chờ VPBank xác nhận |
| 7 | Miễn trừ đánh giá tác động dành cho doanh nghiệp nhỏ có áp dụng cho FundLok hay không | Ý định đã tuyên bố của FundLok là không dựa vào miễn trừ này; việc xác nhận cho phép nêu vị thế đó như một lựa chọn thay vì một giả định | Edward, cùng luật sư tư vấn | 2026-08-14 |
| 8 | VPBank có yêu cầu một hợp đồng xử lý dữ liệu hay không, và theo mẫu của bên nào | Xác định tầng hợp đồng bao trùm hoạt động trao đổi dữ liệu được quy định tại Mục 1.5 | Edward, cùng VPBank | Chờ VPBank xác nhận |
| 9 | Các văn bản hướng dẫn thi hành Luật 91/2025 đối với hoạt động tài chính và tín dụng | Các biện pháp bảo vệ riêng theo ngành của Luật còn chờ hướng dẫn chi tiết; mục này có thể cần được sửa đổi khi hướng dẫn được ban hành | Edward, cùng luật sư tư vấn | Liên tục |
| 10 | Giao diện T-VAN có thể cung cấp doanh thu tổng hợp hằng ngày mà không kèm thông tin chi tiết về đối tác giao dịch ở mức từng hoá đơn hay không | Xác định FundLok có xử lý dữ liệu cá nhân của khách hàng của chính bên đi vay hay không | Edward, cùng luật sư tư vấn | Trước khi việc tích hợp được xây dựng |
| 11 | Căn cứ hợp pháp và câu chữ về sự đồng ý cho luồng dữ liệu bán hàng qua T-VAN, bao gồm thẩm quyền của bên đi vay trong việc cho phép luồng dữ liệu đó | Bên đi vay đồng ý cho FundLok đọc dữ liệu bán hàng của mình; việc sự đồng ý đó có mở rộng đến dữ liệu về khách hàng của chính bên đi vay hay không là một câu hỏi riêng biệt | Edward, cùng luật sư tư vấn | 2026-08-14 |

---

*Phụ thuộc: không có. Nhất quán với Mục 1.4 (luồng tiền, và luồng dữ liệu bán hàng qua T-VAN mà luồng tiền phụ thuộc vào), Mục 1.5 (luồng dữ liệu), Mục 3.3 (yêu cầu an toàn kênh), Mục 3.5 (phần FundLok xây dựng) và Mục 3.7 (phân đoạn triển khai vận hành chính thức). Việc xử lý khi mất khả năng thanh toán và quan điểm kế toán đối với số dư tài khoản ký quỹ được nêu tại Mục 4.5.*
