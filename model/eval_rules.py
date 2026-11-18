"""Score rules.py by VALUE on real rows: a gold term is correct if every number in its span is among the predicted values."""
import sys, json, re, pandas as pd
sys.path.insert(0, "model"); from rules import extract, AR, NUM, ZERO, SHARIA
TERMS = ["cash_price","n_installments","installment_amount","admin_fee","late_fee","profit_rate","shariah_claim"]
def gold_vals(term, s):
    s = s.translate(AR)
    if term == "shariah_claim": return {1.0}
    v = {float(x.replace(",", "")) for x in re.findall(NUM, s)}
    if re.search(r"years?|سنوات|سنة", s, re.I): v = {x * 12 for x in v}      # gold in years -> months
    if not v and (ZERO.search(s) or re.search(r"free|بدون|دون|zero|\bno ", s, re.I)): v = {0.0}
    return v
def run(path, name):
    d = pd.read_csv(path); d = d[d.source == "real"]
    stat = {t: [0, 0] for t in TERMS}; extras = {t: 0 for t in TERMS}; miss = []
    for _, r in d.iterrows():
        pred = extract(r.text); gold = {}
        for s, e, t in json.loads(r.spans): gold.setdefault(t, set()).update(gold_vals(t, r.text[s:e]))
        gold = {t: g for t, g in gold.items() if g}      # skip terms whose gold has no checkable value
        for t in TERMS:
            p = set(pred[t])
            if t in gold:
                stat[t][1] += 1
                if gold[t] <= p: stat[t][0] += 1
                else: miss.append((r.id, t, sorted(gold[t]), sorted(p)))
            extras[t] += len(p - gold.get(t, set()))
    tot = sum(a for a, b in stat.values()); n = sum(b for a, b in stat.values())
    print(f"\n== {name}: {len(d)} rows ==")
    for t in TERMS: print(f"{t:20s} {stat[t][0]:3d}/{stat[t][1]:3d}   extra values: {extras[t]}")
    print(f"ALL terms found: {tot}/{n} = {tot/max(n,1):.0%}")
    return miss
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].endswith(".csv"):
        m = run(sys.argv[1], sys.argv[1])
        sys.argv = [a for a in sys.argv if not a.endswith(".csv")]
    else:
        run("data/train.csv", "TRAIN real rows (rules were tuned on these)")
        m = run("data/test_real.csv", "TEST real rows (rules author saw these)")
    if "-v" in sys.argv:
        for x in m: print(x)
