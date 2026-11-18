"""Exercise 4 (break): how many shots for a five-degree angle.

The dashboard wants the Bloch angle to five degrees. Counting statistics put a
floor on that: the angle error scales as sqrt((1 - x^2) / n), so the shot count
follows from the precision, not from patience.

Run: python3 chapters/chapter02/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable

import numpy as np


def angle_sigma(angle_deg: float, shots: int) -> float:
    """The one-sigma error of a Ry angle measured from counts, in degrees."""
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    theta = math.radians(angle_deg)
    x = math.sin(theta)
    variance = 1.0 - x * x
    return math.degrees(math.sqrt(variance / shots))


def shots_for(angle_deg: float, precision_deg: float, sigma: int = 1) -> int:
    """Shots needed for `precision_deg` at `sigma` standard deviations."""
    if precision_deg <= 0:
        raise ValueError(f"precision must be positive, got {precision_deg}")
    if not 0 < angle_deg < 180:
        raise ValueError(f"angle must be inside (0, 180), got {angle_deg}")
    theta = math.radians(angle_deg)
    variance = 1.0 - math.sin(theta) ** 2
    return math.ceil(variance / (math.radians(precision_deg) / sigma) ** 2)


def check_angle(angle_deg: float, shots: int, seed: int) -> float:
    """Simulate the measurement and return the recovered angle."""
    theta = math.radians(angle_deg)
    p0 = math.cos(theta / 2) ** 2
    rng = np.random.default_rng(seed)
    ones = int((rng.random(shots) >= p0).sum())
    z = (shots - 2 * ones) / shots
    x = math.sqrt(max(0.0, 1.0 - z * z)) * (1 if angle_deg < 90 else 1)
    return math.degrees(math.atan2(x, z))


def checks(check: Callable[[bool, str], None]) -> None:
    check(shots_for(45, 5) == 66, "66 shots for five degrees at 45")
    check(shots_for(45, 1) == 1642, "1642 shots for one degree at 45")
    check(shots_for(80, 5) < shots_for(45, 5), "a state nearer the equator needs fewer shots")
    check(angle_sigma(45, 66) >= 5.0 * 0.95, "the sigma at the computed shot count is about five degrees")
    check(angle_sigma(45, 1000) < angle_sigma(45, 100), "more shots shrink the sigma")

    recovered = check_angle(45, 5000, seed=3)
    check(abs(recovered - 45) < 5, "5000 shots recover 45 degrees within five")

    try:
        shots_for(45, 0)
    except ValueError:
        check(True, "zero precision is refused")
    else:
        check(False, "zero precision is refused")

    try:
        angle_sigma(45, 0)
    except ValueError:
        check(True, "zero shots is refused")
    else:
        check(False, "zero shots is refused")

    check(shots_for(45, 5, sigma=2) > shots_for(45, 5, sigma=1), "a two-sigma bar needs four times the shots")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
