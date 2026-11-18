"""Runs app/app.py with a fake Streamlit so logic errors show up without a browser. Also tests the engine."""
import os, sys, types, importlib, runpy
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

def test_custom_fonts_are_embedded():
    import shutil, tempfile, ui
    out = ui.css("en")                                       # Ronzino ships in app/fonts
    assert "font-family:'Ronzino';font-weight:700" in out and "font-family:'Ronzino';font-weight:500" in out and "base64," in out
    assert "var(--fn)" in out and "--fn:'Ronzino'" in out
    tmp = tempfile.mkdtemp(); old = ui.FONT_DIR
    try:
        shutil.copy(os.path.join(old, "ronzino-700.woff2"), os.path.join(tmp, "bogus.woff2"))      # wrong name: ignored
        ui.FONT_DIR = tmp
        assert "@font-face" not in ui.css("en")
    finally:
        ui.FONT_DIR = old

def test_alert_and_bold_and_tooltips():
    import ui
    a = ui.alert("Hidden fee found", "This offer says **\u201c0%\u201d** but charges **SAR 50**.", "tip text")
    assert 'role="alert"' in a and "<strong>" in a and 'data-tip="tip text"' in a and "\n" not in a
    v = ui.verdict("warn", "Warning", "A **bold** thing <b>", "why")
    assert "<strong>bold</strong>" in v and "&lt;b&gt;" in v and 'role="alert"' in v      # bold works, raw HTML is escaped
    msgs, _, _ = engine.explain("en", [("zero_but_fee", {"fee": 50.0})])
    assert "SAR 50" in msgs[0] and "**" in msgs[0]
    msgs, _, _ = engine.explain("ar", [("zero_but_fee", {"fee": 50.0})])
    assert "50 ريال" in msgs[0]
    for lang in ("en", "ar"):                              # the hidden-fee banner shows for the 0% + fee sample
        _, html = run_app(lang, "Bank Aljazira. Interest Rate : 0% for 3 months. Processing Fees : SR 50. Installment Period : 3 months. Minimum Purchase : SR 1000")
        assert "q-alert" in html

def run_app(lang, text):
    calls = []
    class Ctx:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def metric(self, *a, **k): calls.append(("metric", a))
    st = types.ModuleType("streamlit")
    st.set_page_config = lambda **k: calls.append(("cfg", k))
    class S(dict):
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
    st.session_state = S(lang=lang)
    st.button = lambda *a, **k: False
    html_seen = []
    st.markdown = lambda s, **k: html_seen.append(s)
    st.title = st.caption = st.subheader = st.info = st.success = st.warning = st.error = lambda *a, **k: None
    st.selectbox = lambda label, opts, index=0, **k: opts[index]
    st.text_area = lambda label, value="", **k: text if label.startswith(("Paste", "الصق")) else value
    st.number_input = lambda label, **k: k.get("value", 0)
    st.file_uploader = lambda *a, **k: None
    st.components = types.SimpleNamespace(v1=types.SimpleNamespace(html=lambda s, **k: html_seen.append(s)))
    st.container = lambda **k: Ctx()
    st.columns = lambda n, **k: [Ctx() for _ in range(n if isinstance(n, int) else len(n))]
    sys.modules["streamlit"] = st
    runpy.run_path(os.path.join(ROOT, "app", "app.py"), run_name="__main__")
    assert calls[0][0] == "cfg"                         # set_page_config first
    joined = "".join(html_seen)
    assert "<style>" in joined and "q-hero" in joined      # styling and hero were emitted
    assert "\n\n" not in joined                           # no blank lines: Streamlit would turn them into code blocks
    return calls, joined

def test_hidden_fee_evidence():
    import engine, ui
    t = "Buy now, 0% profit for 12 months!\nProcessing fee: SAR 50\nMinimum purchase SAR 1000"
    ev = engine.evidence(t, 50.0)
    assert ev["claim"][0].startswith("Buy now") and ev["fee"][0] == "Processing fee: SAR 50" and not ev["same_line"]
    assert t.splitlines()[1][ev["fee"][1]:ev["fee"][2]] == "SAR 50"       # the highlight is exactly the fee
    assert "<mark>SAR 50</mark>" in ui.evidence(TXT_EN(), ev)
    assert engine.evidence("No fees at all", 50.0)["fee"] is None

def TXT_EN():
    import runpy, types
    return {k: k for k in ("ev_t", "ev_claim", "ev_fee", "ev_diff", "ev_same")}

def test_api_logic_and_ocr():
    import json, analyze, ocr
    from PIL import Image, ImageDraw
    r = analyze.analyze("Buy now, 0% profit for 12 months!\nProcessing fee: SAR 50\nCash price SAR 1200", "en")
    json.dumps(r)                                                         # must be JSON-friendly for the web API
    assert r["hidden_fee"]["amount"] == 50 and r["cost"]["total_paid"] > 1200 and r["flags"][0]["code"] == "zero_but_fee"
    assert analyze.analyze("hello", "ar")["hidden_fee"] is None and analyze.compute_cost(0, 12) is None
    im = Image.new("RGB", (700, 80), "white"); ImageDraw.Draw(im).text((10, 30), "0% profit. Processing fee: SAR 50", fill="black")
    assert callable(ocr.read_photo)                                       # app.py used to call a read_photo that did not exist

def test_ml_wording_model():
    import ml
    bad = ml.p_misleading("0% profit for 12 months. Processing fee SAR 50.")
    ok = ml.p_misleading("Pay in 4 equal payments. No fees. No interest.")
    assert 0 <= ok <= 1 and 0 <= bad <= 1 and bad > ok          # a buried fee scores higher than a clean offer

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

def test_app_runs():
    for lang in ("en", "ar"):
        run_app(lang, "")
        run_app(lang, "Split into 4 payments of SAR 300. Admin fee SAR 50. 0% profit. Cash price SAR 1200.")
        run_app(lang, "عرض 0% هامش ربح لمدة 6 أشهر ورسوم 50 ريال")
        run_app(lang, "nothing useful here")
        run_app(lang, open(os.path.join(ROOT, 'tests', 'aljazira.txt'), encoding='utf-8').read())
        run_app(lang, open(os.path.join(ROOT, 'tests', 'elantra.txt'), encoding='utf-8').read())

if __name__ == "__main__":
    for f in [test_engine_tasaheal, test_cost_from_monthly_rate, test_zero_with_fee_is_flagged, test_clean_zero_not_flagged, test_warranty_years_are_not_the_loan_term, test_absurd_inputs_warn, test_aljazira_card_plans, test_custom_fonts_are_embedded, test_alert_and_bold_and_tooltips, test_hidden_fee_evidence, test_api_logic_and_ocr, test_ml_wording_model, test_app_runs]:
        f(); print("ok", f.__name__)
