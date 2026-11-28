"""Split offers.csv into train / test without leakage.
Rule 1: all rows from one provider stay on the same side (near-identical pages must not straddle the split).
Rule 2: the score that matters is on REAL offers only; synthetic rows are train-only, plus a small synthetic check set.
Run: python data/split.py   ->  data/train.csv, data/test_real.csv, data/test_synth.csv"""
import pandas as pd, random
G = {"tamara":[1,2,3,4,63,64,68],"extra":[5,9],"jarir":[6,7,18,19],"ahlia":[8,10],"rajhi":[11,12,20,49,50,52,54,59,62],
     "bsf":[13,35,36,41,42,43,44,45],"ikea":[14,39],"stc_aljazira":[15],"sab":[16,17,23,51,53,55,56],"samsung":[21],
     "toyota":[22],"riyad":[24,25,26,31,32,33,34,40,46,47,48],"enbd":[27],"alinma":[28,57],"anb":[29,37],
     "amex":[30],"saib":[38],"albilad":[58,70],"fab":[60],"emkan":[61],"naghi":[65],"alj_kia":[66],"tabby":[67],"redsea":[69]}
grp = {f"real_{i:03d}": g for g, ids in G.items() for i in ids}
df = pd.read_csv("data/offers.csv")
real = df[df.source == "real"].copy(); syn = df[df.source != "real"].copy()
real["group"] = real.id.map(grp)
assert real.group.notna().all(), real[real.group.isna()].id.tolist()
random.seed(7)
groups = sorted(real.group.unique()); random.shuffle(groups)
test_groups, n = [], 0
for g in groups:                       # fill test with whole providers until ~30% of real rows
    if n >= 0.3 * len(real): break
    test_groups.append(g); n += (real.group == g).sum()
test_real = real[real.group.isin(test_groups)].drop(columns="group")
train_real = real[~real.group.isin(test_groups)].drop(columns="group")
syn = syn.sample(frac=1, random_state=7)
test_synth, train_syn = syn[:18], syn[18:]
train = pd.concat([train_real, train_syn]).sample(frac=1, random_state=7)
train.to_csv("data/train.csv", index=False, encoding="utf-8-sig")
test_real.to_csv("data/test_real.csv", index=False, encoding="utf-8-sig")
test_synth.to_csv("data/test_synth.csv", index=False, encoding="utf-8-sig")
print("test providers:", test_groups)
print(f"train {len(train)} ({len(train_real)} real) | test_real {len(test_real)} | test_synth {len(test_synth)}")
