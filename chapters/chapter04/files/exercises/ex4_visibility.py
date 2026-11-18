"""Exercise 4 (break): how much noise a Bell pair tolerates.

Mix the ideal pair with white noise and S falls linearly in the visibility. Find the
point where the margin disappears: below it, no number of shots can recover a
violation, because the state no longer has one.

Run: python3 chapters/chapter04/files/exercises/ex4_visibility.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List, Tuple

import bell

THRESHOLD_VISIBILITY = 1.0 / (2.0 * 0.7071067811865476)  # 1 / sqrt(2)


def s_for_visibility(visibility: float) -> float:
    """S of a Bell pair mixed with white noise at the given visibility."""
    if not 0.0 <= visibility <= 1.0:
        raise ValueError(f"visibility must be in [0, 1], got {visibility}")
    return visibility * bell.TSIRELSON_BOUND


def visibility_for(s_value: float) -> float:
    """The visibility that produces a given S."""
    if s_value < 0:
        raise ValueError(f"S cannot be negative here, got {s_value}")
    return s_value / bell.TSIRELSON_BOUND


def maximum_noise() -> float:
    """The largest white-noise fraction that still leaves a violation."""
    return 1.0 - THRESHOLD_VISIBILITY


def scan(step: float = 0.01) -> List[Tuple[float, float]]:
    out = []
    steps = int(round(1.0 / step))
    for index in range(steps + 1):
        visibility = round(index * step, 12)  # avoid 1.0000000000000002
        out.append((visibility, s_for_visibility(visibility)))
    return out


def checks(check: Callable[[bool, str], None]) -> None:
    check(abs(s_for_visibility(1.0) - bell.TSIRELSON_BOUND) < 1e-12, "full visibility gives the Tsirelson bound")
    check(abs(s_for_visibility(0.0)) < 1e-12, "zero visibility gives S = 0")

    threshold = visibility_for(bell.CLASSICAL_BOUND)
    check(abs(threshold - THRESHOLD_VISIBILITY) < 1e-12, "the threshold visibility is 1/sqrt(2)")
    check(abs(threshold - 0.70710678) < 1e-8, "which is 0.707")
    check(abs(maximum_noise() - 0.29289322) < 1e-8, "so 29.3% noise can be tolerated")

    check(s_for_visibility(threshold + 0.01) > bell.CLASSICAL_BOUND, "just above the threshold still violates")
    check(s_for_visibility(threshold - 0.01) < bell.CLASSICAL_BOUND, "just below it does not")

    grid = scan(step=0.05)
    check(len(grid) == 21, "the scan has 21 points")
    check(all(b <= bell.TSIRELSON_BOUND + 1e-12 for _, b in grid), "no point exceeds Tsirelson")

    check(abs(s_for_visibility(0.5) - 1.41421356) < 1e-8, "half visibility is below the bound")

    for bad in (-0.1, 1.5):
        try:
            s_for_visibility(bad)
        except ValueError:
            check(True, f"visibility {bad} is refused")
        else:
            check(False, f"visibility {bad} is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
