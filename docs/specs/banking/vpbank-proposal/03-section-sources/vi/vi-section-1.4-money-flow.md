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
