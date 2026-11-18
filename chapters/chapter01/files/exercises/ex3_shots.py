"""Exercise 3 (measure): how many shots before an estimate is worth printing.

A report quotes P(0)=0.5 from 20 shots. The reviewer asks for the error bar, and
the bar turns out to be five times the effect being claimed.

Run: python3 chapters/chapter01/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Tuple

Z95 = 1.959963984540054


def shots_for(precision: float, p: float = 0.5, z: float = Z95) -> int:
    """Shots needed for a half-width of `precision` around p, at confidence z."""
    if not 0.0 < p < 1.0:
        raise ValueError(f"p must be strictly inside (0, 1), got {p}")
    if precision <= 0.0:
        raise ValueError(f"precision must be positive, got {precision}")
    return math.ceil(p * (1.0 - p) * (z / precision) ** 2)


def wilson_interval(k: int, n: int, z: float = Z95) -> Tuple[float, float]:
    """The Wilson score interval for k successes in n shots."""
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    if not 0 <= k <= n:
        raise ValueError(f"k must be inside [0, {n}], got {k}")
    p = k / n
    denominator = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    # Clip to the unit interval, and snap values that are one ulp away from a
    # boundary so an all-successes interval reports exactly 1.0.
    low = max(0.0, centre - half)
    high = min(1.0, centre + half)
    if low < 1e-12:
        low = 0.0
    if high > 1.0 - 1e-12:
        high = 1.0
    return low, high


def interval_width(k: int, n: int, z: float = Z95) -> float:
    low, high = wilson_interval(k, n, z)
    return high - low


def checks(check: Callable[[bool, str], None]) -> None:
    check(shots_for(0.05) == 385, "5 points of precision needs 385 shots")
    check(shots_for(0.01) == 9604, "1 point of precision needs 9604 shots")
    check(shots_for(0.05, p=0.9) < shots_for(0.05, p=0.5), "a skewed distribution needs fewer shots")

    low, high = wilson_interval(5000, 10000)
    check(low < 0.5 < high, "the interval contains the estimate")
    check(abs(low - 0.4902) < 0.001, "the lower bound is 0.490 at 10k shots")
    check(abs(high - 0.5098) < 0.001, "the upper bound is 0.510 at 10k shots")
    check(interval_width(50, 100) > interval_width(5000, 10000), "fewer shots widen the interval")
    check(wilson_interval(0, 10)[0] == 0.0, "zero successes cannot have a negative bound")
    check(wilson_interval(10, 10)[1] == 1.0, "all successes cannot exceed one")

    try:
        shots_for(0.0)
    except ValueError:
        check(True, "zero precision is refused")
    else:
        check(False, "zero precision is refused")

    try:
        wilson_interval(11, 10)
    except ValueError:
        check(True, "more successes than shots is refused")
    else:
        check(False, "more successes than shots is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
