"""Honest score for the wording classifier: 5-fold CV where ONLY real rows are scored.
Each fold trains on all synthetic rows + the other real rows, then predicts the held-out real rows."""
import sys, pandas as pd, numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
sys.path.insert(0, "app"); from ml import make, fit_args

df = pd.read_csv("data/offers.csv"); df["misleading"] = df["misleading"].astype(int)
real, syn = df[df.source == "real"].reset_index(drop=True), df[df.source == "synthetic"]
for seed in range(3):                                   # 3 different splits, averaged, so one lucky split cannot flatter the score
    pred = np.zeros(len(real), int)
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(real, real.misleading):
        d = pd.concat([syn, real.iloc[tr]])
        pred[te] = make().fit(d.text, d.misleading, **fit_args(d)).predict(real.text.iloc[te])
    p, r, f, _ = precision_recall_fscore_support(real.misleading, pred, average="binary")
    print(f"split {seed}: real rows {len(real)} ({real.misleading.sum()} misleading)  accuracy {accuracy_score(real.misleading, pred):.0%}  precision {p:.0%}  recall {r:.0%}  F1 {f:.0%}")
print(f"always-say-'fine' baseline accuracy: {1 - real.misleading.mean():.0%}")
