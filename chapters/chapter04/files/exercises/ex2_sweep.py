"""Exercise 2 (extend): sweep the angles and find the settings that maximise S.

The chapter uses 0, 90, 45 and 135 because they are optimal. A reader who wants to
know why should measure it: sweep one angle and watch S fall away from 2.828.

Run: python3 chapters/chapter04/files/exercises/ex2_sweep.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List, Tuple

import bell


def s_for(b_angle: float, b_prime_angle: float, angle_a: float = 0.0, angle_a_prime: float = 90.0) -> float:
    """S for four angles, using the ideal cos(a - b) prediction."""
    values = {
        "ab": bell.predicted_expectation(angle_a, b_angle),
        "ab_prime": bell.predicted_expectation(angle_a, b_prime_angle),
        "a_prime_b": bell.predicted_expectation(angle_a_prime, b_angle),
        "a_prime_b_prime": bell.predicted_expectation(angle_a_prime, b_prime_angle),
    }
    return bell.chsh(values)


def sweep(step: float = 5.0) -> List[Tuple[float, float]]:
    """Every pair of angles on the grid, with its S."""
    out = []
    angle = 0.0
    while angle < 180.0:
        other = 0.0
        while other < 180.0:
            out.append((s_for(angle, other), angle, other))
            other += step
        angle += step
    return out


def best(step: float = 5.0) -> Tuple[float, float, float]:
    return max(sweep(step))


def checks(check: Callable[[bool, str], None]) -> None:
    check(abs(s_for(45, 135) - bell.TSIRELSON_BOUND) < 1e-12, "45 and 135 give the maximum")
    check(abs(s_for(0, 90) - 2.0) < 1e-12, "0 and 90 give exactly the classical bound")

    value, angle, other = best(step=15.0)
    check(abs(value - bell.TSIRELSON_BOUND) < 0.05, "the coarse grid finds the maximum within 0.05")
    check(0 <= angle < 180 and 0 <= other < 180, "the best angles are in range")

    degenerate = s_for(0, 0)
    check(abs(degenerate) < 1e-12, "identical settings give S = 0")

    check(s_for(45, 135) > s_for(40, 135), "moving away from 45 lowers S")
    check(s_for(45, 130) > s_for(45, 100), "moving the second angle away lowers S more")

    grid = sweep(step=30.0)
    check(len(grid) == 36, "a 30-degree grid over two angles has 36 points")
    check(max(g[0] for g in grid) <= bell.TSIRELSON_BOUND + 1e-12, "no setting beats Tsirelson")

    # The maximum is a pair of settings, not a single one: swapping b and b' breaks it.
    check(s_for(135, 45) < bell.CLASSICAL_BOUND, "swapping the two B settings destroys the violation")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
