"""Generates synthetic offers with exact character spans. Run: python data/make_synthetic.py
Every row is marked source=synthetic. READ AND KEEP/DELETE each row by hand (Sprint 1 Wed)."""
import csv, json, random
random.seed(7)
TERMS = ["cash_price", "n_installments", "installment_amount", "admin_fee",
         "late_fee", "profit_rate", "shariah_claim"]
BRANDS_EN = ["PayLater", "SplitIt", "EasyPay", "StoreCard Plan", "CarFlex", "HomeInstall"]
BRANDS_AR = ["قسّطها", "ادفع لاحقاً", "تمويل سهل", "بطاقة المتجر", "خطة التقسيط", "قسط الأسرة"]

def build(lang):
    price = random.choice(range(300, 15001, 50))
    n = random.choice([3, 4, 6, 12, 24])
    hidden = random.random() < 0.45          # "0%" headline with buried fee
    fee = random.choice([19, 29, 39, 49, 59, 99]) if (hidden or random.random() < 0.4) else 0
    late = random.choice([25, 35, 45, 60, 75, 100]) if random.random() < 0.8 else 0
    rate = 0 if hidden or random.random() < 0.3 else random.choice([1.0, 1.5, 2.0, 2.5])
    total = price + fee + (price * rate / 100 * n)
    inst = round((total - fee) / n, 2)
    shar = random.random() < 0.5
    P = []  # pieces: (text, label)
    if lang == "en":
        P += [(f"{random.choice(BRANDS_EN)}: ", None), ("Total price ", None), (f"SAR {price}", "cash_price"),
              (". Split into ", None), (f"{n} installments", "n_installments"), (" of ", None),
              (f"SAR {inst}", "installment_amount"), (" per month. ", None)]
        P += [(f"{'0%' if rate == 0 else str(rate) + '% per month'} ", None)] if False else []
        P += [("Profit rate: ", None), (f"{rate}%" if rate else "0%", "profit_rate"), (". ", None)]
        if fee: P += [("Small print: a one-time admin fee of ", None), (f"SAR {fee}", "admin_fee"), (" applies. ", None)]
        if late: P += [("Late payment fee: ", None), (f"SAR {late}", "late_fee"), (". ", None)]
        if shar: P += [("This plan is ", None), ("Shariah-compliant", "shariah_claim"), (".", None)]
    else:
        P += [(f"{random.choice(BRANDS_AR)}: ", None), ("السعر النقدي ", None), (f"{price} ريال", "cash_price"),
              ("، يُقسّم على ", None), (f"{n} دفعات", "n_installments"), (" بقسط ", None),
              (f"{inst} ريال", "installment_amount"), (" شهرياً. ", None),
              ("نسبة الربح: ", None), (f"{rate}٪" if rate else "٪0", "profit_rate"), (". ", None)]
        if fee: P += [("بخط صغير: تُطبّق رسوم إدارية لمرة واحدة بقيمة ", None), (f"{fee} ريال", "admin_fee"), (". ", None)]
        if late: P += [("غرامة التأخير: ", None), (f"{late} ريال", "late_fee"), (". ", None)]
        if shar: P += [("الخطة ", None), ("متوافقة مع الشريعة", "shariah_claim"), (".", None)]
    text, spans, vals = "", [], {t: "" for t in TERMS}
    for s, lab in P:
        if lab: spans.append([len(text), len(text) + len(s), lab]); vals[lab] = s
        text += s
    mislead = int(rate == 0 and fee > 0)
    return text, spans, vals, mislead

rows = []
for i in range(180):
    lang = "ar" if i % 2 == 0 else "en"
    text, spans, vals, mis = build(lang)
    rows.append({"id": f"syn_{i:03d}", "source": "synthetic", "lang": lang, "text": text, **vals,
                 "spans": json.dumps(spans, ensure_ascii=False), "misleading": mis})
with open("data/synthetic_offers.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "rows written")
