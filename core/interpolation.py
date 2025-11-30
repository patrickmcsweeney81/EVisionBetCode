from typing import List, Tuple, Optional
import numpy as np

def interpolate_odds(points: List[Tuple[float, float]], target: float) -> Optional[float]:
    """
    Linearly interpolate (or extrapolate) decimal odds for a target line value.
    Args:
        points: List of (line, odds) tuples, e.g. [(24.5, 3.3), (25.5, 3.0), ...]
        target: The line value to estimate odds for, e.g. 29.5
    Returns:
        Interpolated odds (float), or None if not enough points
    """
    if not points or len(points) < 2:
        return None
    # Sort by line value
    points = sorted(points)
    lines, odds = zip(*points)
    # Use numpy interp for linear interpolation/extrapolation
    return float(np.interp(target, lines, odds))
