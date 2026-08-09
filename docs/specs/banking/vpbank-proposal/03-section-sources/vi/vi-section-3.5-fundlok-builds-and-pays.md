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
| 0 | Xác nhận từ Phat về tình trạng thực tế của việc tích hợp T-VAN. Không có nội dung nào liên quan đến việc này xuất hiện trong kho mã nguồn của FundLok hoặc trên bất kỳ nhánh nào tại thời điểm 5 August 2026, do đó nội dung này được ghi nhận ở trên là chưa được khởi động | Xác định cấu phần 10 là hoàn toàn mới hay đã hoàn thành một phần, và ước tính khối lượng công việc của cấu phần đó tại Mục 3.6 | Edward, cùng với Phat | 2026-08-12 |
| 1 | Bảng điều khiển vận hành (cấu phần 7) là bắt buộc đối với chương trình thử nghiệm (pilot) hay có thể triển khai sau chương trình thử nghiệm (pilot) | Ở quy mô khối lượng của chương trình thử nghiệm (pilot), việc xử lý các trường hợp ngoại lệ có thể được thực hiện từ các màn hình quản trị hiện có, điều này sẽ loại bỏ một cấu phần khỏi phạm vi của chương trình thử nghiệm (pilot) | Edward | 2026-08-07 |
| 2 | Phân hệ dư nợ và báo cáo (cấu phần 8) thuộc phạm vi của chương trình thử nghiệm (pilot) hay được hoãn lại | Phụ thuộc vào các báo cáo mà VPBank mong muốn nhận được trong thời gian chương trình thử nghiệm (pilot) | Edward, cùng với VPBank | Chờ VPBank xác nhận |
| 3 | Khu vực lưu trữ vận hành đối với dữ liệu cá nhân, và quan điểm về việc xử lý dữ liệu trong nước | Được nêu tại Mục 4.4; ảnh hưởng đến hạng mục hạ tầng của mục này. Việc triển khai hiện nay đặt tại một địa điểm đám mây trong khu vực nhưng ngoài lãnh thổ Việt Nam, do đó một cam kết xử lý trong nước là một cuộc di dời hạ tầng chứ không phải sự mô tả hiện trạng | Edward | 2026-08-07 |

---

*Điều kiện phụ thuộc: không có. Thống nhất với Mục 3.1 (quy trình), Mục 3.3 và 3.4 (phần xây dựng của VPBank), Mục 3.6 (khối lượng công việc) và Mục 4.4 (bảo vệ dữ liệu).*
