"""Cost engine: plain Python, no AI. Maths should be exact, not guessed."""


def true_cost(cash_price, installment_amount, n_installments, upfront_fees=0.0):
    """Return total paid, extra cost (SAR) and effective annual rate (%).

    Assumes monthly installments, first one paid a month after purchase,
    and any admin/processing fee paid on day 0.
    """
    total_paid = installment_amount * n_installments + upfront_fees
    extra = total_paid - cash_price
    return {
        "total_paid": round(total_paid, 2),
        "extra_cost": round(extra, 2),
        "effective_annual_rate": round(_annual_rate(cash_price, installment_amount,
                                                    n_installments, upfront_fees), 2),
    }


def _annual_rate(price, inst, n, fees):
    financed = price - fees  # money you really get use of on day 0
    if financed <= 0 or inst * n <= financed:
        return 0.0
    lo, hi = 0.0, 1.0  # monthly rate bounds, found by bisection
    for _ in range(200):
        mid = (lo + hi) / 2
        pv = sum(inst / (1 + mid) ** k for k in range(1, n + 1))
        if pv > financed:
            lo = mid
        else:
            hi = mid
    return ((1 + lo) ** 12 - 1) * 100
