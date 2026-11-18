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

## Training (optional, not used by the app)
`requirements-train.txt`, `data/split.py`, `model/train_extractor.py` (Colab GPU).

## Honest limits
- Rules found 68% of terms on 20 offers they had never seen; weakest on amounts inside tables.
- The wording flag agrees with the labels on 92% of the 100 real offers (tuned on them, so optimistic); on 30 offers it had never seen it scored 80% before the fixes.
- It cannot read balloon / final-payment car leases correctly yet.
- Not financial advice. Nothing is stored.


## Look
'Kinetic Orange': flat orange page (no gradients), black panels, white text, sharp corners, 2px borders.
Fonts: Archivo Black (headline, marquee, big titles), Space Mono (small labels), Inter (text), Tajawal (Arabic), and **Ronzino** (functional parts: step titles,
the real-cost numbers, gauge, payment tiles, verdict labels, number boxes). Ronzino is embedded from `app/fonts/` (SIL OFL licence included);
the other fonts load from Google Fonts, so the first load needs internet. To add a font, drop `<family>-<weight>.woff2` into `app/fonts/`.
All styling is in `app/ui.py` and `.streamlit/config.toml`.

## Machine learning
- `app/ml.py`: the wording model. TF-IDF character n-grams plus 3 features from the extractor, into a logistic regression. Trained at app start-up from `data/offers.csv` (280 labelled offers: 100 real, 180 synthetic; each real row weighted 10x), so there is no model file to go stale. The 6 real rows behind the app's sample buttons (`demo=1`) are left out of training, so the scores you see on the samples are real predictions.
- Label rule (written down so labels stay consistent): **misleading = the offer promises 0% / free / no profit, and the same offer also charges a fee tied to getting that price.** Fees that are not the price of the instalment (annual card fee, cash-on-delivery, late-payment fee) do not count.
- `model/eval_wording.py`: honest score. Only real offers are scored. **Grouped** 5-fold cross-validation (the same offer in Arabic and English, or the same bank template, always stays on one side of the split), 5 splits averaged. Result on 100 real offers (29 misleading; "always fine" scores 71%):

| model | accuracy | precision | recall | F1 | AUC | Brier (lower is better) |
|---|---|---|---|---|---|---|
| text only | 78% | 70% | 45% | 55% | 0.78 | 0.16 |
| rule flags only | 92% | 92% | 79% | 85% | 0.85 | 0.12 |
| **hybrid (the app)** | **92%** | **92%** | **79%** | **85%** | **0.90** | **0.07** |

  What this means: the text alone barely learns the idea; the hybrid matches the rules on yes/no but ranks offers better (AUC 0.90) and gives more honest percentages (Brier 0.07 vs 0.12). **The rules were refined after looking at these offers, so the 92% is optimistic.** The unbiased check: before refinement, the rules scored 80% accuracy / 57% precision / 100% recall on 30 offers they had never seen (6 false alarms, now fixed; those fixes are covered by `tests/`).
- What the model cannot do: 5 of the 29 "misleading" labels rest on claims like "no hidden fees" with no fee visible in the text (Tamara, Tabby, a Kia lease). The text does not contain the evidence, so no model can learn them (recall ceiling about 83% on this data). They are kept in the data, not removed to look better.
- Final answer shown to the user: a fee next to a 0%/free promise is a **warning** (it is written in the text; the model score is shown as support). No fee but a model score of 50% or more is **watch**. Otherwise **clear**.
- Data sources: 70 earlier real offers plus 30 harvested from bank and merchant pages (Riyad Bank, BSF, SAIB, ANB, Alinma, Al Rajhi, IKEA, Tefal, Jarir, ...). Labels were written by Qist's builder with the rule above and still need a mentor check.
- `model/train_extractor.py`: xlm-roberta-base term extractor, to be run in Google Colab (not run yet). The app currently extracts terms with rules (`model/rules.py`); the cost maths is plain code on purpose.

## Web API (for the Lovable website)
`api/main.py` (FastAPI) wraps the same engine: `POST /analyze`, `POST /analyze-photo`, `POST /cost`, `GET /health`. It runs from the `Dockerfile` (Hugging Face Spaces, Docker SDK). The front-end prompt and sample data are in `lovable/`.
