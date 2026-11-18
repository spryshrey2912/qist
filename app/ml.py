"""The machine-learning part: a small text classifier (TF-IDF character n-grams + logistic regression, plus three
features from the rule extractor) that scores how likely an offer's wording is misleading
(a 0% / free / no-profit promise with a fee tied to it).
Trained at start-up from data/offers.csv (280 labelled offers, 100 real): no saved model file, so nothing can go stale.
The sample offers in the app (rows with demo=1) are left out of training, so their scores are real predictions."""
import functools, os
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union
from sklearn.preprocessing import FunctionTransformer
import engine

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "offers.csv")

def rule_features(texts):
    """Three numbers per offer from the extractor: 0%-but-fee flag, 0%-for-some-plans flag, a fee was found."""
    out = []
    for t in texts:
        c = engine.candidates(t); codes = [k for k, _ in engine.flags(t, c)]
        out.append([3.0 * ("zero_but_fee" in codes), 3.0 * ("zero_for_some_plans" in codes), 3.0 * bool(engine.fee_amounts(t, c))])
    return out

def make():
    """Text n-grams + the three extractor features, one logistic regression on top (the model learns how much to trust each)."""
    feats = make_union(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True), FunctionTransformer(rule_features))
    return make_pipeline(feats, LogisticRegression(max_iter=2000, class_weight="balanced"))

def fit_args(df):
    """Real offers are rare and the synthetic ones are easier, so each real row counts 10x (tested: 3x to 100x gives the same scores)."""
    return {"logisticregression__sample_weight": (df["source"] == "real").map({True: 10.0, False: 1.0}).values}

@functools.lru_cache(maxsize=1)
def model():
    df = pd.read_csv(DATA)
    df = df[df.get("demo", 0) != 1]
    return make().fit(df["text"], df["misleading"].astype(int), **fit_args(df))

def p_misleading(text):
    """Probability 0..1 that the wording is misleading; None if the model cannot run."""
    try: return float(model().predict_proba([text])[0][1])
    except Exception: return None

@functools.lru_cache(maxsize=1)
def info():
    """How many labelled offers the model was trained on (shown in the app, so the text never goes stale)."""
    df = pd.read_csv(DATA); df = df[df.get("demo", 0) != 1]
    return {"n": int(len(df)), "n_real": int((df.source == "real").sum())}
