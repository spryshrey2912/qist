"""Small 'misleading wording' classifier (TF-IDF + logistic regression). Runs on a laptop.
Label: misleading=1 when the offer says 0% profit but has a buried admin fee."""
import pandas as pd, joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report

df = pd.read_csv("data/offers.csv")
X_tr, X_te, y_tr, y_te = train_test_split(df["text"], df["misleading"].astype(int), test_size=0.2, random_state=42)
clf = make_pipeline(TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)), LogisticRegression(max_iter=1000))
clf.fit(X_tr, y_tr)
print(classification_report(y_te, clf.predict(X_te)))
joblib.dump(clf, "model/wording.joblib")
