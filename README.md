# Qist | قسط

Paste or photograph an instalment, BNPL or card-financing offer (Arabic or English). Qist extracts the terms, works out the **true cost in SAR**, flags **misleading wording** (for example "0%" next to a fee) and shows what the SAMA rules say. It informs; it never gives financial advice.

**Live app:** https://spryshrey2912.github.io/qist/ (runs entirely in your browser; nothing is uploaded or stored).

## How it works
1. `model/rules.py`: rule-based term extractor (instalments, amounts, fees, rates), Arabic and English.
2. `app/engine.py`: picks defaults, wording flags, evidence lines and the SAMA reference text.
3. `app/cost.py`: exact maths (total paid, extra cost, effective annual rate).
4. `app/ml.py`: the wording model. TF-IDF character n-grams plus fee-wording features into a logistic regression, scored in plain Python from the saved file `model/wording_model.json`.
5. `app/analyze.py`: ties the steps together and returns one result.
6. `index.html`: the public page. It loads Python in the browser (Pyodide), copies in the files above, and reads photos with Tesseract.js (Arabic + English). Sample offers are in `content/samples.json`.

## Run the tests
```
pip install -r requirements.txt
python -m pytest tests
python model/eval_wording.py       # honest wording-model score (grouped cross-validation)
python model/eval_rules.py         # rule-engine score on the labelled real offers
```
To open the site locally, serve the folder (for example `python -m http.server`) and visit http://localhost:8000.

## Deploy
GitHub Pages serves `index.html` from the `main` branch root. There is no server.

## Honest limits
- Small dataset: 128 real Gulf offers (35 misleading). Scores are estimates and will move as data grows.
- The true-cost panel needs a price and a number of instalments; many real pages give neither, so the panel stays empty and the app says so.
- Car leases with a final balloon payment are not read correctly yet.
- OCR can misread a photo; the text box can be edited and re-checked.
- Terms are extracted by rules, not by a trained model.
- Not financial advice. Nothing is stored.

## Machine learning
- `app/ml.py`: the wording model. TF-IDF character n-grams plus 3 features from the extractor, into a logistic regression. Trained ahead of time by `python model/train_wording.py` on `data/offers.csv` (316 labelled offers: 128 real Gulf offers, 8 real offers from Egypt and Jordan (`source=real_mena`: used for training only, never scored) and 180 synthetic; each real row weighted 10x) and saved as `model/wording_model.json` (vocabulary, IDF weights, coefficients). The app loads that file and scores with plain Python; the scores match scikit-learn to 1e-8 on all 316 offers. `tests/test_app.py` fails if the saved file no longer matches `data/offers.csv`, so re-run the training script after any label change. If the file is missing, `ml.py` falls back to training from `data/offers.csv` (needs scikit-learn and pandas). The 6 real rows behind the app's sample buttons (`demo=1`) are left out of training, so the scores you see on the samples are real predictions.
- Label rule (written down so labels stay consistent): **misleading = the offer promises 0% / free / no profit / no fees, and the same offer also states a fee tied to getting that price.** Fees that are not the price of the instalment (annual card fee, cash-on-delivery, late-payment fee) do not count, and neither do fees that belong only to other plans in the same offer. If no fee is written in the text, the label is 0, because the evidence must be in the text.
- Label check (27 Nov): every real label was compared with the rule. 7 did not follow it and were corrected: `real_012` (Tasaheal: "No Monthly Fees" plan with a SAR 49 processing fee) is now 1; `real_001`, `real_057`, `real_063`, `real_066`, `real_067`, `real_068` (claims such as "no hidden fees" with no fee written in the offer) are now 0.
- `model/eval_wording.py`: honest score. Only real offers are scored. **Grouped** 5-fold cross-validation (the same offer in Arabic and English, or the same bank template, always stays on one side of the split), 5 splits averaged. Result on 128 real Gulf offers (35 misleading; "always fine" scores 73%):

| model | accuracy | precision | recall | F1 | AUC | Brier (lower is better) |
|---|---|---|---|---|---|---|
| text only (character n-grams alone) | 80% | 62% | 74% | 68% | 0.84 | 0.14 |
| **text + fee-wording features** (no rule engine; in the app) | **82%** | **67%** | **68%** | **68%** | **0.86** | **0.13** |
| rule flags only (circular, labels come from these rules) | 97% | 100% | 89% | 94% | 0.91 | 0.07 |
| hybrid (the app; also circular) | 94% | 87% | 91% | 89% | 0.95 | 0.04 |

The alert level is 0.40 (`THRESHOLD` in `app/ml.py`), chosen by cross-validation as the point where precision and recall are about equal. Most of the difference between the two text rows comes from the alert level, not from the fee-wording features. With the extra offers the two text rows are about equal (the fee-wording features no longer give a clear gain). Known rule misses: the Kia lease (`real_066`), meem As'hal (`real_113`, fee written as a question and answer), NBK FlexiPay (`real_115`, "KD 5 one-time fee") and ADCB school fees (`real_124`, fee inside a table).

  What this means: the labels follow a written rule and the rule flags check that same rule, so the 100% rows are true **by construction**, not a sign of a perfect model, and the hybrid mostly copies the rules. The honest machine-learning number is the **text + fee-wording features** row: with no rule engine, the model separates misleading from fair wording with AUC 0.86 on offers from groups it never saw. The rules were also refined after looking at these offers; before refinement they scored 80% accuracy / 57% precision / 100% recall on 30 offers they had never seen (6 false alarms, now fixed and covered by `tests/`).
- Final answer shown to the user: a fee next to a 0%/free promise is a **warning** (it is written in the text; the model score is shown as support). No fee but a model score of 50% or more is **watch**. Otherwise **clear**.
- Data sources: 128 real Gulf offers (verbatim text from bank, app and merchant pages, in Arabic and English), 8 real offers from Egypt and Jordan (training only) and 180 synthetic offers generated with AI and kept or deleted by hand.
- `data/offers.csv` is the master data file.
