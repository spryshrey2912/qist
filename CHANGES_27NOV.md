# Changes, 27 Nov (mentor review)

1. **Tasaheal bug fixed** (`app/engine.py`, one line). The app called the SAR 45 monthly fee a "hidden fee". The real
   hidden fee is the SAR 49 processing fee on the plans that say "No Monthly Fees". A stated monthly charge is no longer
   counted as a one-off fee. All tests still pass.
2. **7 labels corrected** to follow the written rule (`data/offers.csv` and copies). `real_012` is now 1; `real_001`,
   `real_057`, `real_063`, `real_066`, `real_067`, `real_068` are now 0 (they say "no hidden fees" but no fee is written in
   the text). Every real label now follows the rule.
3. **Footer on the live page** no longer says labels were assigned by AI and never reviewed (English and Arabic).
4. **README** updated with the new scores and an honest note: the 100% scores are true by construction, and the
   real machine-learning number is the text-only model (AUC 0.89).
5. **Unreviewed web offers** moved to `data/unreviewed/` with a note. Nothing uses them.
6. **`data/combine.py`** now refuses to run without `--force`, because it would overwrite `offers.csv` with the older sheet.
7. Removed `.pytest_cache/` and `__pycache__/`.

Still to do in the GitHub repo: delete `.github/workflows/keepalive.yml` (it pings a Render server the site does not use).
