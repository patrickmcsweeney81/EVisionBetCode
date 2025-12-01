
import pytest
from core.fair_prices import master_fair_odds

def approx_equal(a, b, tol=1e-6):
    return abs(a - b) <= tol

def test_master_fair_odds_only_pinnacle():
    out = master_fair_odds(2.0, None, [])
    assert approx_equal(out, 2.0)

def test_master_fair_odds_pinnacle_and_sharps():
    out = master_fair_odds(2.0, None, [2.0, 2.0])
    assert approx_equal(out, 2.0)

def test_master_fair_odds_only_sharps():
    out = master_fair_odds(None, None, [1.25, 1.25])
    assert approx_equal(out, 1.25)

def test_master_fair_odds_empty():
    out = master_fair_odds(None, None, [])
    assert approx_equal(out, 0.0)
