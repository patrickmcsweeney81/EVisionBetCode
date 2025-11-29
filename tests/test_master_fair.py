import sys
import os

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ev_arb_bot import master_fair_odds


def approx_equal(a, b, tol=1e-6):
    return abs(a - b) <= tol


def run_tests():
    # Case 1: only pinnacle
    r1 = {"pinnacle": 2.0}
    out1 = master_fair_odds(r1)
    assert approx_equal(out1, 2.0), f"expected 2.0, got {out1}"

    # Case 2: pinnacle + median equal
    r2 = {"pinnacle": 2.0, "median": 2.0}
    out2 = master_fair_odds(r2)
    assert approx_equal(out2, 2.0), f"expected 2.0, got {out2}"

    # Case 3: only median
    r3 = {"median": 1.25}
    out3 = master_fair_odds(r3)
    assert approx_equal(out3, 1.25), f"expected 1.25, got {out3}"

    # Case 4: empty -> 0.0
    r4 = {}
    out4 = master_fair_odds(r4)
    assert approx_equal(out4, 0.0), f"expected 0.0, got {out4}"

    print("All master_fair_odds tests passed.")


if __name__ == '__main__':
    run_tests()
