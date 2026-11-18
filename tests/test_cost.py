import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
from cost import true_cost


def test_zero_interest_no_fee():
    r = true_cost(1200, 300, 4)
    assert r["extra_cost"] == 0 and r["effective_annual_rate"] == 0


def test_hidden_admin_fee():
    # "0% interest" but SAR 50 fee: you pay 50 extra
    r = true_cost(1200, 300, 4, upfront_fees=50)
    assert r["total_paid"] == 1250 and r["extra_cost"] == 50
    assert r["effective_annual_rate"] > 0


def test_known_rate():
    # 1000 financed, 12 x 88.85 is about 1% per month -> about 12.7% a year
    r = true_cost(1000, 88.85, 12)
    assert abs(r["effective_annual_rate"] - 12.68) < 0.1

if __name__ == "__main__":
    test_zero_interest_no_fee(); test_hidden_admin_fee(); test_known_rate(); print("all pass")
