"""Honest score for the wording classifier.
 * Only REAL offers are scored (the synthetic ones are easy and look different).
 * Grouped CV: near-identical offers (same offer in Arabic and English, or the same bank template) share a `group`
   and always sit on the same side of a split, so the model is never tested on a twin of what it trained on.
 * 5 folds x 5 different splits, averaged, so one lucky split cannot flatter the score.
 * Three models are compared: text only, the rule flags only, and the hybrid that the app uses.
Run:  python model/eval_wording.py      (writes data/eval_wording.json)"""
import sys, json, warnings, numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import FunctionTransformer
sys.path.insert(0, "app"); import ml

MODELS = {
    "text only (TF-IDF + LR)": lambda: make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True), LogisticRegression(max_iter=2000, class_weight="balanced")),
    "rule flags only (3 numbers)": lambda: make_pipeline(FunctionTransformer(ml.rule_features), LogisticRegression(max_iter=2000, class_weight="balanced")),
    "hybrid = text + rule flags (the app)": ml.make,
}

def score(y, p):
    pr = p >= .5; tp = (pr & (y == 1)).sum(); fp = (pr & (y == 0)).sum(); fn = (~pr & (y == 1)).sum()
    pre, rec = tp / max(1, tp + fp), tp / max(1, tp + fn)
    return [(pr == y).mean(), pre, rec, 2 * pre * rec / max(1e-9, pre + rec), roc_auc_score(y, p), brier_score_loss(y, p)]

if __name__ == "__main__":
    df = pd.read_csv("data/offers.csv"); df["misleading"] = df["misleading"].astype(int)
    real, syn = df[df.source == "real"].reset_index(drop=True), df[df.source != "real"]
    y = real.misleading.values
    print(f"real offers {len(real)} ({y.sum()} misleading) in {real.group.nunique()} groups; 'always fine' baseline accuracy {1 - y.mean():.0%}\n")
    print(f"{'model':40s} accuracy precision recall   F1    AUC  Brier(lower=better)")
    out = {"n_real": int(len(real)), "n_misleading": int(y.sum()), "baseline_accuracy": float(1 - y.mean()), "models": {}}
    for name, mk in MODELS.items():
        rows = []
        for seed in range(5):
            P = np.zeros(len(real))
            for tr, te in StratifiedGroupKFold(5, shuffle=True, random_state=seed).split(real, y, real.group):
                d = pd.concat([syn, real.iloc[tr]])
                m = mk(); step = m.steps[-1][0]
                m.fit(d.text, d.misleading, **{step + "__sample_weight": ml.fit_args(d)["logisticregression__sample_weight"]})
                P[te] = m.predict_proba(real.text.iloc[te])[:, 1]
            rows.append(score(y, P))
        r = np.mean(rows, 0); out["models"][name] = dict(zip(["accuracy", "precision", "recall", "f1", "auc", "brier"], map(float, r)))
        print(f"{name:40s} {r[0]:8.0%} {r[1]:9.0%} {r[2]:6.0%} {r[3]:5.0%} {r[4]:6.2f} {r[5]:8.2f}")
    json.dump(out, open("data/eval_wording.json", "w"), indent=1)
