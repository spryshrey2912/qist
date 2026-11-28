"""The machine-learning part: a small text classifier (TF-IDF character n-grams + logistic regression, plus three
features from the rule extractor) that scores how likely an offer's wording is misleading
(a 0% / free / no-profit promise with a fee tied to it).

The model is TRAINED AHEAD OF TIME by model/train_wording.py and saved as model/wording_model.json (vocabulary, IDF
weights, coefficients). The page loads that file and scores offers with plain Python: no training in the browser and
no scikit-learn needed to run the app. If the file is missing, the old path still works: train from data/offers.csv
at start-up (needs scikit-learn and pandas). The sample offers in the app (rows with demo=1) are left out of training,
so their scores are real predictions."""
import functools, json, math, os, re
import engine

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "offers.csv")
SAVED = os.path.join(HERE, "..", "model", "wording_model.json")
_WS = re.compile(r"\s\s+")

def rule_features(texts):
    """Three numbers per offer from the extractor: 0%-but-fee flag, 0%-for-some-plans flag, a fee was found."""
    out = []
    for t in texts:
        c = engine.candidates(t); codes = [k for k, _ in engine.flags(t, c)]
        out.append([3.0 * ("zero_but_fee" in codes), 3.0 * ("zero_for_some_plans" in codes), 3.0 * bool(engine.fee_amounts(t, c))])
    return out

def make():
    """Training recipe (used by model/train_wording.py and the fallback): text n-grams + the three extractor features,
    one logistic regression on top (the model learns how much to trust each)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline, make_union
    from sklearn.preprocessing import FunctionTransformer
    feats = make_union(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True), FunctionTransformer(rule_features))
    return make_pipeline(feats, LogisticRegression(max_iter=2000, class_weight="balanced"))

def fit_args(df):
    """Real offers are rare and the synthetic ones are easier, so each real row counts 10x (tested: 3x to 100x gives the same scores)."""
    return {"logisticregression__sample_weight": (df["source"] == "real").map({True: 10.0, False: 1.0}).values}

def training_rows():
    import pandas as pd
    df = pd.read_csv(DATA)
    return df[df.get("demo", 0) != 1]

def _ngrams(text):
    """The same character n-grams scikit-learn's TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4)) makes."""
    out = []
    for w in _WS.sub(" ", text.lower()).split():
        w = " " + w + " "; n_chars = len(w)
        for n in range(2, 5):
            off = 0; out.append(w[off:off + n])
            while off + n < n_chars:
                off += 1; out.append(w[off:off + n])
            if off == 0: break
    return out

@functools.lru_cache(maxsize=1)
def saved():
    """The saved model, or None if model/wording_model.json is missing or unreadable."""
    try:
        with open(SAVED, encoding="utf-8") as f: return json.load(f)
    except Exception: return None

def _score_saved(m, text):
    tf = {}
    for g in _ngrams(text):
        if g in m["vocab"]: tf[g] = tf.get(g, 0) + 1
    w = {g: (1.0 + math.log(c)) * m["idf"][m["vocab"][g]] for g, c in tf.items()}      # sublinear tf x idf
    norm = math.sqrt(sum(v * v for v in w.values())) or 1.0
    z = m["intercept"] + sum(m["coef"][m["vocab"][g]] * v / norm for g, v in w.items())
    z += sum(c * x for c, x in zip(m["coef_rules"], rule_features([text])[0]))
    return 1.0 / (1.0 + math.exp(-z))

@functools.lru_cache(maxsize=1)
def model():
    """Fallback: train in the process from data/offers.csv (used only when the saved model file is missing)."""
    df = training_rows()
    return make().fit(df["text"], df["misleading"].astype(int), **fit_args(df))

def p_misleading(text):
    """Probability 0..1 that the wording is misleading; None if the model cannot run."""
    try:
        m = saved()
        if m: return _score_saved(m, text)
        return float(model().predict_proba([text])[0][1])
    except Exception: return None

@functools.lru_cache(maxsize=1)
def info():
    """How many labelled offers the model was trained on (shown in the app, so the text never goes stale)."""
    m = saved()
    if m: return {"n": m["n"], "n_real": m["n_real"]}
    df = training_rows()
    return {"n": int(len(df)), "n_real": int((df.source == "real").sum())}
