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
