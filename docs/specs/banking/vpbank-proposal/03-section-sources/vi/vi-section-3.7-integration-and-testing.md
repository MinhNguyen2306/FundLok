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
