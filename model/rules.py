"""Rule-based extractor for Qist (stdlib only). Returns, per term, a list of candidate values.
Numbers are floats; zero-wording ("no interest", "بدون فائدة", "0%") becomes 0.0; shariah_claim -> [1.0]."""
import re

AR = str.maketrans("٠١٢٣٤٥٦٧٨٩٫٪", "0123456789.%")
NUM = r"\d[\d,]*(?:\.\d+)?"
CUR = r"(?:SAR|SR|S\.R\.?|ريال(?:\s+سعودي)?|ر\.?\s?س|⃁)"
MONEY = re.compile(rf"(?:{CUR}\s*({NUM}))|(?:({NUM})\s*{CUR})", re.I)
PCT = re.compile(rf"(?:({NUM})\s*%)|(?:%\s*({NUM}))")
UNIT = r"(?:months?|payments?|installments?|instalments?|أشهر|اشهر|شهر[اًا]?|دفعات|دفعة|أقساط|قسط)"
INT = r"\d+(?:\.\d+)?"
SEP = r"(?:\s*(?:,|،|و|&|or|and|او|أو|\|)\s*)"
LIST = rf"({INT}(?:{SEP}{INT})*)\s*(?:\-?\s*(?:[A-Za-z\u0600-\u06FF]+\s+){{0,2}}{UNIT})"
RANGE = rf"({INT})\s*(?:to|-|–|الى|إلى|حتى|until)\s*({INT})\s*{UNIT}"
YEARS = rf"({INT})\s*(?:years?|سنوات|سنة|سنين)"

KW = {
 "profit_rate": r"interest|profit|mark-?up|margin|rate|monthly fees?|tawarr?ouq|فائدة|فوائد|هامش|ربح|نسبة|معدل",
 "admin_fee":   r"administrative|admin|processing|transaction fee|setup|set-up|establishment|إدارية|تأسيس|مصاريف|رسوم إجراء|رسوم المعاملة",
 "late_fee":    r"late|delay|overdue|default|تأخير|تأخر|عدم السداد|التأخر",
}
ZERO = re.compile(r"no (?:interest|profit|monthly fees?|hidden)|interest[- ]free|0%\s*(?:interest|installment|profit)|"
                  r"(?:بدون|دون|لا)\s+(?:فائدة|فوائد|هامش|رسوم|أرباح|ربح)|بدون رسوم شهري|بدون هامش", re.I)
SHARIA = re.compile(r"shari['’`]?ah|sharia|shariah|شريعة|الشرعية|شرعي|الشرعي", re.I)

def _f(s): return float(s.replace(",", ""))

def _nums(m): return _f(next(g for g in m.groups() if g))

def extract(text):
    t = text.translate(AR)
    out = {k: [] for k in ["cash_price","n_installments","installment_amount","admin_fee","late_fee","profit_rate","shariah_claim"]}
    # n_installments
    def add_n(v):
        if 1 <= v <= 120 and v not in out["n_installments"]: out["n_installments"].append(v)
    for m in re.finditer(LIST, t, re.I):
        for n in re.findall(INT, m.group(1)): add_n(_f(n))
    for m in re.finditer(r"(?:من|from)?\s*" + RANGE, t, re.I):
        add_n(_f(m.group(1))); add_n(_f(m.group(2)))
    for m in re.finditer(YEARS, t, re.I): add_n(_f(m.group(1)) * 12)
    for m in re.finditer(rf"(?:split|divide|pay)\w*\s+(?:it\s+)?(?:in|into)\s+({NUM})\b", t, re.I):
        v = _f(m.group(1))
        if 1 <= v <= 60 and v not in out["n_installments"]: out["n_installments"].append(v)
    # fees and rates: look for a keyword within a window before/after the figure
    def near(m, kw, w=70):
        s = max(0, m.start()-w); e = min(len(t), m.end()+w)
        return re.search(KW[kw], t[s:e], re.I) is not None
    for m in PCT.finditer(t):
        v = _nums(m)
        if near(m, "late_fee", 50): out["late_fee"].append(v)
        elif near(m, "admin_fee", 50): out["admin_fee"].append(v)
        elif near(m, "profit_rate"): out["profit_rate"].append(v)
    FEEW = r"fees?|charges?|رسوم|مصاريف|مصروفات"
    for m in MONEY.finditer(t):
        v = _nums(m)
        w = t[max(0, m.start()-45):min(len(t), m.end()+25)]
        if near(m, "late_fee", 50): out["late_fee"].append(v)
        elif near(m, "admin_fee", 50) or (re.search(FEEW, w, re.I) and not re.search(r"minimum|maximum|limit|الحد", w, re.I)):
            out["admin_fee"].append(v)
    if re.search(r"no late (?:payment )?fees?|late (?:payment )?fees?\W{0,10}(?:0|none|nil|free)|(?:بدون|دون|لا)\s+رسوم\s+(?:التأخير|تأخير|التأخر)", t, re.I):
        out["late_fee"].append(0.0)
    for m in PCT.finditer(t):
        if _nums(m) == 0:
            w = t[max(0, m.start()-25):min(len(t), m.end()+25)]
            if not re.search(r"down ?payment|admin|fee|رسوم|دفعة|مقدم|إدارية", w, re.I): out["profit_rate"].append(0.0)
    if ZERO.search(t): out["profit_rate"].append(0.0)
    if re.search(r"(?:admin\w*|processing|إدارية|تأسيس)\s*(?:fees?|رسوم)?\W{0,6}0\s*%|(?:رسوم إدارية|رسوم تأسيس)\s*0", t, re.I):
        out["admin_fee"].append(0.0)
    if re.search(r"(?:no|without|بدون)\s+(?:admin\w*|processing|setup|إدارية|تأسيس)\s*(?:fees?|رسوم)?", t, re.I):
        out["admin_fee"].append(0.0)
    # amounts
    for m in re.finditer(rf"(?:illustrative example|for an? |example)[^.\n]{{0,40}}?(?:{CUR}\s*({NUM})|({NUM})\s*{CUR})|"
                         rf"(?:transaction amount|purchase (?:price|amount)|cash price|price|سعر|قيمة الشراء|مبلغ العملية)\W{{0,12}}(?:{CUR}\s*)?({NUM})", t, re.I):
        out["cash_price"].append(_f(next(g for g in m.groups() if g)))
    for m in re.finditer(rf"(?:monthly )?(?:installment|instalment|القسط الشهري|قسط)(?: amount)?\W{{0,12}}(?:{CUR}\s*)?({NUM})", t, re.I):
        v = _f(m.group(1))
        if v not in (3,6,9,12,24,36): out["installment_amount"].append(v)
    for m in re.finditer(rf"(?:starts? from|starting from|تبدأ من|يبدأ من)\s*({NUM})\s*{CUR}", t, re.I):
        out["installment_amount"].append(_f(m.group(1)))
    for m in re.finditer(rf"installment amount[^\n]*\n\s*({NUM})", t, re.I): out["installment_amount"].append(_f(m.group(1)))
    for m in re.finditer(rf"total with[^\n]*\n\s*({NUM})", t, re.I): out["cash_price"].append(_f(m.group(1)))
    for m in re.finditer(rf"(?:purchase transaction of|purchase of|a purchase)\s*{CUR}\s*({NUM})", t, re.I): out["cash_price"].append(_f(m.group(1)))
    if SHARIA.search(t): out["shariah_claim"].append(1.0)
    return {k: sorted(set(v)) for k, v in out.items()}
