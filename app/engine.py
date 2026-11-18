"""Qist engine: no UI, no AI. Rules extract the terms, plain maths gives the cost, rules flag wording."""
import os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "model"))
from rules import extract, AR, ZERO
from cost import true_cost

NOFEE = re.compile(r"no (?:hidden )?fees?|fee[- ]free|without (?:any )?fees?|zero fees?|0% fees?|"
                   r"بدون (?:أي |اي )?رسوم|بدون فوائد ورسوم|دون رسوم|مجان", re.I)
# Fees that are not the price of the instalment itself: card fees, cash advances, late penalties, cash on delivery.
NOTINSTAL = re.compile(r"annual|issu|renewal|replacement|cash (?:advance|withdrawal)|withdrawal|international|late|overdue|penalt|delay|"
                       r"cash on delivery|\bCOD\b|statement|سنوي|السنوية|إصدار|اصدار|تجديد|بديل|سحب نقدي|رسوم السحب|دولية|تأخر|متأخر|غرامة|"
                       r"الدفع عند الاستلام|كشف حساب", re.I)
# 'free call number' is not a 'free instalments' claim.
TOLL = re.compile(r"(?:الرقم|رقم|الاتصال|اتصل|هاتف)[^\n]{0,25}المجاني|toll[- ]free|free (?:phone|call|number|hotline)", re.I)
# '0% installment', 'قسّط 0%', 'Qasset 0%': the zero sits next to the word for instalment, not next to 'interest'.
ZERO2 = re.compile(r"(?:installments?|instalments?|qasset|qist|epp|قسّ?ط|تقسيط|أقساط|اقساط)\s*[:\-]?\s*[%٪]?\s*0\s*[%٪]|0\s*[%٪]\s*(?:installments?|instalments?|qasset|qist|قسّ?ط|تقسيط|أقساط|اقساط)", re.I)
def _claim(t):
    t = TOLL.sub(" ", t)
    return (ZERO.search(t) or NOFEE.search(t) or ZERO2.search(t))
MONTHLY = re.compile(r"monthly|per month|/ ?month|شهري|شهريا|شهرياً|كل شهر", re.I)
ANNUAL = re.compile(r"annual|apr|per year|سنوي|السنوية|سنويا", re.I)

NOTFINANCE = re.compile(r"warrant|guarantee|maintenance|roadside|\bkm\b|ضمان|صيانة|كم\b|مساعدة الطريق|assistance", re.I)

def candidates(text):
    """rules.py output, except the instalment count ignores lines about warranty / maintenance / roadside cover
    ('5 years or 100,000 km' is the car warranty, not the financing period)."""
    c = extract(text)
    kept = "\n".join(l for l in text.splitlines() if not NOTFINANCE.search(l))
    c["n_installments"] = extract(kept)["n_installments"]
    return c

TENORS = {2, 3, 4, 5, 6, 9, 12, 18, 24, 30, 36, 48, 60, 72, 84}
_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%|%\s*(\d+(?:\.\d+)?)")
SKIPPCT = re.compile(r"down ?payment|vat|discount|cash ?back|% off|\boff\b|debt burden|dbr|final payment|card limit|credit limit|upfront|property|of the total|دفعة|مقدم|ضريبة|خصم|الأخيرة|الحد الائتماني|حد البطاقة", re.I)
FEEPCT = re.compile(r"administrative|admin fees?|processing fee|management fee|setup|رسوم إدارية|رسوم تأسيس|إدارية|fees? of|of (?:the )?(?:finance|financing|transaction|purchase)", re.I)
CAP = re.compile(r"(?:SAR|SR|ريال)\s*(\d[\d,]*)\s*(?:\(?whichever is (?:less|lower)|أيهما أقل)|(\d[\d,]*)\s*(?:SAR|SR|ريال)\s*(?:\(?whichever is (?:less|lower)|أيهما أقل)", re.I)

def _tenor(c, text):
    t = text.translate(AR)
    m = re.search(r"(?:chosen|selected|المختار)[^\n|]{0,40}[|:]\s*(\d+)\s*(?:months?|شهر|أشهر)", t, re.I)
    if m and int(m.group(1)) in TENORS: return int(m.group(1))
    cands = [int(v) for v in c["n_installments"] if v == int(v) and int(v) in TENORS]
    return max(cands) if cands else 0

def _line_window(t, a, b, before, after):
    """Text around a match, kept to the same line and cut at the neighbouring % sign so one figure does not borrow another's words."""
    ls = t.rfind("\n", 0, a) + 1; le = t.find("\n", b); le = len(t) if le < 0 else le
    left = t[max(ls, a - before):a]; left = left[left.rfind("%") + 1:] if "%" in left else left
    right = t[b:min(le, b + after)]; right = right[:right.find("%")] if "%" in right else right
    return left + " " + t[a:b] + " " + right

def _fee_sar(text):
    """First money amount next to a fee word (not a minimum/limit, not a monthly profit). Looks after any worked example first."""
    t = text.translate(AR)
    ex = re.search(r"example|illustrative|مثال", t, re.I)
    for start in ([ex.start()] if ex else []) + [0]:
        for m in _MONEY.finditer(t, start):
            w = _line_window(t, m.start(), m.end(), 45, 15)
            if re.search(FEEWORD, w, re.I) and not re.search(LIMITWORD, w, re.I) and not re.search(r"monthly|شهري", w, re.I):
                return float((m.group(1) or m.group(2)).replace(",", ""))
    return 0.0

def _percents(text):
    """Every percentage sorted into: profit rate (with monthly/annual/unknown) or fee-as-percent. Down payment, VAT, discounts are ignored."""
    t = text.translate(AR); rates, fees = [], []
    for m in _PCT.finditer(t):
        v = float(m.group(1) or m.group(2))
        w = _line_window(t, m.start(), m.end(), 40, 45)
        if SKIPPCT.search(w): continue
        if FEEPCT.search(w) and not re.search(r"profit|interest|ربح|فائدة|apr|monthly fees", w, re.I):
            if not NOTINSTAL.search(w): fees.append(v)
            continue
        kind = "monthly" if MONTHLY.search(w) else "annual" if ANNUAL.search(w) else "unknown"
        rates.append((v, kind))
    return rates, fees

PLAN1 = re.compile(r"(\d+(?:\.\d+)?)\s*%\s*(?:for|over|لمدة|على)?\s*(\d{1,2})\s*(?:months?|شهر|أشهر|اشهر)", re.I)
PLAN2 = re.compile(r"(\d{1,2})\s*(?:months?|شهر|أشهر|اشهر)\s*[|:\-–]\s*(\d+(?:\.\d+)?)\s*%", re.I)
MINBUY = re.compile(r"(?:minimum (?:purchase|transaction|spend)|الحد الأدنى)[^\n\d]{0,30}(?:SAR|SR|ريال)?\s*(\d[\d,]*)", re.I)

def plans(text):
    """Different rate for each length, e.g. '0% for 3 months, 1.5% for 6 months'. Returns {months: rate} if two or more are found."""
    t = text.translate(AR); out = {}
    for m in PLAN1.finditer(t): out[int(m.group(2))] = float(m.group(1))
    for m in PLAN2.finditer(t): out.setdefault(int(m.group(1)), float(m.group(2)))
    return out if len(out) >= 2 else {}

PRODUCT = [("bnpl", r"tamara|tabby|tweeq|buy now|bnpl|تمارا|تابي|اشتر[ِ]?ي? الآن"),
           ("card", r"credit card|cardholder|card holder|بطاقة ائتمان|البطاقة الائتمانية|بطاقات|حامل البطاقة|قسط|easy payment plan|tasaheal|تساهيل|qasset|epp"),
           ("finance", r"personal finance|car finance|leasing|murabaha|tawarruq|تمويل شخصي|تأجير|مرابحة|تورق|financing period|finance amount")]

def product_type(text):
    t = text.translate(AR)
    for name, rx in PRODUCT:
        if re.search(rx, t, re.I): return name
    return "unknown"

def example_price(text):
    """If the offer states a minimum purchase, use it as an example price (clearly labelled in the app)."""
    m = MINBUY.search(text.translate(AR))
    return float(m.group(1).replace(",", "")) if m else 0.0

def defaults(c, text):
    """Best first guess for each field. The user can change all of them in the app."""
    rates, fee_pcts = _percents(text)
    nz = [(v, k) for v, k in rates if v > 0]
    rate, kind = max(nz) if nz else (0.0, "none")
    sar_fee = _fee_sar(text)
    capm = CAP.search(text.translate(AR))
    cap = float((capm.group(1) or capm.group(2)).replace(",", "")) if capm else 0.0
    pl = plans(text); n_def = _tenor(c, text)
    if pl:                                             # a rate per plan: take the rate of the plan we default to
        n_def = n_def if n_def in pl else max(pl); rate = pl[n_def]
        kind = "monthly" if kind in ("none", "unknown") else kind     # per-length rates in Saudi card programmes are normally monthly
    return {
        "plans": pl, "product": product_type(text), "example_price": example_price(text),
        "rate_assumed": bool(pl) and kind == "monthly" and not MONTHLY.search(text),
        "cash_price": c["cash_price"][0] if c["cash_price"] else 0.0,
        "n_installments": n_def,
        "installment_amount": c["installment_amount"][0] if c["installment_amount"] else 0.0,
        "admin_fee": sar_fee,
        "admin_fee_pct": 0.0 if sar_fee else (fee_pcts[0] if fee_pcts else 0.0),
        "admin_fee_cap": cap,
        "late_fee": max(c["late_fee"]) if c["late_fee"] else 0.0,
        "profit_rate": rate, "rate_kind": kind,
        "shariah_claim": bool(c["shariah_claim"]),
    }

def cost(price, n, inst=0.0, admin_fee_sar=0.0, rate=0.0, rate_kind="none", fee_pct=0.0, fee_cap=0.0):
    """Total cost in SAR. If the instalment is known it is used as is. If not, it is worked out from the rate:
    monthly rate = flat on the original price each month (how Tasaheal's own example works);
    annual rate = standard reducing-balance instalment. Returns None if there is not enough to calculate."""
    if price <= 0 or n <= 0: return None
    if fee_pct > 0:                                   # fee quoted as a % of the amount, with an optional SAR cap
        pct_fee = price * fee_pct / 100
        admin_fee_sar += min(pct_fee, fee_cap) if fee_cap > 0 else pct_fee
    how = "from the instalment in the offer"
    if inst <= 0:
        if rate > 0 and rate_kind == "monthly":
            inst = price / n + price * rate / 100; how = "flat monthly rate on the original price"
        elif rate > 0:
            i = rate / 100 / 12
            inst = price * i / (1 - (1 + i) ** -n); how = "annual rate on a reducing balance"
        else:
            inst = price / n; how = "price divided equally (no profit rate found)"
    r = true_cost(price, inst, n, admin_fee_sar)
    r["instalment"] = round(inst, 2); r["how"] = how
    r["warnings"] = []
    if r["total_paid"] < price - 0.01: r["warnings"].append("below_price")      # you would pay less than the price: inputs are inconsistent
    if r["effective_annual_rate"] > 150: r["warnings"].append("extreme_rate")  # almost always a wrong price or instalment
    return r

FEEWORD = r"fees?|charges?|commission|one[- ]time|processing|administrative|عمولة|رسوم|مصاريف|لمرة واحدة"
LIMITWORD = r"minimum|maximum|limit|الحد|at least|not less|لا تقل|أقل من|يجب"
_MONEY = re.compile(r"(?:SAR|SR|S\.{1,2}R\.?|ريال(?:\s+سعودي)?|ر\.?\s?س|⃁)\s*(\d[\d,]*(?:\.\d+)?)|(\d[\d,]*(?:\.\d+)?)\s*(?:SAR|SR|S\.{1,2}R\.?|ريال(?:\s+سعودي)?|ر\.?\s?س|⃁)", re.I)

_LABEL = re.compile(r"^(?![#•])[^\n:：]{0,30}(?:%s)[^\n:：]{0,15}\n\s*(\d[\d,]*(?:\.\d+)?)\s*(?:فقط|only|SAR|SR|ريال|ر\.س)(?=\s|$)" % FEEWORD, re.I | re.M)

def _label_fees(t):
    """Table written one cell per line: a line that only says 'Service fee' and the next line is the amount."""
    return [(float(m.group(1).replace(",", "")), m) for m in _LABEL.finditer(t)
            if not NOTINSTAL.search(m.group(0)) and not re.search(LIMITWORD, m.group(0), re.I)]

def fee_amounts(text, c):
    """Fee amounts in the text: what rules.py found, plus money written next to fee words (commission, one-time...)."""
    t = text.translate(AR); out = [v for v in _percents(text)[1] if v > 0]      # fees quoted as a %, found by our own stricter check
    for m in _MONEY.finditer(t):
        w = _line_window(t, m.start(), m.end(), 45, 20)
        if re.search(FEEWORD, w, re.I) and not re.search(LIMITWORD, w, re.I) and not NOTINSTAL.search(_line_window(t, m.start(), m.end(), 60, 70)) and not MONTHLY.search(_line_window(t, m.start(), m.end(), 25, 8)):
            out.append(float((m.group(1) or m.group(2)).replace(",", "")))
    out += [v for v, _ in _label_fees(t) if v > 0]
    out.sort(key=lambda v: (v < 5, v))          # SAR amounts first in the message, small % fees after
    return sorted(set(out), key=lambda v: (v < 5, v))

def flags(text, c=None):
    """Explainable wording flags. Each is (code, details). 'zero_but_fee' is the misleading-wording warning;
    'zero_for_some_plans' is only an information note. Empty list = nothing found."""
    c = c or extract(text)
    t = text.translate(AR)
    zero_claim = (0.0 in c["profit_rate"]) or bool(_claim(t))
    fees = fee_amounts(text, c)
    rates = [v for v in c["profit_rate"] if v > 0]
    out = []
    if zero_claim and fees:
        out.append(("zero_but_fee", {"fee": fees[0]}))
    if zero_claim and rates and 0.0 in c["profit_rate"]:
        out.append(("zero_for_some_plans", {"rate": max(rates)}))
    return out

def evidence(text, fee):
    """Where in the pasted text the '0% / free' promise and the fee are written: each is (line, start, end) so the UI can
    quote the line and highlight the words. Digits are mapped one-to-one, so positions in the translated line fit the original line."""
    claim = feeloc = None
    lab = [(v, m) for v, m in _label_fees(text.translate(AR)) if v == fee]
    for line in text.splitlines():
        t = line.translate(AR)
        if not claim:
            m = _claim(t) or re.search(r"\b0\s*%", t)
            if m: claim = (line, m.start(), m.end())
        if not feeloc:
            for m in _MONEY.finditer(t):
                w = _line_window(t, m.start(), m.end(), 45, 20)
                if float((m.group(1) or m.group(2)).replace(",", "")) == fee and re.search(FEEWORD, w, re.I) and not re.search(LIMITWORD, w, re.I) and not NOTINSTAL.search(w):
                    feeloc = (line, m.start(), m.end()); break
            else:
                m = re.search(r"\b%g\s*%%" % fee, t)                      # a fee written as a percentage, e.g. 2%
                if m and re.search(FEEWORD, t, re.I): feeloc = (line, m.start(), m.end())
    if lab and not feeloc:                                   # amount on its own line under a 'Service fee' label line
        ls = text.splitlines()
        for i in range(1, len(ls)):
            t = ls[i].translate(AR); m = re.match(r"\s*(\d[\d,]*(?:\.\d+)?)", t)
            if m and float(m.group(1).replace(",", "")) == fee and re.search(FEEWORD, ls[i - 1], re.I):
                feeloc = (ls[i], m.start(1), m.end(1)); break
    return {"claim": claim, "fee": feeloc, "same_line": bool(claim and feeloc and claim[0] == feeloc[0])}

def is_misleading(fl):
    return any(code == "zero_but_fee" for code, _ in fl)

SAMA = {
 "en": {
   "zero_but_fee": "The offer says **\u201c0%\u201d**, **\u201cno profit\u201d** or **\u201cfree\u201d**, but it also charges **a fee of SAR {fee:g}**. Add that fee to what you pay: it is part of the real cost.",
   "zero_for_some_plans": "**\u201c0%\u201d** appears together with a rate of **{rate:g}%**. The 0% usually applies only to some plans or partners. Check which plan you are choosing.",
   "none": "No misleading-wording flag found by the rules. That does not prove there are no hidden costs: read the full terms.",
   "rules": "SAMA reference: under the SAMA Rules for Regulating Buy-Now-Pay-Later Companies, a BNPL company may not charge the consumer fees other than delay penalties and debt-collection fees (Art. 20(1)), and the contract must state the amount, number and due dates of instalments and the consequences of late payment (Art. 26). Bank card instalment programmes are covered by other SAMA rules (for example the APR calculation and price-disclosure rules). Qist does not decide whether an offer is lawful; it shows what to check.",
   "disc": "Not financial advice. Nothing you paste is stored. Check every figure against the provider's official terms."},
 "ar": {
   "zero_but_fee": "يعلن العرض عن **«0%»** أو **«بدون ربح»** أو **«مجاني»**، لكنه يفرض أيضاً **رسماً قدره {fee:g} ريال**. أضف هذا الرسم إلى ما ستدفعه، فهو جزء من التكلفة الحقيقية.",
   "zero_for_some_plans": "ظهرت **«0%»** مع نسبة **{rate:g}%**. غالباً تنطبق نسبة 0% على بعض الخطط أو الشركاء فقط. تأكد من الخطة التي تختارها.",
   "none": "لم تجد القواعد صياغة مضللة. هذا لا يثبت خلو العرض من تكاليف خفية، فاقرأ الشروط كاملة.",
   "rules": "مرجع ساما: بموجب قواعد تنظيم شركات «اشترِ الآن وادفع لاحقاً»، لا يجوز للشركة تحميل المستهلك رسوماً غير غرامات التأخير ورسوم التحصيل (المادة 20/1)، ويجب أن يوضح العقد مبلغ الأقساط وعددها وتواريخ استحقاقها وعواقب التأخر في السداد (المادة 26). أما برامج التقسيط على بطاقات البنوك فتخضع لقواعد أخرى لدى ساما (مثل قواعد احتساب معدل النسبة السنوي والإفصاح عن الأسعار). لا يحكم «قسط» على مشروعية العرض، بل يبيّن ما ينبغي التحقق منه.",
   "disc": "ليست نصيحة مالية. لا يتم حفظ ما تلصقه. تحقق من كل رقم من الشروط الرسمية لدى مزوّد الخدمة."},
}

SAMA_CARD = {
 "en": "SAMA reference: this looks like a bank card instalment programme, so it falls under the bank's card terms and SAMA's consumer-finance rules (for example the APR calculation and price-disclosure rules), not the Buy-Now-Pay-Later rules. The BNPL rule banning consumer fees (Art. 20(1)) applies to BNPL companies. Qist does not decide whether an offer is lawful; it shows what to check.",
 "ar": "مرجع ساما: يبدو أن هذا برنامج تقسيط على بطاقة بنكية، لذا يخضع لشروط البنك ولقواعد ساما لحماية العملاء (مثل قواعد احتساب معدل النسبة السنوي والإفصاح عن الأسعار) وليس لقواعد «اشترِ الآن وادفع لاحقاً». أما منع تحميل المستهلك الرسوم (المادة 20/1) فينطبق على شركات BNPL. لا يحكم «قسط» على مشروعية العرض، بل يبيّن ما ينبغي التحقق منه."}
PRODUCT_NAME = {
 "en": {"bnpl": "Buy-now-pay-later (BNPL) company", "card": "Bank credit-card instalment programme", "finance": "Finance product / loan", "unknown": "Type not clear"},
 "ar": {"bnpl": "شركة «اشترِ الآن وادفع لاحقاً»", "card": "برنامج تقسيط على البطاقة الائتمانية", "finance": "منتج تمويل / قرض", "unknown": "النوع غير واضح"}}

def explain(lang, fl, product="unknown"):
    S = SAMA[lang]
    msgs = [S[code].format(**d) for code, d in fl] or [S["none"]]
    rules = SAMA_CARD[lang] if product in ("card", "finance") else S["rules"]
    return msgs, rules, S["disc"]
