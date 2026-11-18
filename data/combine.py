"""Merge your labelled real offers with the kept synthetic ones into data/offers.csv.
Real rows need `spans` filled; if you only filled the 7 term columns, this script finds the spans for you."""
import csv, json
def load(p): return list(csv.DictReader(open(p, encoding="utf-8-sig")))
T = ["cash_price","n_installments","installment_amount","admin_fee","late_fee","profit_rate","shariah_claim"]
rows = load("data/synthetic_offers.csv")
for r in load("data/real_offers_labelling_sheet.csv"):
    if not r["text"].strip(): continue            # skip rows you haven't done yet
    if not r["spans"]:
        sp = []
        for t in T:
            v = r[t].strip()
            i = r["text"].find(v) if v else -1
            if i >= 0: sp.append([i, i + len(v), t])
        r["spans"] = json.dumps(sp, ensure_ascii=False)
    rows.append(r)
with open("data/offers.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "rows in data/offers.csv")
