# The 7 terms Qist extracts (Sprint 1, Tue)

| # | Term | Meaning | English example | Arabic example |
|---|------|---------|-----------------|----------------|
| 1 | cash_price | Price if you paid in full today | "Total price SAR 1,200" | "السعر النقدي 1200 ريال" |
| 2 | n_installments | How many payments | "4 installments" | "4 دفعات" |
| 3 | installment_amount | Each payment | "SAR 300 per month" | "بقسط 300 ريال شهرياً" |
| 4 | admin_fee | Processing / admin / activation fee | "one-time admin fee of SAR 49" | "رسوم إدارية بقيمة 49 ريال" |
| 5 | late_fee | Penalty for paying late or reactivating | "late fee SAR 75" | "غرامة التأخير 75 ريال" |
| 6 | profit_rate | Profit or interest rate | "profit rate 1.5% per month" | "نسبة الربح 1.5٪" |
| 7 | shariah_claim | Any claim of Shariah compliance | "Shariah-compliant" | "متوافقة مع الشريعة" |

Labelling rules: tag only the value (e.g. "SAR 49"), leave a term blank if the offer does not say it,
and when the same fee has two names pick the wording the offer uses.

Judge-ready one-liner: the model only *finds* these terms in text; plain code does the maths.
