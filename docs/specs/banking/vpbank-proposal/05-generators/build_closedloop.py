#!/usr/bin/env python3
"""Closed-loop money transfer with FundLok's fee as an instruction line, and VPBank's gate.

Four party lanes x five loop stages, plus an expanded four-gate control panel showing how
VPBank bounds what FundLok can take on any single instruction.

One geometry pass, two languages:  python3 build_closedloop.py en|vi
Vietnamese strings follow VI-GLOSSARY.md, including the mandated renderings
lượt chuyển tiền / lệnh thanh toán / bị tạm giữ / sơ đồ phân luồng trách nhiệm.
"""
import html, pathlib, sys, textwrap

OUTDIR = pathlib.Path(__file__).resolve().parent.parent / "04-diagrams"

LANG = (sys.argv[1] if len(sys.argv) > 1 else "en").lower()
VI = LANG == "vi"

# ─────────────────────────────────────────────────────────────────────── strings
S = {
"title":        ("Section 1.4 — the closed loop, and the gate on FundLok's fee",
                 "Mục 1.4 — vòng kín và cơ chế kiểm soát phí của FundLok"),
"sub":          ("Money never leaves the escrow perimeter except to an account already registered as a permitted destination. FundLok's fee is a line inside a beneficiary payment, not a payment of its own.",
                 "Tiền không rời khỏi phạm vi tài khoản ký quỹ, trừ khi chuyển đến một tài khoản đã được đăng ký trong danh sách tài khoản đích được phép. Phí của FundLok là một dòng nằm bên trong lệnh thanh toán cho người thụ hưởng, không phải một lệnh riêng."),
"meta":         ("Working case: loan of VND 2.5 billion, eight participating investors, 1% disbursement fee. FundLok internal estimates dated 5 August 2026.",
                 "Trường hợp minh hoạ: khoản vay VND 2.5 tỷ, tám nhà đầu tư tham gia, phí giải ngân 1%. Ước lượng nội bộ của FundLok ngày 5 August 2026."),

"svg_t1":       ("Every movement below is executed by VPBank on a dual-authorised instruction from FundLok. FundLok holds none of the funds and has no",
                 "Mọi lượt chuyển tiền dưới đây do VPBank thực hiện trên cơ sở lệnh thanh toán có phê duyệt kép của FundLok. FundLok không giữ tiền và không có"),
"svg_t2":       ("withdrawal right over the escrow account. Its own fee never travels alone — it rides inside an instruction that pays a beneficiary in the",
                 "quyền rút tiền đối với tài khoản ký quỹ. Phí của FundLok không bao giờ đi một mình — phí nằm bên trong lệnh thanh toán chi trả cho người"),
"svg_t3":       ("same movement, as a proportion VPBank can check on the face of the instruction.",
                 "thụ hưởng trong cùng một lượt chuyển tiền, theo tỷ lệ mà VPBank có thể kiểm tra ngay trên mặt lệnh."),
"svg_closed":   ("The loop is closed: whatever an investor receives can be paid out only to the bank account that investor funded from.",
                 "Vòng kín: khoản mà nhà đầu tư nhận được chỉ có thể chi trả về đúng tài khoản ngân hàng mà nhà đầu tư đó đã chuyển tiền đi."),

"lane_inv":     ("Investor", "Nhà đầu tư"),
"lane_inv_r":   ("lender of record", "bên cho vay chính thức"),
"lane_sme":     ("SME", "SME"),
"lane_sme_r":   ("borrower", "bên đi vay"),
"lane_vpb":     ("VPBank", "VPBank"),
"lane_vpb_r":   ("custodian — holds and moves the money", "đơn vị lưu ký — giữ và chuyển tiền"),
"lane_fl":      ("FundLok", "FundLok"),
"lane_fl_r":    ("arranger & servicer — issues instructions, holds no escrow funds", "bên thu xếp & vận hành — phát hành lệnh, không giữ tiền ký quỹ"),

"st1":          ("Funding", "Cấp vốn"),
"st1f":         ("once, as each investor commits", "một lần, khi mỗi nhà đầu tư cam kết"),
"st2":          ("Disbursement", "Giải ngân"),
"st2f":         ("once, when the target is met", "một lần, khi đủ số vốn mục tiêu"),
"st3":          ("Daily collection", "Thu nợ hằng ngày"),
"st3f":         ("every business day", "mỗi ngày làm việc"),
"st4":          ("Daily allocation", "Phân bổ hằng ngày"),
"st4f":         ("every business day", "mỗi ngày làm việc"),
"st5":          ("Withdrawal or reinvestment", "Rút tiền hoặc tái đầu tư"),
"st5f":         ("on the investor's request", "theo yêu cầu của nhà đầu tư"),
"feebearing":   ("fee-bearing", "có dòng phí"),

# nodes
"n_a1":         ("Investor's own bank account", "Tài khoản ngân hàng của nhà đầu tư"),
"n_a1s":        ("recorded at M1 — the only external destination open to them thereafter",
                 "được ghi nhận tại M1 — sau đó là tài khoản đích bên ngoài duy nhất"),
"n_a2":         ("Balance available same day", "Số dư khả dụng trong ngày"),
"n_a2s":        ("visible on the platform; transferred only when asked for",
                 "hiển thị trên nền tảng; chỉ chuyển đi khi có yêu cầu"),
"n_a3":         ("Withdrawal request", "Yêu cầu rút tiền"),
"n_a3s":        ("the amount is theirs; the destination is not selectable",
                 "số tiền là của họ; tài khoản đích không thể tự chọn"),
"n_b1":         ("SME's verified account", "Tài khoản đã xác thực của SME"),
"n_b1s":        ("receives the principal less the 1% fee", "nhận vốn gốc sau khi trừ phí 1%"),
"n_b2":         ("Daily revenue share", "Chia sẻ doanh thu hằng ngày"),
"n_b2s":        ("a % of prior-day revenue, computed from T-VAN", "một % doanh thu ngày trước, tính từ T-VAN"),
"n_d1":         ("Project escrow account — restricted, at VPBank", "Tài khoản ký quỹ của dự án — hạn chế, tại VPBank"),
"n_d1s":        ("all principal and all receipts rest here · FundLok has no withdrawal right",
                 "toàn bộ vốn gốc và các khoản thu nằm tại đây · FundLok không có quyền rút tiền"),
"n_d2":         ("Investor holdings at VPBank", "Số dư nắm giữ của nhà đầu tư tại VPBank"),
"n_d2s":        ("one escrow account per investor under Option B", "mỗi nhà đầu tư một tài khoản ký quỹ (Phương án B)"),
"n_c1":         ("Match and record", "Đối chiếu và ghi nhận"),
"n_c1s":        ("records the originating account — no funds touched",
                 "ghi nhận tài khoản chuyển tiền nguồn — không chạm vào tiền"),
"n_c3":         ("Compute and request", "Tính toán và yêu cầu"),
"n_c3s":        ("reads T-VAN; issues the payment request", "đọc T-VAN; phát hành yêu cầu thanh toán"),
"n_c5":         ("Relay only", "Chỉ chuyển tiếp"),
"n_c5s":        ("cannot alter, add or substitute a destination", "không thể thay đổi, thêm hoặc thay thế tài khoản đích"),
"n_fee":        ("FundLok fee account — outside the escrow perimeter", "Tài khoản phí của FundLok — ngoài phạm vi ký quỹ"),
"n_fees":       ("credited only as a line inside an instruction that pays a beneficiary in the same movement",
                 "chỉ được ghi có dưới dạng một dòng bên trong lệnh thanh toán chi trả cho người thụ hưởng trong cùng lượt chuyển tiền"),

"i_disb":       ("Disbursement instruction", "Lệnh giải ngân"),
"i_alloc":      ("Allocation instruction", "Lệnh phân bổ"),
"i_tag":        ("dual authorisation · one instruction, two lines", "phê duyệt kép · một lệnh, hai dòng"),
"i_d1":         ("1 · pay the SME — gross principal less 1%", "1 · chi trả SME — vốn gốc trước phí trừ 1%"),
"i_d2":         ("2 · pay FundLok — 1% of the gross", "2 · chi trả FundLok — 1% của vốn gốc trước phí"),
"i_a1":         ("1 · pay each investor — pro-rata share", "1 · chi trả từng nhà đầu tư — phần theo tỷ lệ"),
"i_a2":         ("2 · pay FundLok — a % of that same allocation", "2 · chi trả FundLok — một % của chính khoản phân bổ đó"),

# edges
"e_m1":         ("M1 · principal", "M1 · vốn gốc"),
"e_m2":         ("M2 · principal less fee", "M2 · vốn gốc sau phí"),
"e_m3":         ("M3 · disbursement fee", "M3 · phí giải ngân"),
"e_m4":         ("M4 · daily revenue share", "M4 · chia sẻ doanh thu hằng ngày"),
"e_m5":         ("M5 · allocation", "M5 · phân bổ"),
"e_m6":         ("M6 · management fee", "M6 · phí quản lý khoản vay"),
"e_m7":         ("M7 · withdrawal — to the registered account, and no other. The loop closes here.",
                 "M7 · rút tiền — về đúng tài khoản đã đăng ký, không tài khoản nào khác. Vòng kín đóng lại tại đây."),
"e_m8":         ("M8 · reinvestment", "M8 · tái đầu tư"),
"e_ins":        ("instruction", "lệnh thanh toán"),
"e_gate":       ("gate", "kiểm soát"),

# panel
"p_title":      ("The gate, expanded — VPBank's control on every instruction that contains a FundLok fee line (M3, M6)",
                 "Cơ chế kiểm soát, diễn giải chi tiết — kiểm soát của VPBank đối với mọi lệnh thanh toán có chứa dòng phí của FundLok (M3, M6)"),
"p_sub":        ("Four checks, all on the face of the instruction. VPBank needs no knowledge of the loan to apply them.",
                 "Bốn bước kiểm tra, tất cả đều thực hiện ngay trên mặt lệnh. VPBank không cần biết thông tin khoản vay để áp dụng."),
"g1":           ("Destination", "Tài khoản đích"),
"g1q":          ("Is every beneficiary on the registered permitted-destination list?",
                 "Mọi người thụ hưởng có nằm trong danh sách tài khoản đích được phép đã đăng ký không?"),
"g1f":          ("Fails on any account not on the list — including FundLok's own.",
                 "Không đạt nếu có tài khoản ngoài danh sách — kể cả tài khoản của chính FundLok."),
"g2":           ("Pairing", "Ghép cặp"),
"g2q":          ("Does the fee line sit inside an instruction that also pays a beneficiary?",
                 "Dòng phí có nằm trong một lệnh đồng thời chi trả cho người thụ hưởng không?"),
"g2f":          ("Fails on a fee line standing alone, or any draw on an idle balance.",
                 "Không đạt nếu dòng phí đứng một mình, hoặc rút từ số dư đang để không."),
"g3":           ("Proportion and ceiling", "Tỷ lệ và mức trần"),
"g3q":          ("Is the fee line within the registered proportion of this instruction, and within the registered ceiling?",
                 "Dòng phí có nằm trong tỷ lệ đã đăng ký của chính lệnh này, và trong mức trần đã đăng ký không?"),
"g3f":          ("Arithmetic, not a representation. Both values to be confirmed with VPBank.",
                 "Là phép tính, không phải lời cam kết. Cả hai giá trị cần xác nhận với VPBank."),
"g4":           ("Hold", "Tạm giữ"),
"g4q":          ("Is either account held under the dispute mechanism?",
                 "Có tài khoản nào đang bị tạm giữ theo cơ chế xử lý tranh chấp không?"),
"g4f":          ("If held, the fee line is suspended for the duration — the beneficiary line still settles.",
                 "Nếu bị tạm giữ, dòng phí bị tạm ngưng trong thời gian đó — dòng chi trả người thụ hưởng vẫn được thực hiện."),
"p_pass":       ("PASS", "ĐẠT"),
"p_passd":      ("VPBank executes the beneficiary line and the fee line as one movement. Neither can settle without the other.",
                 "VPBank thực hiện dòng chi trả người thụ hưởng và dòng phí trong cùng một lượt chuyển tiền. Không dòng nào được thực hiện nếu thiếu dòng kia."),
"p_fail":       ("FAIL at any gate", "KHÔNG ĐẠT tại bất kỳ bước nào"),
"p_faild":      ("The whole instruction is rejected and returned to FundLok's exception queue. No fee moves, no balance moves, and FundLok cannot resubmit against a different destination.",
                 "Toàn bộ lệnh bị từ chối và chuyển về danh sách trường hợp ngoại lệ của FundLok. Không có phí nào được chuyển, không có số dư nào dịch chuyển, và FundLok không thể gửi lại lệnh với một tài khoản đích khác."),

"note":         ("How much FundLok can take is therefore not a policy FundLok promises to keep. It is arithmetic VPBank checks on each instruction, bounded twice — as a proportion of that instruction, and by a registered ceiling.",
                 "Vì vậy, số tiền FundLok có thể lấy không phải là một chính sách do FundLok tự cam kết tuân thủ. Đó là phép tính VPBank kiểm tra trên từng lệnh, bị giới hạn hai lần — theo tỷ lệ của chính lệnh đó, và theo mức trần đã đăng ký."),

"cap":          ("Colour carries the kind of movement. The two orange lines, M3 and M6, are the only movements that reach FundLok, and each is a line inside the instruction that pays a beneficiary in the same movement — never an instruction of its own. FundLok is never a permitted destination for principal.",
                 "Màu sắc thể hiện loại lượt chuyển tiền. Hai đường màu cam, M3 và M6, là hai lượt chuyển tiền duy nhất đến FundLok, và mỗi lượt là một dòng nằm trong lệnh thanh toán chi trả cho người thụ hưởng trong cùng lượt chuyển tiền — không bao giờ là một lệnh riêng. FundLok không bao giờ là tài khoản đích được phép đối với vốn gốc."),
"cap2":         ("Rates and ceilings are to be confirmed with VPBank; the mechanism does not depend on their values. Section 1.4.4 states the four constraints in full; Section 1.4.3 states the closed-loop rule.",
                 "Mức phí và mức trần cần xác nhận với VPBank; cơ chế không phụ thuộc vào giá trị cụ thể. Mục 1.4.4 nêu đầy đủ bốn ràng buộc; Mục 1.4.3 nêu quy tắc vòng kín."),

"leg_pr":       ("Principal", "Vốn gốc"),
"leg_fe":       ("FundLok fee — inside a beneficiary instruction", "Phí FundLok — bên trong lệnh chi trả người thụ hưởng"),
"leg_rp":       ("Repayment & allocation", "Trả nợ & phân bổ"),
"leg_wd":       ("Withdrawal & reinvestment", "Rút tiền & tái đầu tư"),
"leg_in":       ("Instruction — data, not money", "Lệnh thanh toán — dữ liệu, không phải tiền"),

"tx_h":         ("Text equivalent", "Nội dung dạng văn bản"),
"tx_m":         ("The movements", "Các lượt chuyển tiền"),
"tx_g":         ("The four gates", "Bốn bước kiểm soát"),
"th_ref":       ("Ref", "Mã"),
"th_mv":        ("Movement", "Lượt chuyển tiền"),
"th_from":      ("From", "Từ"),
"th_to":        ("To", "Đến"),
"th_gate":      ("Gate", "Bước kiểm soát"),
"th_q":         ("Check applied", "Nội dung kiểm tra"),
"th_fail":      ("Consequence", "Hệ quả"),
"theme":        ("Toggle dark mode", "Chuyển chế độ tối"),
}


def t(k):
    return S[k][1 if VI else 0]


def esc(s):
    return html.escape(s, quote=True)


def wrap(s, w):
    return textwrap.wrap(s, width=w) if s else []


# ──────────────────────────────────────────────────────────────────── geometry
LW = 158                      # lane-label column
SW = 206                      # stage column
NST = 5
NW = 156                      # default node width
NX = 25                       # node inset inside its stage
PAD = 16
W = LW + NST * SW + PAD       # 1204

TIT_Y = [22, 40, 58]
CLOSED_Y = 80
BAND_Y = 94                   # stage-header band
BAND_H = 70
STRIP_Y = BAND_Y + BAND_H + 16   # the M7 return strip
HEAD = STRIP_Y + 16

LANES = [
    ("inv", "lane_inv", "lane_inv_r", "p1", 120),
    ("sme", "lane_sme", "lane_sme_r", "p2", 104),
    ("vpb", "lane_vpb", "lane_vpb_r", "p4", 108),
    ("flk", "lane_fl", "lane_fl_r", "p3", 250),
]
LY = {}
_y = HEAD
for k, _, _, _, h in LANES:
    LY[k] = _y
    _y += h
LANES_BOT = _y

STAGES = [("1", "st1", "st1f", False), ("2", "st2", "st2f", True),
          ("3", "st3", "st3f", False), ("4", "st4", "st4f", True),
          ("5", "st5", "st5f", False)]


def sx(i):
    return LW + i * SW


# nodes: id -> lane, stage_a, stage_b, yo, h, kind, label-key, sub-key
NODES = {
    "A1":  ("inv", 0, 0, 18, 74, "pr",  "n_a1",  "n_a1s"),
    "A2":  ("inv", 3, 3, 18, 74, "rpx", "n_a2",  "n_a2s"),
    "A3":  ("inv", 4, 4, 18, 74, "wdx", "n_a3",  "n_a3s"),
    "B1":  ("sme", 1, 1, 24, 58, "pr",  "n_b1",  "n_b1s"),
    "B2":  ("sme", 2, 2, 24, 58, "rp",  "n_b2",  "n_b2s"),
    "D1":  ("vpb", 0, 3, 24, 60, "es",  "n_d1",  "n_d1s"),
    "D2":  ("vpb", 4, 4, 24, 68, "es",  "n_d2",  "n_d2s"),
    "C1":  ("flk", 0, 0, 60, 60, "ins", "n_c1",  "n_c1s"),
    "C3":  ("flk", 2, 2, 60, 60, "ins", "n_c3",  "n_c3s"),
    "C5":  ("flk", 4, 4, 60, 60, "ins", "n_c5",  "n_c5s"),
    "FEE": ("flk", 1, 3, 182, 54, "fe", "n_fee", "n_fees"),
}
INSTR = {  # compound instruction boxes in the FundLok lane
    "C2": (1, 34, 136, "i_disb", ("i_d1", "i_d2")),
    "C4": (3, 34, 136, "i_alloc", ("i_a1", "i_a2")),
}

# vertical channels: money drops to the fee account use the left edge of the fee stage,
# instruction arrows rise at a channel clear of every node
def drop_x(st):
    return sx(st) + 11


def instr_x(st):
    return sx(st) + 150      # rises out of the right-hand side of the instruction box


D1_END = sx(3) + NX + NW      # the escrow perimeter runs from funding through allocation
A3_X, A3_W = sx(4) + 6, 140    # shifted left, clear of the M7 riser
FEE_X0 = sx(1) + 2
FEE_X1 = D1_END          # the fee bar ends flush with the escrow bar above it

RECT = {}
for nid, (lane, a_, b_, yo, h, kind, lk, sk) in NODES.items():
    x = sx(a_) + NX
    w = (b_ - a_) * SW + NW
    if nid == "D1":
        w = D1_END - x
    if nid == "A3":
        x, w = A3_X, A3_W
    if nid == "FEE":
        x, w = FEE_X0, FEE_X1 - FEE_X0
    RECT[nid] = (x, LY[lane] + yo, w, h)
for nid, (st, yo, h, tk, lines) in INSTR.items():
    RECT[nid] = (sx(st) + NX, LY["flk"] + yo, NW, h)


def cy(nid):
    x, y, w, h = RECT[nid]
    return y + h / 2


p = []
a = p.append

# ───────────────────────────────────────────────────────────── header + bands
a(f'<text class="t1" x="{PAD}" y="{TIT_Y[0]}">{esc(t("svg_t1"))}</text>')
a(f'<text class="t1" x="{PAD}" y="{TIT_Y[1]}">{esc(t("svg_t2"))}</text>')
a(f'<text class="t1" x="{PAD}" y="{TIT_Y[2]}">{esc(t("svg_t3"))}</text>')
a(f'<text class="closed" x="{PAD}" y="{CLOSED_Y}">{esc(t("svg_closed"))}</text>')

for li, (k, nk, rk, slot, h) in enumerate(LANES):
    a(f'<rect class="{"bandalt" if li % 2 else "band"}" x="0" y="{LY[k]}" '
      f'width="{W - PAD}" height="{h}"/>')
    a(f'<rect class="laneedge {slot}-fill" x="0" y="{LY[k]}" width="4" height="{h}"/>')
    a(f'<text class="lanename" x="14" y="{LY[k] + 26}">{esc(t(nk))}</text>')
    for i, ln in enumerate(wrap(t(rk), 21)):
        a(f'<text class="lanerole" x="14" y="{LY[k] + 44 + i * 12}">{esc(ln)}</text>')

a(f'<rect class="headband" x="0" y="{BAND_Y}" width="{W - PAD}" height="{BAND_H}"/>')
for i, (num, nk, fk, fee) in enumerate(STAGES):
    x = sx(i)
    a(f'<circle class="stnum-bg" cx="{x + NX + 10}" cy="{BAND_Y + 19}" r="10"/>')
    a(f'<text class="stnum" x="{x + NX + 10}" y="{BAND_Y + 23}" text-anchor="middle">{num}</text>')
    nl = wrap(t(nk), 18)
    a(f'<text class="stname" x="{x + NX + 26}" y="{BAND_Y + 23}">{esc(nl[0])}</text>')
    for j, ln in enumerate(nl[1:]):
        a(f'<text class="stname" x="{x + NX}" y="{BAND_Y + 36 + j * 12}">{esc(ln)}</text>')
    a(f'<text class="stfreq" x="{x + NX}" y="{BAND_Y + 51}">{esc(t(fk))}</text>')
    if fee:
        a(f'<rect class="feebar f-fe" x="{x + 1}" y="{BAND_Y + 1}" width="{SW - 2}" height="3"/>')
        a(f'<text class="feetagtx" x="{x + NX}" y="{BAND_Y + 64}">{esc(t("feebearing"))}</text>')

for i in range(NST + 1):
    a(f'<line class="colsep" x1="{sx(i)}" y1="{BAND_Y}" x2="{sx(i)}" y2="{LANES_BOT}"/>')
for li, (k, nk, rk, slot, h) in enumerate(LANES):
    a(f'<line class="rowsep" x1="0" y1="{LY[k]}" x2="{W - PAD}" y2="{LY[k]}"/>')
a(f'<line class="rowsep" x1="0" y1="{LANES_BOT}" x2="{W - PAD}" y2="{LANES_BOT}"/>')


# ───────────────────────────────────────────────────────────────────── nodes
def draw_node(nid):
    lane, sa, sb, yo, h, kind, lk, sk = NODES[nid]
    x, y, w, hh = RECT[nid]
    dashed = kind.endswith("x")
    base = kind[:-1] if dashed else kind
    cls = "nodedash" if dashed else ("nodebox-es" if base == "es" else "nodebox")
    a(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{hh}" rx="6"/>')
    if not dashed:
        a(f'<rect class="nodeedge f-{base}" x="{x}" y="{y}" width="3.5" height="{hh}" rx="1.75"/>')
    cw = int((w - 26) / 5.9)
    ll = wrap(t(lk), cw)
    sl = wrap(t(sk), int(cw * 1.16))
    ty = y + 17 if len(ll) + len(sl) > 3 else y + 20
    a(f'<text class="nodelabel" x="{x + 12}" y="{ty}">')
    for i, ln in enumerate(ll):
        a(f'<tspan x="{x + 12}" dy="{0 if i == 0 else 12}">{esc(ln)}</tspan>')
    a('</text>')
    syy = ty + len(ll) * 12 + 3
    a(f'<text class="nodesub" x="{x + 12}" y="{syy}">')
    for i, ln in enumerate(sl):
        a(f'<tspan x="{x + 12}" dy="{0 if i == 0 else 10.5}">{esc(ln)}</tspan>')
    a('</text>')


for nid in ("A1", "A2", "A3", "B1", "B2", "D1", "D2", "C1", "C3", "C5", "FEE"):
    draw_node(nid)

for nid, (st, yo, h, tk, lines) in INSTR.items():
    x, y, w, hh = RECT[nid]
    a(f'<rect class="instrbox" x="{x}" y="{y}" width="{w}" height="{hh}" rx="6"/>')
    a(f'<rect class="nodeedge f-ins" x="{x}" y="{y}" width="3.5" height="{hh}" rx="1.75"/>')
    yy = y + 16
    for ln in wrap(t(tk), 22):
        a(f'<text class="instrtitle" x="{x + 12}" y="{yy}">{esc(ln)}</text>')
        yy += 12
    for ln in wrap(t("i_tag"), 27):
        a(f'<text class="instrtag" x="{x + 12}" y="{yy + 1}">{esc(ln)}</text>')
        yy += 10
    yy += 6
    for j, lk in enumerate(lines):
        kind = "fe" if j else "pr"
        wl = wrap(t(lk), 26)
        a(f'<rect class="instrline l-{kind}" x="{x + 9}" y="{yy - 8}" width="{w - 18}" '
          f'height="{11 * len(wl) + 3}" rx="3"/>')
        for ln in wl:
            a(f'<text class="instrtx t-{kind}" x="{x + 14}" y="{yy}">{esc(ln)}</text>')
            yy += 11
        yy += 9


# ───────────────────────────────────────────────────────────────────── edges
def arrow(d, kind, dash=False):
    a(f'<path class="edge e-{kind}{" dashed" if dash else ""}" d="{d}" marker-end="url(#a-{kind})"/>')


def lbl(x, y, label, kind, band="band", cw=5.0, padw=10):
    pw = len(label) * cw + padw
    a(f'<rect class="plate {band}" x="{x - pw / 2}" y="{y - 10}" width="{pw}" height="13" rx="3"/>')
    a(f'<text class="edgelabel t-{kind}" x="{x}" y="{y}" text-anchor="middle">{esc(label)}</text>')


A1x, A1y, A1w, A1h = RECT["A1"]
B1x, B1y, B1w, B1h = RECT["B1"]
B2x, B2y, B2w, B2h = RECT["B2"]
D1x, D1y, D1w, D1h = RECT["D1"]
D2x, D2y, D2w, D2h = RECT["D2"]
Fx, Fy, Fw, Fh = RECT["FEE"]

# M1 — investor's own account into the project escrow (crosses the empty SME cell)
x = A1x + 60
arrow(f"M {x} {A1y + A1h} V {D1y - 8}", "pr")
lbl(x, LY["sme"] + 16, t("e_m1"), "pr", "bandalt")

# M2 — escrow to the SME
x = B1x + 60
arrow(f"M {x} {D1y} V {B1y + B1h + 8}", "pr")
lbl(x, LY["vpb"] + 16, t("e_m2"), "pr", "band")

# M4 — the SME's daily revenue share into escrow
x = B2x + 96
arrow(f"M {x} {B2y + B2h} V {D1y - 8}", "rp")
lbl(x, LY["vpb"] + 16, t("e_m4"), "rp", "band")

# M5 out to the investor holdings, M8 back in — same gap, opposite directions
gapmid = (D1x + D1w + D2x) / 2
arrow(f"M {D1x + D1w + 3} {D1y + 18} H {D2x - 8}", "rp")
arrow(f"M {D2x - 3} {D1y + 44} H {D1x + D1w + 8}", "wd")
# labels sit in the lane margins above and below the pair, not in the narrow gap between them
lbl(D1x + D1w - 27, LY["vpb"] + 16, t("e_m5"), "rp", "band")
lbl(D1x + D1w - 27, LY["vpb"] + 100, t("e_m8"), "wd", "band")

# M3 and M6 — the two fee lines, dropping out of escrow into FundLok's own account
for st, key in ((1, "e_m3"), (3, "e_m6")):
    x = drop_x(st)
    arrow(f"M {x} {D1y + D1h} V {Fy - 8}", "fe")
    lbl(x + 50, LY["flk"] + 16, t(key), "fe", "bandalt")

# instructions rise from FundLok to VPBank, through the gate
for nid, st in (("C2", 1), ("C4", 3)):
    ix, iy, iw, ih = RECT[nid]
    x = instr_x(st)
    arrow(f"M {x} {iy} V {D1y + D1h + 8}", "ins", dash=True)
    gy = iy - 16
    gw = len(t("e_gate")) * 5.6 + 24
    a(f'<rect class="gatebox" x="{x - gw / 2}" y="{gy - 9}" width="{gw}" height="17" rx="8.5"/>')
    a(f'<text class="gatetx" x="{x}" y="{gy + 3}" text-anchor="middle">{esc(t("e_gate"))}</text>')

# M7 — the closing arc: holdings back to the account the investor funded from
arrow(f"M {D2x + D2w - 20} {D2y} V {STRIP_Y} H {LW - 10} V {cy('A1')} H {A1x - 8}", "wd")
lbl((LW + D2x) / 2, STRIP_Y - 6, t("e_m7"), "wd", "band")


svg1 = "\n".join(p)
H1 = LANES_BOT + 10
p = []
a = p.append

# ───────────────────────────────────────────────────────────────────── panel
PY = 8
GW, GGAP, GX0 = 214, 20, 26
GATES = [("g1", "g1q", "g1f"), ("g2", "g2q", "g2f"), ("g3", "g3q", "g3f"), ("g4", "g4q", "g4f")]
PW_ALL = W - PAD - 12 - GX0 + 12 - 14           # inner width of the panel content
PX = GX0 + 4 * (GW + GGAP)                      # PASS card
PASSW = GX0 + PW_ALL - PX

GQW, GFW = 34, 36
GH = 40 + max(11 * len(wrap(t(qk), GQW)) + 6 + 10 * len(wrap(t(fk), GFW))
              for _, qk, fk in GATES) + 12
GH = max(GH, 40 + 11 * len(wrap(t("p_passd"), 32)) + 12)

FAILL = wrap(t("p_faild"), 150)
FAILH = max(30, 14 + 12 * len(FAILL))
PANH = 54 + GH + 14 + FAILH + 16

a(f'<rect class="panel" x="12" y="{PY}" width="{W - PAD - 12}" height="{PANH}" rx="10"/>')
a(f'<text class="ptitle" x="{GX0}" y="{PY + 24}">{esc(t("p_title"))}</text>')
a(f'<text class="psub" x="{GX0}" y="{PY + 41}">{esc(t("p_sub"))}</text>')

GTOP = PY + 54
for gi, (nk, qk, fk) in enumerate(GATES):
    x = GX0 + gi * (GW + GGAP)
    a(f'<rect class="gatecard" x="{x}" y="{GTOP}" width="{GW}" height="{GH}" rx="7"/>')
    a(f'<rect class="nodeedge f-p4" x="{x}" y="{GTOP}" width="3.5" height="{GH}" rx="1.75"/>')
    a(f'<circle class="gnum-bg" cx="{x + 24}" cy="{GTOP + 20}" r="9"/>')
    a(f'<text class="gnum" x="{x + 24}" y="{GTOP + 23.5}" text-anchor="middle">{gi + 1}</text>')
    a(f'<text class="gname" x="{x + 39}" y="{GTOP + 24}">{esc(t(nk))}</text>')
    yy = GTOP + 43
    ql = wrap(t(qk), GQW)
    a(f'<text class="gq" x="{x + 13}" y="{yy}">')
    for i, ln in enumerate(ql):
        a(f'<tspan x="{x + 13}" dy="{0 if i == 0 else 11}">{esc(ln)}</tspan>')
    a('</text>')
    yy += 11 * len(ql) + 6
    a(f'<text class="gf" x="{x + 13}" y="{yy}">')
    for i, ln in enumerate(wrap(t(fk), GFW)):
        a(f'<tspan x="{x + 13}" dy="{0 if i == 0 else 10}">{esc(ln)}</tspan>')
    a('</text>')
    if gi < len(GATES) - 1:
        mx = x + GW + GGAP / 2
        a(f'<path class="chev" d="M {mx - 4} {GTOP + GH / 2 - 5} l 5 5 l -5 5"/>')

a(f'<rect class="passcard" x="{PX}" y="{GTOP}" width="{PASSW}" height="{GH}" rx="7"/>')
a(f'<rect class="nodeedge f-rp" x="{PX}" y="{GTOP}" width="3.5" height="{GH}" rx="1.75"/>')
a(f'<text class="passname" x="{PX + 13}" y="{GTOP + 24}">{esc(t("p_pass"))}</text>')
a(f'<text class="gq" x="{PX + 13}" y="{GTOP + 43}">')
for i, ln in enumerate(wrap(t("p_passd"), 32)):
    a(f'<tspan x="{PX + 13}" dy="{0 if i == 0 else 11}">{esc(ln)}</tspan>')
a('</text>')

FYY = GTOP + GH + 14
a(f'<rect class="failbar" x="{GX0}" y="{FYY}" width="{PW_ALL}" height="{FAILH}" rx="7"/>')
a(f'<text class="failname" x="{GX0 + 14}" y="{FYY + 19}">{esc(t("p_fail"))}</text>')
fw = len(t("p_fail")) * 6.6 + 34
a(f'<text class="faildesc" x="{GX0 + fw}" y="{FYY + 19}">')
for i, ln in enumerate(FAILL):
    a(f'<tspan x="{GX0 + fw}" dy="{0 if i == 0 else 12}">{esc(ln)}</tspan>')
a('</text>')

NY = PY + PANH + 26
NOTEL = wrap(t("note"), 168)
for i, ln in enumerate(NOTEL):
    a(f'<text class="note" x="{PAD}" y="{NY + i * 15}">{esc(ln)}</text>')

H2 = NY + 15 * len(NOTEL) + 10
svg2 = "\n".join(p)

# ─────────────────────────────────────────────────────────── text equivalents
MV = [
    ("M1", "e_m1", "n_a1", "n_d1"), ("M2", "e_m2", "n_d1", "n_b1"),
    ("M3", "e_m3", "n_d1", "n_fee"), ("M4", "e_m4", "n_b2", "n_d1"),
    ("M5", "e_m5", "n_d1", "n_d2"), ("M6", "e_m6", "n_d1", "n_fee"),
    ("M7", "e_m7", "n_d2", "n_a1"), ("M8", "e_m8", "n_d2", "n_d1"),
]
mv_rows = "\n".join(
    f'<tr><td class="tref">{r}</td><td>{esc(t(lk).split(" · ", 1)[-1])}</td>'
    f'<td>{esc(t(fk))}</td><td>{esc(t(tk))}</td></tr>'
    for r, lk, fk, tk in MV)
g_rows = "\n".join(
    f'<tr><td class="tref">{i + 1}</td><td><strong>{esc(t(nk))}</strong></td><td>{esc(t(qk))}</td><td>{esc(t(fk))}</td></tr>'
    for i, (nk, qk, fk) in enumerate(GATES))

LEGS = [("pr", "leg_pr"), ("fe", "leg_fe"), ("rp", "leg_rp"), ("wd", "leg_wd"), ("ins", "leg_in")]
legend = "\n".join(f'<span><span class="sw sw-{k}"></span>{esc(t(v))}</span>' for k, v in LEGS)

HTML = f"""<!DOCTYPE html>
<html lang="{'vi' if VI else 'en'}" data-palette="#2a78d6,#eb6834,#1baf7a,#4a3aa7">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(t('title'))}</title>
<style>
  :root {{
    color-scheme: light;
    --surface-1:#fcfcfb; --plane:#f9f9f7; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781;
    --grid:#e1e0d9; --axis:#c3c2b7; --border:rgba(11,11,11,0.10);
    --band:#fcfcfb; --bandalt:#f6f6f3; --cellbg:#ffffff; --esbg:#f1f0ec; --headband:#f2f2ee;
    --panel:#f6f6f3; --card:#ffffff;
    --pr:#2a78d6; --fe:#eb6834; --rp:#1baf7a; --wd:#4a3aa7;
    --p1:#2a78d6; --p2:#eb6834; --p3:#1baf7a; --p4:#4a3aa7;
    --ins:#7d7b74;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) {{
      color-scheme: dark;
      --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
      --grid:#2c2c2a; --axis:#4a4945; --border:rgba(255,255,255,0.10);
      --band:#1a1a19; --bandalt:#201f1e; --cellbg:#242422; --esbg:#2b2a27; --headband:#232322;
      --panel:#201f1e; --card:#242422;
      --pr:#3987e5; --fe:#d95926; --rp:#199e70; --wd:#9085e9;
      --p1:#3987e5; --p2:#d95926; --p3:#199e70; --p4:#9085e9;
      --ins:#98968f;
    }}
  }}
  :root[data-theme="dark"] {{
    color-scheme: dark;
    --surface-1:#1a1a19; --plane:#0d0d0d; --ink:#fff; --ink-2:#c3c2b7; --muted:#898781;
    --grid:#2c2c2a; --axis:#4a4945; --border:rgba(255,255,255,0.10);
    --band:#1a1a19; --bandalt:#201f1e; --cellbg:#242422; --esbg:#2b2a27; --headband:#232322;
    --panel:#201f1e; --card:#242422;
    --pr:#3987e5; --fe:#d95926; --rp:#199e70; --wd:#9085e9;
    --p1:#3987e5; --p2:#d95926; --p3:#199e70; --p4:#9085e9;
    --ins:#98968f;
  }}
  *{{box-sizing:border-box}}
  body{{margin:0;padding:26px 22px 48px;background:var(--plane);color:var(--ink);
       font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.55}}
  header,figure,details{{max-width:1260px;margin-left:auto;margin-right:auto}}
  h1{{font-size:21px;margin:0 0 6px;letter-spacing:-0.01em}}
  .sub{{color:var(--ink-2);margin:0 0 4px}} .meta{{color:var(--muted);font-size:12.5px;margin:0}}
  .toolbar{{max-width:1260px;margin:16px auto 12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
  button{{font:inherit;font-size:12.5px;padding:6px 13px;border-radius:999px;border:1px solid var(--border);
          background:var(--surface-1);color:var(--ink-2);cursor:pointer}}
  .legend{{margin-left:auto;display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--ink-2);align-items:center}}
  .legend .sw{{display:inline-block;width:20px;height:3px;border-radius:2px;margin-right:6px;vertical-align:3px}}
  .sw-pr{{background:var(--pr)}} .sw-fe{{background:var(--fe)}} .sw-rp{{background:var(--rp)}}
  .sw-wd{{background:var(--wd)}} .sw-ins{{background:var(--ins)}}
  .scroller{{overflow-x:auto;background:var(--surface-1);border:1px solid var(--border);border-radius:12px;padding:6px}}
  svg{{display:block;width:100%;height:auto}}
  .band{{fill:var(--band)}} .bandalt{{fill:var(--bandalt)}} .headband{{fill:var(--headband)}}
  .rowsep,.colsep{{stroke:var(--grid);stroke-width:1}}
  .nodebox{{fill:var(--cellbg);stroke:var(--border);stroke-width:1}}
  .nodebox-es{{fill:var(--esbg);stroke:var(--border);stroke-width:1.4}}
  .nodedash{{fill:none;stroke:var(--axis);stroke-width:1;stroke-dasharray:3 3}}
  .instrbox{{fill:var(--cellbg);stroke:var(--ink-2);stroke-width:1.3}}
  .instrline{{stroke:none;opacity:0.11}}
  .l-pr{{fill:var(--pr)}} .l-fe{{fill:var(--fe)}}
  .instrtitle{{font-size:11px;font-weight:660;fill:var(--ink)}}
  .instrtag{{font-size:8.6px;fill:var(--muted)}}
  .instrtx{{font-size:9.4px;font-weight:600}}
  .nodelabel{{font-size:10.8px;font-weight:640;fill:var(--ink)}}
  .nodesub{{font-size:9.2px;fill:var(--muted)}}
  .edge{{fill:none;stroke-width:1.8}} .edge.dashed{{stroke-width:1.4;stroke-dasharray:4 3}}
  .e-pr{{stroke:var(--pr)}} .e-fe{{stroke:var(--fe)}} .e-rp{{stroke:var(--rp)}}
  .e-wd{{stroke:var(--wd)}} .e-ins{{stroke:var(--ins)}}
  .edgelabel{{font-size:9.4px;font-weight:640;fill:var(--ink-2)}}
  .t-pr{{fill:var(--pr)}} .t-fe{{fill:var(--fe)}} .t-rp{{fill:var(--rp)}} .t-wd{{fill:var(--wd)}}
  .f-pr{{fill:var(--pr)}} .f-fe{{fill:var(--fe)}} .f-rp{{fill:var(--rp)}} .f-wd{{fill:var(--wd)}}
  .f-es{{fill:var(--muted)}} .f-ins{{fill:var(--ins)}} .f-p4{{fill:var(--p4)}}
  .p1-fill{{fill:var(--p1)}} .p2-fill{{fill:var(--p2)}} .p3-fill{{fill:var(--p3)}} .p4-fill{{fill:var(--p4)}}
  .plate{{stroke:none}}
  .t1{{font-size:11px;fill:var(--ink-2)}}
  .closed{{font-size:12px;font-weight:680;fill:var(--rp)}}
  .lanename{{font-size:12.5px;font-weight:660;fill:var(--ink)}}
  .lanerole{{font-size:9.2px;fill:var(--muted)}}
  .stnum{{font-size:9.6px;font-weight:700;fill:var(--surface-1)}} .stnum-bg{{fill:var(--ink)}}
  .stname{{font-size:11.4px;font-weight:660;fill:var(--ink)}}
  .stfreq{{font-size:9px;fill:var(--muted)}}
  .feetagtx{{font-size:8.8px;font-weight:680;fill:var(--fe)}}
  .feebar{{opacity:0.85}}
  .gatebox{{fill:var(--card);stroke:var(--p4);stroke-width:1.2}}
  .gatetx{{font-size:8.8px;font-weight:700;fill:var(--p4)}}
  .instrarr{{font-size:8.8px;fill:var(--ins)}}
  .panel{{fill:var(--panel);stroke:var(--border);stroke-width:1}}
  .ptitle{{font-size:12.4px;font-weight:680;fill:var(--ink)}}
  .psub{{font-size:9.6px;fill:var(--ink-2)}}
  .gatecard{{fill:var(--card);stroke:var(--border);stroke-width:1}}
  .passcard{{fill:var(--card);stroke:var(--rp);stroke-width:1.3}}
  .gnum{{font-size:9px;font-weight:700;fill:var(--card)}} .gnum-bg{{fill:var(--p4)}}
  .gname{{font-size:11px;font-weight:680;fill:var(--ink)}}
  .passname{{font-size:11px;font-weight:700;fill:var(--rp)}}
  .gq{{font-size:9.4px;fill:var(--ink-2)}}
  .gf{{font-size:8.8px;fill:var(--muted);font-style:italic}}
  .chev{{fill:none;stroke:var(--muted);stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}}
  .failbar{{fill:none;stroke:var(--ink-2);stroke-width:1.2;stroke-dasharray:5 3}}
  .failname{{font-size:10.4px;font-weight:700;fill:var(--ink)}}
  .faildesc{{font-size:9.4px;fill:var(--ink-2)}}
  .note{{font-size:9.6px;fill:var(--ink-2)}}
  figcaption{{font-size:12.5px;color:var(--muted);margin-top:11px}}
  figcaption p{{margin:0 0 5px}}
  figure.second{{margin-top:24px}}
  summary{{cursor:pointer;font-size:13px;color:var(--ink-2)}} details{{margin-top:24px}}
  table{{border-collapse:collapse;width:100%;margin:12px 0 20px;font-size:12.5px}}
  th,td{{text-align:left;padding:6px 9px;border-bottom:1px solid var(--grid);vertical-align:top}}
  th{{color:var(--muted);font-weight:620;font-size:11px;text-transform:uppercase;letter-spacing:0.04em}}
  h3{{font-size:12.5px;margin:18px 0 0;color:var(--ink-2)}}
  .tref{{font-weight:700;color:var(--ink-2);white-space:nowrap}}
  @media print{{
    @page {{ size: A4 landscape; margin: 9mm 11mm; }}
    body{{padding:0;background:#fff}} .toolbar{{display:none}}
    .scroller{{overflow:visible;border:none;padding:0;background:none}}
    header{{margin-bottom:5px}} h1{{font-size:12.5pt}} .sub{{font-size:8.4pt;margin-bottom:2px}}
    .meta{{font-size:7.6pt}}
    figure{{max-width:none;text-align:center;margin:0;break-inside:avoid}}
    figure.second{{break-before:page;margin-top:0}}
    svg{{width:238mm!important;height:auto!important;margin:0 auto}}
    figure.second svg{{width:246mm!important}}
    figcaption{{font-size:7.4pt;text-align:left;margin-top:4px}}
    details{{break-before:avoid;margin-top:8px;max-width:none}}
    summary{{font-size:8.4pt;font-weight:700;list-style:none}}
    h3{{font-size:8pt;margin:10px 0 0}}
    table{{font-size:7pt;margin:4px 0 8px}}
    th,td{{padding:2.5px 6px}}
    tr{{break-inside:avoid}}
  }}
</style></head>
<body>
<header>
  <h1>{esc(t('title'))}</h1>
  <p class="sub">{esc(t('sub'))}</p>
  <p class="meta">{esc(t('meta'))}</p>
</header>
<div class="toolbar">
  <button id="themeBtn" type="button">{esc(t('theme'))}</button>
  <div class="legend">{legend}</div>
</div>
<figure>
  <div class="scroller">
    <svg viewBox="0 0 {W} {H1}" role="img" aria-label="{esc(t('title'))}">
      <defs>
        <marker id="a-pr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--pr)"/></marker>
        <marker id="a-fe" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--fe)"/></marker>
        <marker id="a-rp" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--rp)"/></marker>
        <marker id="a-wd" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--wd)"/></marker>
        <marker id="a-ins" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M 0 1 L 9 5 L 0 9 z" fill="var(--ins)"/></marker>
      </defs>
{svg1}
    </svg>
  </div>
  <figcaption>
    <p>{esc(t('cap'))}</p>
  </figcaption>
</figure>
<figure class="second">
  <div class="scroller">
    <svg viewBox="0 0 {W} {H2}" role="img" aria-label="{esc(t('p_title'))}">
{svg2}
    </svg>
  </div>
  <figcaption>
    <p>{esc(t('cap2'))}</p>
  </figcaption>
</figure>
<details open>
  <summary>{esc(t('tx_h'))}</summary>
  <h3>{esc(t('tx_m'))}</h3>
  <table>
    <thead><tr><th>{esc(t('th_ref'))}</th><th>{esc(t('th_mv'))}</th><th>{esc(t('th_from'))}</th><th>{esc(t('th_to'))}</th></tr></thead>
    <tbody>
{mv_rows}
    </tbody>
  </table>
  <h3>{esc(t('tx_g'))}</h3>
  <table>
    <thead><tr><th>#</th><th>{esc(t('th_gate'))}</th><th>{esc(t('th_q'))}</th><th>{esc(t('th_fail'))}</th></tr></thead>
    <tbody>
{g_rows}
    </tbody>
  </table>
</details>
<script>
(function(){{
  document.getElementById('themeBtn').addEventListener('click',function(){{
    var r=document.documentElement;
    var d=r.getAttribute('data-theme')==='dark'||(!r.hasAttribute('data-theme')&&matchMedia('(prefers-color-scheme: dark)').matches);
    r.setAttribute('data-theme',d?'light':'dark');
  }});
}})();
</script>
</body></html>
"""

out = OUTDIR / f"section-1.4-closedloop{'-VI' if VI else ''}.html"
out.write_text(HTML)
print(f"{out}  {W}x{H1} + panel {W}x{H2}")
