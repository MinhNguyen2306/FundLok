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
| 8 | Số lượng tài khoản đích tối đa cho mỗi tài khoản (yêu cầu A2a) | Với tám nhà đầu tư, một dự án cần mười hai tài khoản đích; một sản phẩm giới hạn ở mức năm sẽ phá vỡ mô hình một cách âm thầm | VPBank, theo đề nghị của Edward | Chờ VPBank xác nhận |
| 7 | Thời điểm ngừng nhận lệnh, việc xác định ngày giá trị và cách xử lý ngày không phải ngày làm việc đối với kênh truyền lệnh thanh toán | Quyết định những gì FundLok có thể cam kết với các nhà đầu tư và các bên đi vay về mặt thời gian | VPBank, theo đề nghị của Edward — được ghi nhận tại Phụ lục C | Chờ VPBank xác nhận |

---

*Các nội dung phụ thuộc: sự xác nhận của VPBank, theo 3.3.2. Nhất quán với Mục 3.1 (quy trình), Mục 1.7 (giới hạn vai trò), Mục 1.8 (cấu trúc tài khoản) và Mục 3.4 (Giai đoạn 2). Ước tính khối lượng công việc cho từng thành phần nêu trên được trình bày tại Mục 3.6.*
