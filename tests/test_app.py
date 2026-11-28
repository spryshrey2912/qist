"""Tests for the rule engine, cost maths and wording model (the code the live site runs in the browser)."""
import os, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(ROOT, "app"))
import engine

def test_engine_tasaheal():
    t = open(os.path.join(ROOT, "tests", "tasaheal.txt"), encoding="utf-8").read()
    c = engine.candidates(t); d = engine.defaults(c, t)
    r = engine.cost(5000, 12, 461.66, 100)
    assert abs(r["total_paid"] - (461.66 * 12 + 100)) < 0.01
    assert engine.is_misleading(engine.flags(t)) is True or engine.flags(t)

def test_cost_from_monthly_rate():
    r = engine.cost(5000, 12, 0, 100, 0.9, "monthly")
    assert abs(r["instalment"] - 461.67) < 0.01          # 5000/12 + 45, matches Al Rajhi's own example

def test_zero_with_fee_is_flagged():
    t = "قسط 0% هامش ربح لمدة 6 أشهر. رسوم تحويل العملية الى أقساط 50 ريال."
    assert engine.is_misleading(engine.flags(t))

def test_clean_zero_not_flagged():
    t = "Pay in 3 installments at 0% profit. No other charges."
    assert not engine.is_misleading(engine.flags(t))

def test_no_fees_claim_does_not_turn_the_price_into_a_fee():
    for t in ("Pay in 4 interest-free payments of SAR 250. No fees, no hidden charges. Total price SAR 1,000.",
              "0% profit for 6 months with no fees. Product price SAR 2,400.",
              "أقساط 0% لمدة 6 أشهر بدون أي رسوم. سعر المنتج 2,400 ريال."):
        assert not engine.is_misleading(engine.flags(t)), t

def test_warranty_years_are_not_the_loan_term():
    t = open(os.path.join(ROOT, "tests", "elantra.txt"), encoding="utf-8").read()
    d = engine.defaults(engine.candidates(t), t)
    assert d["n_installments"] == 0 and d["installment_amount"] == 899

def test_absurd_inputs_warn():
    assert "extreme_rate" in engine.cost(900, 60, 899, 0)["warnings"]
    assert "below_price" in engine.cost(1000000, 60, 899, 0)["warnings"]

def test_aljazira_card_plans():
    t = open(os.path.join(ROOT, "tests", "aljazira.txt"), encoding="utf-8").read()
    d = engine.defaults(engine.candidates(t), t)
    assert d["plans"] == {3: 0.0, 6: 1.5, 9: 1.2, 12: 1.0}
    assert d["product"] == "card" and d["admin_fee"] == 50 and d["example_price"] == 1000
    assert ("zero_but_fee", {"fee": 50.0}) in engine.flags(t)
    r = engine.cost(3000, 3, 0, 50, 0.0, "monthly")
    assert r["total_paid"] == 3050 and r["extra_cost"] == 50       # "0%" plan still costs the SAR 50 fee
    r = engine.cost(3000, 12, 0, 50, 1.0, "monthly")
    assert r["instalment"] == 280 and r["total_paid"] == 3410

def test_explanations_in_both_languages():
    msgs, _, _ = engine.explain("en", [("zero_but_fee", {"fee": 50.0})])
    assert "SAR 50" in msgs[0] and "**" in msgs[0]
    msgs, _, _ = engine.explain("ar", [("zero_but_fee", {"fee": 50.0})])
    assert "50 ريال" in msgs[0]

def test_hidden_fee_evidence():
    import engine
    t = "Buy now, 0% profit for 12 months!\nProcessing fee: SAR 50\nMinimum purchase SAR 1000"
    ev = engine.evidence(t, 50.0)
    assert ev["claim"][0].startswith("Buy now") and ev["fee"][0] == "Processing fee: SAR 50" and not ev["same_line"]
    assert t.splitlines()[1][ev["fee"][1]:ev["fee"][2]] == "SAR 50"       # the highlight is exactly the fee
    assert engine.evidence("No fees at all", 50.0)["fee"] is None

def test_analyze_output_is_json_friendly():
    import json, analyze
    r = analyze.analyze("Buy now, 0% profit for 12 months!\nProcessing fee: SAR 50\nCash price SAR 1200", "en")
    json.dumps(r)                                                         # must be JSON-friendly for the web API
    assert r["hidden_fee"]["amount"] == 50 and r["cost"]["total_paid"] > 1200 and r["flags"][0]["code"] == "zero_but_fee"
    assert analyze.analyze("hello", "ar")["hidden_fee"] is None and analyze.compute_cost(0, 12) is None

def test_ml_wording_model():
    import ml
    bad = ml.p_misleading("0% profit for 12 months. Processing fee SAR 50.")
    ok = ml.p_misleading("Pay in 4 equal payments. No fees. No interest.")
    assert 0 <= ok <= 1 and 0 <= bad <= 1 and bad > ok          # a buried fee scores higher than a clean offer

def test_saved_wording_model_is_current_and_matches_sklearn():
    """model/wording_model.json must come from the current data/offers.csv, and its plain-Python scores must equal scikit-learn's."""
    import hashlib, ml
    m = ml.saved()
    assert m is not None, "model/wording_model.json is missing: run python model/train_wording.py"
    assert m["data_sha256"] == hashlib.sha256(open(ml.DATA, "rb").read()).hexdigest(), "offers.csv changed: re-run python model/train_wording.py"
    ref = ml.model()
    for t in ["0% profit for 12 months. Processing fee SAR 50.", "Pay in 4 equal payments. No fees. No interest.", "قسّط بدون فوائد ورسوم إدارية 50 ريال"]:
        assert abs(ml.p_misleading(t) - float(ref.predict_proba([t])[0][1])) < 1e-5

def test_wording_flag_fixes_from_new_real_offers():
    """Each case below was a wrong answer on a real offer harvested from a bank/merchant page."""
    import engine
    hit = lambda t: any(k == "zero_but_fee" for k, _ in engine.flags(t, engine.candidates(t)))
    assert not hit("قسّط مشترياتك لمدة 12 شهر.\nيرجى الاتصال على الرقم المجاني بعد 48 ساعة. رسوم تحويل العملية 50 ريال")  # 'free phone number' is not a free-fee claim
    assert hit("قسّط 0%\n• يوجد عمولة برنامج قسط لمرة واحدة بقيمة 50 S..R .\n• يجب ألا تقل قيمة المشتريات 1000 S..R")      # '0%' next to the word instalment, 'S..R' currency, limit on the next line
    assert hit("برنامج بدون هامش ربح\nرسوم الخدمة\n50 فقط (الرسوم ثابتة)")                                                  # fee label and amount on separate lines
    assert not hit("Tabby is free and interest-free. A small fee (15 SAR) applies for the cash on delivery service.")        # cash-on-delivery fee is not the instalment fee
    assert not hit("Interest-free plans. A late payment fee of SAR 100 applies if you miss a payment.")                      # late-payment fee is allowed by SAMA, not hidden
    assert not hit("0% profit. Annual card fee SAR 425.")                                                                    # annual card fee is not the instalment price

def test_ocr_096_and_exact_fee():
    from analyze import analyze
    a = analyze("Minimum Purchase : SR 1000\nInterest Rate : 096 for 3 months, 1.5% for 6 months, 1.2% for 9 months, 1% for 12 months\nProcessing Fees : SR 50", "en")
    assert a["terms"]["plans"].get("3") == 0.0 or a["terms"]["plans"].get(3) == 0.0
    assert a["cost"]["fee_total"] == 50.0 and a["cost"]["total_paid"] == 1170.0
    assert any(f["code"] == "zero_but_fee" for f in a["flags"])

def test_sample_offers_not_in_training():
    import pandas as pd, ml
    df = pd.read_csv(os.path.join(ROOT, "data", "offers.csv"))
    assert (df.demo == 1).sum() >= 6 and ml.info()["n"] == len(df) - int((df.demo == 1).sum())
    from analyze import analyze
    a = analyze("قسّط 0%\nسيتم فرض رسوم قدرها 50 ريال سعودي على كل عملية.", "ar")
    assert a["verdict"]["level"] == "warning" and a["ml_info"]["n_real"] > 50

if __name__ == "__main__":
    for f in [test_engine_tasaheal, test_cost_from_monthly_rate, test_zero_with_fee_is_flagged, test_clean_zero_not_flagged, test_warranty_years_are_not_the_loan_term, test_absurd_inputs_warn, test_aljazira_card_plans, test_explanations_in_both_languages, test_hidden_fee_evidence, test_analyze_output_is_json_friendly, test_ml_wording_model]:
        f(); print("ok", f.__name__)


def test_arabic_real_offers_fee_without_currency_and_annual_rate_zero():
    # Al Jazira "La Tajil": 'بدون هامش ربح' for 3 months + '57.5 كرسوم إدارية' (no currency written).
    from analyze import analyze as _an
    laj = "تقسيط بدون هامش ربح لمدة 3 أشهر. هامش ربح شهري 1.5% لمدة 6 أشهر. سيتم احتساب مبلغ 57.5 كرسوم إدارية شاملة رسوم القيمة المضافة."
    r = _an(laj, "ar")
    assert r["verdict"]["level"] == "warning" and r["hidden_fee"]["amount"] == 57.5
    # Awwal Aqsat: 'بمعدل سنوي 0%' is an annual RATE of 0%, not an annual fee.
    aw = "تقسيط 6 أشهر بمعدل سنوي 0% ورسوم إدارية 113.85 ريال. 24 شهراً بمعدل 24% ورسوم إدارية 57.5 ريال."
    r = _an(aw, "ar")
    assert r["verdict"]["level"] == "warning" and r["hidden_fee"]["amount"] == 113.85
    # an honest offer with a disclosed fee and no 0% promise stays clear
    ok = "Profit rate 7.5% per year, 36 months, administrative fee SAR 500 shown in the contract. Finance amount SAR 40,000."
    assert _an(ok, "en")["verdict"]["level"] == "clear"

def test_rate_waiver_cashback_are_not_fees_and_gcc_currencies():
    """Al Rajhi page: '100% fee waiver' and 'annual rate from 5.01%' once read as a hidden fee of 5.01. Other GCC currencies are fees too."""
    import engine
    hit = lambda t: [d for k, d in engine.flags(t, engine.candidates(t)) if k == "zero_but_fee"]
    assert not hit("إعفاء كامل الرسوم الادارية 100% لمنتجات التمويل الشخصي ... استمتع بتمويلك بدون رسوم إدارية. ... معدل النسبة السنوي يبدأ من 5.01%")
    assert not hit("0% interest instalments. Get 5% cashback on all purchases. Annual percentage rate 4.5%.")
    for cur in ("KWD", "KD", "QAR", "QR", "BHD", "BD", "AED", "OMR"):
        h = hit("Enjoy 0%% interest instalments. A one-time processing fee of %s 6 will apply." % cur)
        assert h and h[0]["fee"] == 6.0 and h[0].get("cur") == {"KD": "KWD", "QR": "QAR", "BD": "BHD"}.get(cur, cur), cur
    h = hit("0% profit rate. A conversion fee of SAR 50 applies.")
    assert h == [{"fee": 50.0}]                                     # riyal fees keep the old shape
    msgs, _, _ = engine.explain("en", [("zero_but_fee", {"fee": 6.0, "cur": "KWD"})])
    assert "KWD 6" in msgs[0]

def test_early_settlement_fee_is_not_an_upfront_fee_and_profit_margin_zero_is_a_claim():
    import engine
    hit = lambda t: any(k == "zero_but_fee" for k, _ in engine.flags(t, engine.candidates(t)))
    assert not hit("0% Interest. Zero fees. No Hidden Charges. A foreclosure fee of AED 100 applies if you close the plan early.")
    assert not hit("0% interest plan. An early settlement fee of 1% of the principal outstanding applies.")
    assert hit("Monthly Profit Margin 0%. A processing fee of SAR 50 will be charged on each booking.")

def test_negated_fee_and_purchase_threshold_are_not_a_fee():
    """Amex Plan It: 'no set-up fee ... purchase above SAR 1000' once read as a fee of 1000."""
    import engine
    t = "تقسيط مجاني بدون رسوم تأسيس وبدون هامش مرابحة على أي عملية شراء تتجاوز 1000 ريال سعودي"
    assert not any(k == "zero_but_fee" for k, _ in engine.flags(t, engine.candidates(t)))

def test_api_returns_fee_currency_separately():
    """A non-SAR fee must never reach the front end as a bare number that looks like riyals."""
    from analyze import analyze
    a = analyze("Enjoy 0% interest instalments. A one-time processing fee of KWD 6 will apply.", "en")
    assert a["hidden_fee"]["amount"] == 6.0 and a["hidden_fee"]["currency"] == "KWD"
    assert "KWD 6" in a["flags"][0]["message"] and "SAR 6" not in a["flags"][0]["message"]
    b = analyze("0% profit rate. A conversion fee of SAR 50 applies.", "en")
    assert b["hidden_fee"]["amount"] == 50.0 and b["hidden_fee"]["currency"] == "SAR"


def test_arabic_and_iso_currency_names_are_not_reported_as_sar():
    """Round 3: an AED fee written in Arabic ("درهماً إماراتي") must not come back as SAR, and KD/QR use ISO codes."""
    def cur(t):
        f = engine.flags(engine.clean(t), engine.candidates(engine.clean(t)))
        return [d.get("cur", "SAR") for c, d in f if c == "zero_but_fee"]
    assert cur("تتضمن خطط التقسيط بفائدة 0% رسوم معالجة قدرها 51.45 درهماً إماراتي لكل معاملة.") == ["AED"]
    assert cur("0% interest. KD 6 processing fee applies") == ["KWD"]
    assert cur("0% interest. processing fee QR 25 applies") == ["QAR"]
    assert cur("0% profit, processing fee SAR 50") == ["SAR"]


def test_fee_on_other_tenures_is_not_a_hidden_fee_but_a_zero_claim_with_positive_rate_is_a_watch():
    """Tamara terms: the 3-payment option is free, only tenures of 4 to 24 months carry a 1% fee -> not a hidden fee. A real fee on the free plan still flags."""
    import engine
    from analyze import analyze
    t = ("The 3-payment option is offered completely free of any fees.\nTenures from 4 to 24 months are subject to a processing fee of 1% of the financed amount.\n"
         "Tenures from 4 to 24 months are subject to a monthly profit margin ranging from 0.00% to 2.00%.")
    assert not [k for k, _ in engine.flags(t, engine.candidates(t)) if k == "zero_but_fee"]
    assert [k for k, _ in engine.flags("0% profit instalments. A processing fee of SAR 50 applies.", None) if k == "zero_but_fee"]
    a = analyze("0% profit margin for 3 months. 0.95% monthly for 6 months. 0.99% monthly for 12 months.", "en")
    assert a["verdict"]["level"] in ("watch", "warning")
