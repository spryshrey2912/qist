"""One function that does everything the Streamlit page does, but returns plain data (JSON-friendly) for the web API."""
import engine, ml

def _loc(t):
    return {"line": t[0], "start": t[1], "end": t[2]} if t else None

def compute_cost(price, n, inst=0.0, fee=0.0, rate=0.0, rate_kind="none", fee_pct=0.0, fee_cap=0.0):
    """The real cost, or None when the price or the number of instalments is missing."""
    r = engine.cost(float(price), int(n), float(inst), float(fee), float(rate), rate_kind, float(fee_pct), float(fee_cap))
    if r is None: return None
    r["fee_total"] = round(r["total_paid"] - r["instalment"] * int(n), 2)
    return r

def analyze(text, lang="en"):
    lang = "ar" if lang == "ar" else "en"
    c = engine.candidates(text); d = engine.defaults(c, text)
    plans = {int(k): v for k, v in d["plans"].items()}
    n, rate = int(d["n_installments"]), float(d["profit_rate"])
    if plans:                                                # same default plan choice as the Streamlit page
        n = n if n in plans else max(plans); rate = plans[n]
    price = float(d["cash_price"]) or float(d["example_price"])
    cost = compute_cost(price, n, d["installment_amount"], d["admin_fee"], rate, d["rate_kind"], d["admin_fee_pct"], d["admin_fee_cap"] or 0.0)
    fl = engine.flags(text, c)
    hidden = [dd["fee"] for code, dd in fl if code == "zero_but_fee"]
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
        "hidden_fee": None if not hidden else {"amount": hidden[0], "promise": _loc(ev["claim"]), "fee": _loc(ev["fee"]), "same_line": ev["same_line"]},
        "flags": [{"code": code, "message": m} for (code, _), m in zip(fl, msgs)] if fl else [],
        "message_if_no_flag": None if fl else msgs[0],
        "sama": rules, "disclaimer": disc,
        "ml_p_misleading": pm,
    }
