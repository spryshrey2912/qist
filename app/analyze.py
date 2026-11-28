"""One function that runs the whole check and returns plain data (JSON-friendly)."""
import engine, ml

def _loc(t):
    return {"line": t[0], "start": t[1], "end": t[2]} if t else None

def compute_cost(price, n, inst=0.0, fee=0.0, rate=0.0, rate_kind="none", fee_pct=0.0, fee_cap=0.0):
    """The real cost, or None when the price or the number of instalments is missing."""
    r = engine.cost(float(price), int(n), float(inst), float(fee), float(rate), rate_kind, float(fee_pct), float(fee_cap))
    if r is None: return None
    return r

def _verdict(hit, pm, some_plans=False):
    """One answer from both parts: a fee next to a 0%/free promise is 'warning' (it is written in the text);
    no fee but the wording model says >= 40% is 'watch'; otherwise 'clear'. 'agree' says whether the model backs the rules."""
    hi = pm is not None and pm >= ml.THRESHOLD
    level = "warning" if hit else "watch" if (hi or some_plans) else "clear"      # a 0% claim next to a positive rate = check which plan
    return {"level": level, "model_agrees": (hi == hit) if pm is not None else None}

def analyze(text, lang="en"):
    lang = "ar" if lang == "ar" else "en"
    text = engine.clean(text)
    c = engine.candidates(text); d = engine.defaults(c, text)
    plans = {int(k): v for k, v in d["plans"].items()}
    n, rate = int(d["n_installments"]), float(d["profit_rate"])
    if plans:                                                # default plan choice
        n = n if n in plans else max(plans); rate = plans[n]
    price = float(d["cash_price"]) or float(d["example_price"])
    cost = compute_cost(price, n, d["installment_amount"], d["admin_fee"], rate, d["rate_kind"], d["admin_fee_pct"], d["admin_fee_cap"] or 0.0)
    fl = engine.flags(text, c)
    hidden = [dd["fee"] for code, dd in fl if code == "zero_but_fee"]
    hidden_cur = [dd.get("cur", "SAR") for code, dd in fl if code == "zero_but_fee"]      # fee currency; the cost maths below stay SAR-only
    msgs, rules, disc = engine.explain(lang, fl, d["product"])
    ev = engine.evidence(text, hidden[0]) if hidden else None
    pm = ml.p_misleading(text)
    return {
        "lang": lang,
        "product": d["product"], "product_name": engine.PRODUCT_NAME[lang][d["product"]],
        "terms": {"cash_price": price, "price_is_example": not d["cash_price"] and bool(d["example_price"]),
                  "n_installments": n, "installment_amount": d["installment_amount"], "admin_fee": d["admin_fee"],
                  "admin_fee_pct": d["admin_fee_pct"], "admin_fee_cap": d["admin_fee_cap"], "late_fee": d["late_fee"],
                  "profit_rate": rate, "rate_kind": d["rate_kind"], "rate_assumed": d["rate_assumed"],
                  "shariah_claim": d["shariah_claim"], "plans": plans},
        "also_seen": {"n_installments": c["n_installments"], "admin_fee": c["admin_fee"]},
        "cost": cost,
        "hidden_fee": None if not hidden else {"amount": hidden[0], "currency": hidden_cur[0], "promise": _loc(ev["claim"]), "fee": _loc(ev["fee"]), "same_line": ev["same_line"]},
        "flags": [{"code": code, "message": m} for (code, _), m in zip(fl, msgs)] if fl else [],
        "message_if_no_flag": None if fl else msgs[0],
        "sama": rules, "disclaimer": disc,
        "ml_p_misleading": pm,
        "ml_info": ml.info(),
        "verdict": _verdict(bool(hidden), pm, any(code == "zero_for_some_plans" for code, _ in fl)),
    }
