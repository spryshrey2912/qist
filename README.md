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
- The wording flag agreed with the author's labels on 87% of the 70 labelled offers (tuned on them, so optimistic).
- It cannot read balloon / final-payment car leases correctly yet.
- Not financial advice. Nothing is stored.


## Look
'Kinetic Orange': flat orange page (no gradients), black panels, white text, sharp corners, 2px borders.
Fonts: Archivo Black (headline, marquee, big titles), Space Mono (small labels), Inter (text), Tajawal (Arabic), and **Ronzino** (functional parts: step titles,
the real-cost numbers, gauge, payment tiles, verdict labels, number boxes). Ronzino is embedded from `app/fonts/` (SIL OFL licence included);
the other fonts load from Google Fonts, so the first load needs internet. To add a font, drop `<family>-<weight>.woff2` into `app/fonts/`.
All styling is in `app/ui.py` and `.streamlit/config.toml`.

## Machine learning
- `app/ml.py`: the wording model. TF-IDF character n-grams plus 3 extractor features, into a logistic regression. It is trained at app start-up from `data/offers.csv` (250 offers, 70 real, each real row weighted 10x), so there is no model file to go stale. Its score shows in step 4 as "AI wording model".
- `model/eval_wording.py`: honest score. 5-fold cross-validation, only the 70 real rows are scored, 3 splits. Result: about 87% accuracy, 88% precision, 65% recall (always saying "fine" scores 70%). The hand-written rules alone score 87%, so the model matches them rather than beating them; it is small data (21 misleading real rows).
- `model/train_extractor.py`: xlm-roberta-base term extractor, to be run in Google Colab (not run yet). The app currently extracts terms with rules (`model/rules.py`); the cost maths is plain code on purpose.

## Web API (for the Lovable website)
`api/main.py` (FastAPI) wraps the same engine: `POST /analyze`, `POST /analyze-photo`, `POST /cost`, `GET /health`. It runs from the `Dockerfile` (Hugging Face Spaces, Docker SDK). The front-end prompt and sample data are in `lovable/`.
