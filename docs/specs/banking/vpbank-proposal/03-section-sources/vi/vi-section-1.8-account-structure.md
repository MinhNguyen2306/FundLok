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
