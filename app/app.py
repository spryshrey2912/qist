import os, sys
import streamlit as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine, ml, ui
from ocr import read_photo

st.set_page_config(page_title="Qist | قسط", page_icon="💳")          # must be the first Streamlit call

TXT = {
    "en": {"brand": "Qist", "brand2": "قسط", "h1big": "Know the<br>real cost", "tips": {"monthly": "What you pay every month, including any monthly profit.", "total": "Everything you pay in total: all instalments plus fees.", "extra": "The total you pay minus the cash price. This is the extra cost of paying in instalments.", "ear": "The yearly rate this deal equals once fees are included. Use it to compare offers, even a 0% one.", "timeline": "One tile per month. The orange tile is the fee you pay today.", "warn": "Offers that say 0% or free can still charge a fee. We add it to the total so you see the real price."},
           "ev_t": "Where we found it", "ev_claim": "The promise", "ev_fee": "The fee", "ev_diff": "The promise and the fee are written in **different places**. Read both before you decide: the headline does not include the fee.", "ev_same": "The promise and the fee are in **the same sentence**. The headline still leaves the fee out of the price you see.", "alert_title": "Hidden fee found", "alert_msg": "This offer says **\u201c0%\u201d** but charges **SAR {fee:g}**. Your real cost is higher than advertised.",
           "help": {"price": "The price if you paid in full today, not in instalments.", "n": "How many monthly payments the offer splits the price into.", "inst": "The amount of one monthly payment, if the offer states it.", "late": "The penalty if you pay late. It only costs you if you are late.", "fee": "A one-time fee charged when you start the plan.", "feepct": "Use this if the fee is quoted as a percentage of the amount.", "rate": "The profit rate the provider charges.", "kind": "A monthly rate costs far more than the same number per year. Check which one the offer means.", "plan": "Offers often have several plans. Pick the one you would choose."},
           "scroll": "SCROLL DOWN \u2022 ", "meta_l": "Instalments<br>Card plans<br>Car finance", "meta_r": "For shoppers<br>in Saudi Arabia<br>Prices in SAR",
           "mq1": "0% can still cost you", "mq2": "True cost in SAR \u2022 Wording check \u2022 SAMA reference",
           "svc_kick": "What Qist checks", "svc": [("True cost", ["Total in SAR", "Extra you pay", "Effective rate"]), ("Hidden fees", ["Admin fee", "Processing fee", "Late fee"]), ("0% wording", ["0% plus a fee", "Some plans only"]), ("SAMA rules", ["BNPL Art. 1", "Art. 20(1)", "Art. 26"])],
           "cta": "Know before<br>you pay.", "cta_note": "Paste an offer above",
"h1": "The real cost of an instalment offer, in SAR", "demo": {"in": "The offer", "out": "What Qist finds", "lines": ["Purchase: SAR 3,000", "Period: 3 months", "Profit rate: 0%", "Processing fee: SAR 50"], "flag": "Says 0%, but a fee applies"}, "step1": "Add the offer", "step2": "What we found (check and correct)", "step3": "The real cost", "step4": "Wording check", "timeline": "Your payments: SAR fee today, then one tile per month", "sama": "Regulation reference", "title": "Qist", "sub": "Paste or photograph a buy-now-pay-later, card or car-finance offer. Qist reads the terms, adds up what you pay and flags \u201c0%\u201d wording that hides a fee.",
           "sample": "Try a sample", "none": "(none)", "paste": "Paste the offer text", "upload": "Photo", "samples": {"tasaheal": "Al Rajhi Tasaheal", "riyad": "Riyad 0% wallet", "aljazira": "AlJazira card", "kia": "Kia lease"},
           "ocr_fail": "Could not read the photo (OCR needs Tesseract with Arabic + English installed). Paste the text instead.",
           "found": "What we found (check and correct)", "price": "Cash price (SAR)", "n": "Number of instalments (months)",
           "inst": "Instalment amount (SAR)", "fee": "Admin / one-time fee (SAR)", "feepct": "Fee as % of the amount (if quoted that way)", "late": "Late fee (SAR)", "rate": "Profit rate (%)",
           "kind": "The rate is", "kinds": {"none": "not found", "monthly": "monthly (flat)", "annual": "annual (APR)", "unknown": "unclear: treated as annual"},
           "seen": "also seen in the text", "ptype": "Looks like", "plan": "Choose a plan", "plan_fmt": "{n} months, rate {r:g}%", "assumed": "The page does not say if the rate is monthly or annual. Qist assumed MONTHLY (flat). Change it below if the bank says otherwise.", "example": "No price in the offer: using the minimum purchase ({p:g} SAR) as an example. Enter your own price.", "shariah": "The offer claims to be Shariah-compliant",
           "cost": "True cost", "total": "Total you pay (SAR)", "extra": "Extra you pay (SAR)", "ear": "Effective annual rate",
           "monthly": "Monthly payment (SAR)", "needs": "Enter a cash price and the number of instalments to see the cost.",
           "payments_only": "Total of the instalments in the offer (SAR); enter the cash price to see the extra cost", "w_below_price": "The instalments add up to less than the cash price: check the price and the instalment.", "w_extreme_rate": "This rate is extremely high. The cash price, instalment or number of months is probably wrong. Check them.",
           "assume": "How this was worked out", "ml_t": "AI wording model", "ml_agree": "The wording model (trained on {n} labelled offers, {r} of them real) agrees: **{p}%** chance this wording is misleading.", "ml_disagree": "The wording model scores this low (**{p}%**), but the rules found a concrete fee in the text. Trust the fee: it is written there.", "ml_watch": "No fee was found by the rules, but the wording looks like offers that hid costs (**{p}%**, model trained on {n} labelled offers). Read the full terms before you accept.", "ml_lo": "The wording model (trained on {n} labelled offers, {r} of them real) scores only **{p}%** for misleading wording.", "check": "Wording check", "warn": "Warning", "note": "Note"},
    "ar": {"brand": "قسط", "brand2": "Qist", "h1big": "اعرف التكلفة<br>الحقيقية", "tips": {"monthly": "ما تدفعه كل شهر، شاملاً أي ربح شهري.", "total": "كل ما تدفعه في المجموع: جميع الأقساط مع الرسوم.", "extra": "إجمالي ما تدفعه ناقص السعر النقدي. هذه هي التكلفة الإضافية للتقسيط.", "ear": "النسبة السنوية التي يعادلها هذا العرض بعد إضافة الرسوم. استخدمها للمقارنة بين العروض، حتى عرض 0%.", "timeline": "مربع لكل شهر. المربع البرتقالي هو الرسم الذي تدفعه اليوم.", "warn": "العروض التي تقول 0% أو مجاني قد تفرض رسوماً. نضيفها إلى الإجمالي لتعرف السعر الحقيقي."},
           "ev_t": "أين وجدناها", "ev_claim": "الوعد", "ev_fee": "الرسم", "ev_diff": "الوعد والرسم مكتوبان في **مكانين مختلفين**. اقرأهما معاً قبل أن تقرر: العنوان الرئيسي لا يشمل الرسم.", "ev_same": "الوعد والرسم في **الجملة نفسها**. ومع ذلك فالعنوان الرئيسي لا يُدخل الرسم في السعر الذي تراه.", "alert_title": "رسوم مخفية", "alert_msg": "يعلن هذا العرض **«0%»** لكنه يفرض **{fee:g} ريال**. تكلفتك الحقيقية أعلى مما يُعلن.",
           "help": {"price": "السعر لو دفعت كاملاً اليوم، بدون تقسيط.", "n": "عدد الدفعات الشهرية التي يقسّم إليها العرض السعر.", "inst": "قيمة الدفعة الشهرية الواحدة، إن ذكرها العرض.", "late": "الغرامة عند التأخر في الدفع. لا تكلّفك إلا إذا تأخرت.", "fee": "رسم يُدفع مرة واحدة عند بدء الخطة.", "feepct": "استخدمه إذا ذُكر الرسم كنسبة من المبلغ.", "rate": "نسبة الربح التي يفرضها المزوّد.", "kind": "النسبة الشهرية تكلّف أكثر بكثير من الرقم نفسه سنوياً. تأكد أيها يقصده العرض.", "plan": "للعروض غالباً عدة خطط. اختر الخطة التي ستختارها."},
           "scroll": "مرر للأسفل \u2022 ", "meta_l": "تقسيط<br>خطط البطاقات<br>تمويل السيارات", "meta_r": "للمتسوّقين<br>في السعودية<br>الأسعار بالريال",
           "mq1": "0% قد تكلّفك أيضاً", "mq2": "التكلفة الحقيقية بالريال \u2022 فحص الصياغة \u2022 مرجع ساما",
           "svc_kick": "ما يفحصه «قسط»", "svc": [("التكلفة الحقيقية", ["الإجمالي بالريال", "المبلغ الإضافي", "المعدل الفعلي"]), ("الرسوم الخفية", ["رسوم إدارية", "رسوم معالجة", "رسوم التأخير"]), ("صياغة 0%", ["0% مع رسوم", "لبعض الخطط فقط"]), ("أنظمة ساما", ["البند 1", "المادة 20(1)", "المادة 26"])],
           "cta": "اعرف قبل<br>أن تدفع.", "cta_note": "الصق عرضاً في الأعلى",
"h1": "التكلفة الحقيقية لعرض التقسيط بالريال", "demo": {"in": "العرض", "out": "ما يجده «قسط»", "lines": ["السعر: 3,000 ريال", "المدة: 3 أشهر", "هامش الربح: 0%", "رسوم المعالجة: 50 ريال"], "flag": "يقول 0% لكن فيه رسوم"}, "step1": "أضف العرض", "step2": "ما وجدناه (تأكد منه وصحّحه)", "step3": "التكلفة الحقيقية", "step4": "فحص الصياغة", "timeline": "دفعاتك: رسم اليوم، ثم مربع لكل شهر", "sama": "مرجع تنظيمي", "title": "قسط", "sub": "الصق عرض تقسيط (اشترِ الآن وادفع لاحقاً، أو بطاقة ائتمانية، أو تمويل سيارة) أو صوّره. يقرأ «قسط» الشروط ويحسب ما تدفعه فعلاً وينبّه إلى عبارة «0%» التي تُخفي رسوماً.",
           "sample": "جرّب عرضاً", "none": "(بدون)", "paste": "الصق نص العرض", "upload": "صورة", "samples": {"tasaheal": "تساهيل الراجحي", "riyad": "بنك الرياض قسّط 0%", "aljazira": "بنك الجزيرة", "kia": "تأجير كيا"},
           "ocr_fail": "تعذّرت قراءة الصورة (يحتاج إلى Tesseract مع اللغتين العربية والإنجليزية). الصق النص بدلاً من ذلك.",
           "found": "ما وجدناه (تأكد منه وصحّحه)", "price": "السعر النقدي (ريال)", "n": "عدد الأقساط (أشهر)",
           "inst": "قيمة القسط (ريال)", "fee": "رسوم إدارية / لمرة واحدة (ريال)", "feepct": "الرسوم كنسبة من المبلغ (إن ذُكرت هكذا)", "late": "رسوم التأخير (ريال)", "rate": "نسبة الربح (%)",
           "kind": "النسبة", "kinds": {"none": "غير موجودة", "monthly": "شهرية (ثابتة)", "annual": "سنوية", "unknown": "غير واضحة: تعامل كسنوية"},
           "seen": "وردت أيضاً في النص", "ptype": "يبدو أنه", "plan": "اختر الخطة", "plan_fmt": "{n} أشهر، النسبة {r:g}٪", "assumed": "لا تذكر الصفحة هل النسبة شهرية أم سنوية. افترض «قسط» أنها شهرية (ثابتة). غيّرها أدناه إن ذكر البنك غير ذلك.", "example": "لا يوجد سعر في العرض: نستخدم الحد الأدنى للشراء ({p:g} ريال) كمثال. أدخل سعرك.", "shariah": "يدّعي العرض أنه متوافق مع الشريعة",
           "cost": "التكلفة الحقيقية", "total": "إجمالي ما تدفعه (ريال)", "extra": "المبلغ الإضافي (ريال)", "ear": "المعدل السنوي الفعلي",
           "monthly": "القسط الشهري (ريال)", "needs": "أدخل السعر النقدي وعدد الأقساط لعرض التكلفة.",
           "payments_only": "مجموع الأقساط في العرض (ريال)؛ أدخل السعر النقدي لمعرفة المبلغ الإضافي", "w_below_price": "مجموع الأقساط أقل من السعر النقدي: تحقق من السعر ومن القسط.", "w_extreme_rate": "هذه النسبة مرتفعة جداً. على الأرجح أن السعر النقدي أو القسط أو عدد الأشهر غير صحيح. تحقق منها.",
           "assume": "كيف حُسبت", "ml_t": "نموذج الذكاء الاصطناعي", "ml_agree": "نموذج الصياغة (مدرَّب على {n} عرضاً مصنَّفاً، منها {r} حقيقية) يوافق: احتمال أن تكون الصياغة مضللة **{p}٪**.", "ml_disagree": "نموذج الصياغة يعطي نسبة منخفضة (**{p}٪**)، لكن القواعد وجدت رسماً محدداً في النص. اعتمد على الرسم لأنه مكتوب فيه.", "ml_watch": "لم تجد القواعد رسماً، لكن الصياغة تشبه عروضاً أخفت تكاليفها (**{p}٪**، نموذج مدرَّب على {n} عرضاً). اقرأ الشروط كاملة قبل أن تقبل.", "ml_lo": "نموذج الصياغة (مدرَّب على {n} عرضاً مصنَّفاً، منها {r} حقيقية) يعطي **{p}٪** فقط للصياغة المضللة.", "check": "فحص الصياغة", "warn": "تنبيه", "note": "ملاحظة"},
}
HOW_AR = {"from the instalment in the offer": "من القسط المذكور في العرض",
          "flat monthly rate on the original price": "نسبة شهرية ثابتة على السعر الأصلي",
          "annual rate on a reducing balance": "نسبة سنوية على الرصيد المتناقص",
          "price divided equally (no profit rate found)": "السعر مقسوماً بالتساوي (لم تُوجد نسبة ربح)"}

SAMPLES = {
    "tasaheal": "Terms and Conditions of Tasaheal Program (excerpt)\nPlan | 3 months | 6 months | 9 months | 12 months\nSAR 500 or above | No Monthly Fees | 0.9% Monthly Fees*\nOne-time processing fee* | SAR 49 | 2% of the transaction value with minimum of SAR 100 and maximum of SAR 1,500\nIllustrative Example – SAR 5,000 Installment:\nTransaction amount | SAR 5000\nInstallment plan chosen by the customer | 12 months\nTasaheal monthly fees | SAR 45\nOne-time processing fee | SAR 100\nMonthly installment Amount | SAR 461.66",
    "riyad": "قسط 0%\nيسري العرض حتى 31/05/2026\nاشحن محفظتك الــرقــمــيـــــة وحولها لِقسّط 0%\nساري حتى\n31/05/2026\n• اشحن محفظتك الرقمية باستخدام بطاقتك الائتمانية من بنك الرياض وحولها إلى قسّط 0٪ لمدة 3 أشهر!\n• تنطبق الحملة فقط على حاملي البطاقات الائتمانية من بنك الرياض الذين تلقوا اشعارات من بنك الرياض عبر الرسائل النصية القصيرة أو البريد الإلكتروني أو إشعارات الهاتف المحمول.\n• سيتم فرض رسوم قدرها 50 ريال سعودي على كل عملية يتم تحويلها إلى \"قسّط 0%\".\n• العمليات المؤهلة: عمليات شحن المحافظ الرقمية فقط مؤهلة لهذه الحملة. تُحدد عمليات شحن المحافظ الرقمية وفقًا لتصنيف رمز فئة التاجر (MCC) الذي تُجريه فيزا أو ماستركارد. يحتفظ البنك بجميع الحقوق في استبعاد أي عملية لا تتوافق مع هذا التصنيف العالمي.\n• جميع العمليات المؤهلة التي أُجريت بين 25/04/2026 و 31/05/2026 تُؤخذ في الاعتبار في هذه الحملة، ويتم تحويلها إلى خطط تقسيط قسّط خلال نفس الفترة.\n• للاستفادة من هذا العرض، يجب أن تكون قيمة العملية المؤهلة 1000 ريال سعودي أو أكثر.\n• أي إلغاء مشتريات، أو استرداد، أو إرجاع، أو عمليات متنازع عليها ستُستثنى من العرض.",
    "aljazira": "Bank Aljazira\nMinimum Purchase : SR 1000\nMaximum Purchase : Cardholder limit\nInstallment Period : 3, 6, 9 and 12 months\nInterest Rate : 0% for 3 months, 1.5% for 6 months, 1.2% for 9 months, 1% for 12 months\nProcessing Fees : SR 50",
    "kia": "The offer on the KIA Sonet 1.5L GL\nMonthly installment 1370 SAR\nThe first 3 installments are on us\n0% down payment\nNo guarantor required\n• Financing period is 60 months\n• Annual percentage rate (Pegas 20.23% – K3 20.21% – Sonet 20.21%) approximately\n• 1% administrative fee",
}


if "lang" not in st.session_state: st.session_state["lang"] = "en"
if "offer_text" not in st.session_state: st.session_state["offer_text"] = ""
def panel(name):
    """One stone panel. A keyed container gets the CSS class st-key-panel_<name>; older Streamlit has no key, so fall back to a plain border."""
    try:
        return st.container(key=f"panel_{name}")
    except TypeError:
        return st.container(border=True)
def _set_lang(code): st.session_state["lang"] = code
def _set_sample(key): st.session_state["offer_text"] = SAMPLES[key]
lang = st.session_state["lang"]
T = TXT[lang]
st.markdown(ui.css(lang), unsafe_allow_html=True)
c_en, c_ar = st.columns(2)                                         # the language pill: two buttons, the active one is white
with c_en:
    st.button("English", key="lang_en", type="primary" if lang == "en" else "secondary", on_click=_set_lang, args=("en",))
with c_ar:
    st.button("العربية", key="lang_ar", type="primary" if lang == "ar" else "secondary", on_click=_set_lang, args=("ar",))
DEMO = engine.cost(3000, 3, 0, 50, 0, "monthly", 0, None)          # the hero example: same engine, same answer as the app
st.markdown(ui.hero_top(T, lang), unsafe_allow_html=True)
st.markdown(ui.hero_body(T, DEMO, lang) + ui.marquee(T), unsafe_allow_html=True)
with panel("add"):
    st.markdown(ui.section(1, T["step1"]), unsafe_allow_html=True)
    st.caption(T["sample"])
    for col, key in zip(st.columns(len(SAMPLES)), SAMPLES):            # sample offers as chips: one click fills the box
        with col:
            st.button(T["samples"][key], key=f"sample_{key}", on_click=_set_sample, args=(key,))
    c_text, c_photo = st.columns([5, 1])
    with c_text:
        text = engine.clean(st.text_area(T["paste"], key="offer_text", height=170))
    with c_photo:
        photo = st.file_uploader(T["upload"], type=["png", "jpg", "jpeg"])      # shown as an icon tile (see ui.css)

if photo and not text.strip():
    try:
        from PIL import Image
        text, note = read_photo(Image.open(photo))
        st.text_area("OCR", text, height=120)
        if note: st.warning(note)
    except Exception as e:
        st.error(T["ocr_fail"]); st.caption(f"{type(e).__name__}: {e}")

if text.strip():
    c = engine.candidates(text)
    d = engine.defaults(c, text)
    with panel("found"):
        st.markdown(ui.section(2, T["step2"]) + ui.chip(f'{T["ptype"]}: {engine.PRODUCT_NAME[lang][d["product"]]}'), unsafe_allow_html=True)
        n_def, rate_def = int(d["n_installments"]), float(d["profit_rate"])
        if d["plans"]:
            keys = sorted(d["plans"])
            n_def = st.selectbox(T["plan"], keys, index=keys.index(n_def) if n_def in keys else len(keys) - 1,
                                 format_func=lambda k: T["plan_fmt"].format(n=k, r=d["plans"][k]), help=T["help"]["plan"])
            rate_def = d["plans"][n_def]
        price_def = float(d["cash_price"]) or float(d["example_price"])
        if not d["cash_price"] and d["example_price"]:
            st.caption(T["example"].format(p=d["example_price"]))
        c1, c2 = st.columns(2)
        with c1:
            price = st.number_input(T["price"], min_value=0.0, value=price_def, step=100.0, key=f"price_{price_def}", help=T["help"]["price"])
            n = st.number_input(T["n"], min_value=0, value=n_def, step=1, key=f"n_{n_def}", help=T["help"]["n"])
            if len(c["n_installments"]) > 1:
                st.caption(f'{T["seen"]}: {", ".join("%g" % v for v in c["n_installments"])}')
            inst = st.number_input(T["inst"], min_value=0.0, value=float(d["installment_amount"]), step=10.0, help=T["help"]["inst"])
            late = st.number_input(T["late"], min_value=0.0, value=float(d["late_fee"]), step=10.0, help=T["help"]["late"])
        with c2:
            fee = st.number_input(T["fee"], min_value=0.0, value=float(d["admin_fee"]), step=10.0, help=T["help"]["fee"])
            if len(c["admin_fee"]) > 1:
                st.caption(f'{T["seen"]}: {", ".join("%g" % v for v in c["admin_fee"])}')
            fee_pct = st.number_input(T["feepct"], min_value=0.0, value=float(d["admin_fee_pct"]), step=0.1, help=T["help"]["feepct"])
            rate = st.number_input(T["rate"], min_value=0.0, value=rate_def, step=0.1, key=f"rate_{n_def}_{rate_def}", help=T["help"]["rate"])
            kinds = list(T["kinds"])
            kind = st.selectbox(T["kind"], kinds, index=kinds.index(d["rate_kind"]), format_func=lambda k: T["kinds"][k], help=T["help"]["kind"])
        if d["rate_assumed"]:
            st.caption(T["assumed"])
        if d["shariah_claim"]:
            st.caption("✔ " + T["shariah"])

    fl = engine.flags(text, c)
    hidden = [dd for code, dd in fl if code == "zero_but_fee"]
    with panel("cost"):
        st.markdown(ui.section(3, T["step3"]), unsafe_allow_html=True)
        if hidden:                                           # the loud banner: a 0% offer that still charges a fee
            st.markdown(ui.alert(T["alert_title"], T["alert_msg"].format(fee=hidden[0]["fee"]), T["tips"]["warn"]), unsafe_allow_html=True)
            st.markdown(ui.evidence(T, engine.evidence(text, hidden[0]["fee"])), unsafe_allow_html=True)
        r = engine.cost(price, int(n), inst, fee, rate, kind, fee_pct, d["admin_fee_cap"])
        if r is None:
            st.markdown(ui.verdict("note", "", T["needs"]), unsafe_allow_html=True)
            if inst > 0 and n > 0:
                st.markdown(ui.verdict("note", T["payments_only"], f"{round(inst * int(n) + fee, 2):,.2f} SAR"), unsafe_allow_html=True)
        else:
            fee_total = r["fee_total"]
            out = "".join(ui.verdict("bad", "", T["w_" + w]) for w in r["warnings"])
            out += ui.results(T, r, price, int(n), fee_total)
            st.markdown(out, unsafe_allow_html=True)
            st.caption(f'{T["assume"]}: ' + (HOW_AR[r["how"]] if lang == "ar" else r["how"]))

    with panel("check"):
        st.markdown(ui.section(4, T["step4"]), unsafe_allow_html=True)
        msgs, rules, disc = engine.explain(lang, fl, d["product"])
        out = ""
        for (code, _), m in zip(fl or [(None, None)], msgs):
            kind_ = "warn" if code == "zero_but_fee" else "note" if code else "ok"
            out += ui.verdict(kind_, T["warn"] if kind_ == "warn" else T["note"] if kind_ == "note" else "", m, T["tips"]["warn"] if kind_ == "warn" else "")
        pm = ml.p_misleading(text)                           # the machine-learning score, next to the rule-based flags
        if pm is not None:
            hit = any(code == "zero_but_fee" for code, _ in (fl or []))
            key = ("ml_agree" if pm >= .5 else "ml_disagree") if hit else ("ml_watch" if pm >= .5 else "ml_lo")
            out += ui.verdict("warn" if (pm >= .5 and not hit) or key == "ml_agree" else "note" if key == "ml_disagree" else "ok", T["ml_t"],
                              T[key].format(p=round(pm * 100), n=ml.info()["n"], r=ml.info()["n_real"]))
        st.markdown(out + ui.sama(T, rules, disc), unsafe_allow_html=True)

st.markdown(ui.services(T, lang) + ui.closer(T, lang), unsafe_allow_html=True)
