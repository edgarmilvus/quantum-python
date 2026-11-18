"""Exercise 1 (repair): intervals that leave the unit interval.

A dashboard reports p ± 1.96 sqrt(p(1-p)/n). At the edges the interval goes negative or
above one, and a reader who sees "-4% converted" stops trusting the whole report.

Run: python3 chapters/chapter05/files/exercises/ex1_edges.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Tuple

from stats import wilson


def normal_interval(count: int, shots: int, z: float = 1.96) -> Tuple[float, float]:
    """The defect: symmetric, unbounded, and wrong at the edges."""
    p = count / shots
    half = z * math.sqrt(p * (1 - p) / shots)
    return p - half, p + half


def repaired(count: int, shots: int, z: float = 1.96) -> Tuple[float, float]:
    return wilson(count, shots, z)


def checks(check: Callable[[bool, str], None]) -> None:
    low_bad, high_bad = normal_interval(1, 20)
    check(low_bad < 0, "the defective lower bound is negative at one success in twenty")
    check(normal_interval(0, 20) == (0.0, 0.0), "at zero successes the defect claims certainty")

    low_ok, high_ok = repaired(1, 20)
    check(low_ok > 0, "the repaired lower bound stays above zero")
    check(high_ok > 0.2, "and the upper bound is honest about the uncertainty")

    check(normal_interval(19, 20)[1] > 1.0, "the defect exceeds one at nineteen of twenty")
    check(repaired(19, 20)[1] < 1.0, "the repair keeps nineteen of twenty below certainty")
    check(repaired(20, 20)[1] == 1.0, "and reaches exactly one only at all successes")

    check(abs(normal_interval(5000, 10000)[0] - repaired(5000, 10000)[0]) < 0.002,
          "in the middle the two agree to two points")
    check(repaired(0, 1000)[1] < 0.01, "a thousand shots with no successes still bound it tightly")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
