---
title: Qist API
emoji: 💳
colorFrom: yellow
colorTo: red
sdk: docker
app_port: 7860
---

# Qist | قسط

Paste or photograph an instalment / BNPL / card-financing offer (Arabic or English). Qist extracts the terms,
works out the **true cost in SAR**, flags **misleading wording** (e.g. "0%" next to a fee) and shows the **SAMA reference**.

How it works (all explainable, no black box in the app):
1. `model/rules.py`: rule-based extractor (instalments, amounts, fees, rates, Shariah claim), Arabic + English.
2. `app/engine.py`: picks defaults, works out the instalment from the rate if needed, wording flags, SAMA text.
3. `app/cost.py`: exact maths (total paid, extra cost, effective annual rate).
4. `app/ui.py`: the look (glass cards, animated background, inline SVG art, gauge and timeline; no external images). `.streamlit/config.toml` sets the dark theme.
5. `app/app.py`: Streamlit screen. Every extracted field can be corrected by the user.

## Run on your computer
```
pip install -r requirements.txt
streamlit run app/app.py
```
Photo upload needs Tesseract with Arabic + English:
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki (tick Arabic), then set
  `setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"` and reopen the terminal.
- Without Tesseract the app still works by pasting text.

## Tests
```
python tests/test_cost.py
python tests/test_app.py
python model/eval_rules.py            # rules score on the labelled real offers
python model/eval_rules.py data/new_real_051_070.csv -v   # rows the rules never saw (68%)
```

## Deploy (Streamlit Community Cloud)
1. Push this folder to a GitHub repo (the model weights are git-ignored; the app does not need them).
2. share.streamlit.io -> New app -> main file `app/app.py`.
3. `packages.txt` installs Tesseract + Arabic for photo upload; `requirements.txt` is the minimal app set.

## Live site (GitHub Pages, no server)
`index.html` is the public app. It loads Python in the browser (Pyodide), copies in `app/engine.py`, `app/cost.py`,
`app/analyze.py`, `app/ml.py`, `model/rules.py` and the saved wording model `model/wording_model.json`, and reads
photos with Tesseract.js (Arabic + English). Nothing is uploaded or stored. Only plain Python is needed (no numpy, pandas or scikit-learn in the browser).

## Honest limits
- Rules found 68% of terms on 20 real offers they had never seen (`data/new_real_051_070.csv`), and 82% on all labelled real offers; weakest on amounts inside tables.
- The true-cost panel needs a price and a number of instalments; many real T&C pages give neither, so the panel stays empty for them.
- It cannot read balloon / final-payment car leases correctly yet.
- The term extractor is rule-based. `model/train_extractor.py` (xlm-roberta-base) is written but has not been trained, so no score is claimed for it.
- Not financial advice. Nothing is stored.

## Look
'Kinetic Orange': flat orange page (no gradients), black panels, white text, sharp corners, 2px borders.
Fonts: Archivo Black (headline, marquee, big titles), Space Mono (small labels), Inter (text), Tajawal (Arabic), and **Ronzino** (functional parts: step titles,
the real-cost numbers, gauge, payment tiles, verdict labels, number boxes). Ronzino is embedded from `app/fonts/` (SIL OFL licence included);
the other fonts load from Google Fonts, so the first load needs internet. To add a font, drop `<family>-<weight>.woff2` into `app/fonts/`.
All styling is in `app/ui.py` and `.streamlit/config.toml`.

## Machine learning
- `app/ml.py`: the wording model. TF-IDF character n-grams plus 3 features from the extractor, into a logistic regression. Trained ahead of time by `python model/train_wording.py` on `data/offers.csv` (292 labelled offers: 112 real, 180 synthetic; each real row weighted 10x) and saved as `model/wording_model.json` (vocabulary, IDF weights, coefficients). The app loads that file and scores with plain Python; the scores match scikit-learn to 1e-8 on all 292 offers. `tests/test_app.py` fails if the saved file no longer matches `data/offers.csv`, so re-run the training script after any label change. If the file is missing, `ml.py` falls back to training from `data/offers.csv` (needs scikit-learn and pandas). The 6 real rows behind the app's sample buttons (`demo=1`) are left out of training, so the scores you see on the samples are real predictions.
- Label rule (written down so labels stay consistent): **misleading = the offer promises 0% / free / no profit / no fees, and the same offer also states a fee tied to getting that price.** Fees that are not the price of the instalment (annual card fee, cash-on-delivery, late-payment fee) do not count, and neither do fees that belong only to other plans in the same offer. If no fee is written in the text, the label is 0, because the evidence must be in the text.
- Label check (27 Nov): every real label was compared with the rule. 7 did not follow it and were corrected: `real_012` (Tasaheal: "No Monthly Fees" plan with a SAR 49 processing fee) is now 1; `real_001`, `real_057`, `real_063`, `real_066`, `real_067`, `real_068` (claims such as "no hidden fees" with no fee written in the offer) are now 0.
- `model/eval_wording.py`: honest score. Only real offers are scored. **Grouped** 5-fold cross-validation (the same offer in Arabic and English, or the same bank template, always stays on one side of the split), 5 splits averaged. Result on 112 real offers (31 misleading; "always fine" scores 72%):

| model | accuracy | precision | recall | F1 | AUC | Brier (lower is better) |
|---|---|---|---|---|---|---|
| **text only** (learns from wording alone) | **81%** | **73%** | **52%** | **60%** | **0.86** | **0.14** |
| rule flags only (circular, labels come from these rules) | 99% | 100% | 97% | 98% | 0.97 | 0.05 |
| hybrid (the app; also circular) | 99% | 100% | 97% | 98% | 0.99 | 0.01 |

  What this means: the labels follow a written rule and the rule flags check that same rule, so the 100% rows are true **by construction**, not a sign of a perfect model, and the hybrid mostly copies the rules. The honest machine-learning number is the **text-only** row: from examples alone, with no rules, the model separates misleading from fair wording with AUC 0.89 on offers from groups it never saw. The rules were also refined after looking at these offers; before refinement they scored 80% accuracy / 57% precision / 100% recall on 30 offers they had never seen (6 false alarms, now fixed and covered by `tests/`).
- Final answer shown to the user: a fee next to a 0%/free promise is a **warning** (it is written in the text; the model score is shown as support). No fee but a model score of 50% or more is **watch**. Otherwise **clear**.
- Data sources: 70 real offers collected by the builder plus 30 taken from bank and merchant pages (Riyad Bank, BSF, SAIB, ANB, Alinma, Al Rajhi, IKEA, Tefal, Jarir, ...), and 180 synthetic offers generated with AI and kept or deleted by hand. `data/unreviewed/` holds a further 180 web offers whose labels were suggested by AI and have **not** been reviewed; they are not used anywhere.
- `data/offers.csv` is the master data file. `data/real_offers_labelling_sheet.csv` is an older copy (rows 101-120 are empty), so `data/combine.py` now refuses to overwrite `offers.csv` unless run with `--force`.
- `model/train_extractor.py`: xlm-roberta-base term extractor (needs a GPU, e.g. Colab). Not trained; the app extracts terms with rules (`model/rules.py`), and the cost maths is plain code on purpose.

## Web API (for the Lovable website)
`api/main.py` (FastAPI) wraps the same engine: `POST /analyze`, `POST /analyze-photo`, `POST /cost`, `GET /health`. It runs from the `Dockerfile` (Hugging Face Spaces, Docker SDK). The front-end prompt and sample data are in `lovable/`.
