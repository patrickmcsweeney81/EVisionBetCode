import sys
import os

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.fair_prices import master_fair_odds


def approx_equal(a, b, tol=1e-6):
    return abs(a - b) <= tol


def run_tests():
    # Case 1: only Pinnacle
    out1 = master_fair_odds(2.0, None, [])
    assert approx_equal(out1, 2.0), f"expected 2.0, got {out1}"

    # Case 2: Pinnacle + other sharps median equal
    out2 = master_fair_odds(2.0, None, [2.0, 2.0])
    assert approx_equal(out2, 2.0), f"expected 2.0, got {out2}"

    # Case 3: only other sharps (median)
    out3 = master_fair_odds(None, None, [1.25, 1.25])
    assert approx_equal(out3, 1.25), f"expected 1.25, got {out3}"

    # Case 4: empty inputs -> 0.0
    out4 = master_fair_odds(None, None, [])
    assert approx_equal(out4, 0.0), f"expected 0.0, got {out4}"

    print("All master_fair_odds tests passed.")


if __name__ == '__main__':
    run_tests()
