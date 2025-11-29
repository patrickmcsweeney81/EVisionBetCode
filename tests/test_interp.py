import sys
import os

# Ensure project root is on path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ev_arb_bot import neighbor_interp


def run_tests():
    # Empty map
    assert neighbor_interp({}, 1.0) == 0.0

    # Single neighbor (can't interpolate)
    m = {1.0: [0.6, 0.62, 0.61]}
    assert neighbor_interp(m, 1.0) == 0.0

    # Two neighbors with sufficient samples
    m2 = {
        1.0: [0.4, 0.42, 0.41],
        2.0: [0.6, 0.62, 0.61],
    }
    p = neighbor_interp(m2, 1.5)
    assert 0.0 < p < 1.0

    # Insufficient samples on one side
    m3 = {1.0: [0.4], 2.0: [0.6, 0.6, 0.6]}
    assert neighbor_interp(m3, 1.5) == 0.0

    print("All interpolation tests passed.")


if __name__ == '__main__':
    run_tests()
