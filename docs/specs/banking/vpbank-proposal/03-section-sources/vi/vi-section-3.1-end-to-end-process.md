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
