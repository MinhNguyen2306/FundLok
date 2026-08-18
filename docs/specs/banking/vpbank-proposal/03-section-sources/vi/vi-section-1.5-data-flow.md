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
