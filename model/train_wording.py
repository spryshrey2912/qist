"""Train the 'misleading wording' classifier ONCE and save it as model/wording_model.json.
Run from the project folder:  python model/train_wording.py
The app (app/ml.py) loads that file and scores offers with plain Python. Run this again whenever data/offers.csv changes
(tests/test_app.py fails if the saved model no longer matches the data file)."""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..")
sys.path[:0] = [os.path.join(ROOT, "app"), HERE]
import ml

df = ml.training_rows()
pipe = ml.make().fit(df["text"], df["misleading"].astype(int), **ml.fit_args(df))
tfidf = pipe.steps[0][1].transformer_list[0][1]; lr = pipe.steps[-1][1]
V = len(tfidf.vocabulary_); coef = lr.coef_[0]
assert coef.shape[0] == V + 5
out = {
    "about": "TF-IDF char_wb 2-4 (sublinear tf, L2) + 3 rule features + 2 fee-wording features -> logistic regression. Trained by model/train_wording.py.",
    "n": int(len(df)), "n_real": int((df.source == "real").sum()),
    "data_sha256": hashlib.sha256(open(ml.DATA, "rb").read()).hexdigest(),
    "vocab": {g: int(i) for g, i in tfidf.vocabulary_.items()},
    "idf": [round(float(x), 8) for x in tfidf.idf_],
    "coef": [round(float(x), 8) for x in coef[:V]],
    "coef_rules": [round(float(x), 8) for x in coef[V:V + 3]],
    "coef_lex": [round(float(x), 8) for x in coef[V + 3:]],
    "intercept": round(float(lr.intercept_[0]), 8),
}
path = os.path.join(HERE, "wording_model.json")
json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("saved", path, os.path.getsize(path) // 1024, "KB;", V, "n-grams;", out["n"], "training offers")
