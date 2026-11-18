"""Exercise 2 (extend): how many shots the fidelity is worth.

Run: python3 chapters/chapter20/files/exercises/ex2_shots.py

A fidelity computed from 2,048 shots is itself a measurement, and its error is the same
binomial error the book has used since chapter 5. Each of the three Pauli expectations
has a standard error of 1/sqrt(N), and because the ideal Bloch vector has unit length the
fidelity's error is 1/(2 sqrt(N)): one half of a percent of shots buys one point.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Tuple


def sigma(shots: int) -> float:
    if shots <= 0:
        raise ValueError(f"shots are positive, got {shots}")
    return 1.0 / (2.0 * math.sqrt(shots))


def shots_for(sigma_f: float) -> int:
    if sigma_f <= 0:
        raise ValueError(f"a sigma is positive, got {sigma_f}")
    return math.ceil(1.0 / (4.0 * sigma_f**2))


def interval(value: float, shots: int) -> Tuple[float, float]:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"a fidelity is in [0, 1], got {value}")
    error = sigma(shots)
    return (max(0.0, value - error), min(1.0, value + error))


def checks(check: Callable[[bool, str], None]) -> None:
    check(abs(sigma(2048) - 0.011049) < 1e-5, "2,048 shots give a sigma of 0.0110")
    check(abs(sigma(1024) - 0.015625) < 1e-6, "1,024 shots give 0.0156")
    check(abs(sigma(8192) - sigma(2048) / 2) < 1e-9, "four times the shots halve the error")
    check(shots_for(0.01) == 2500, "one percent needs 2,500 shots")
    check(shots_for(0.005) == 10000, "half a percent needs 10,000")
    check(abs(shots_for(sigma(2048)) - 2048) <= 1, "the two functions are inverses")

    low, high = interval(0.9558, 2048)
    check(abs(low - 0.94475) < 1e-4, "the interval starts at 0.9447")
    check(abs(high - 0.96685) < 1e-4, "and ends at 0.9669")
    check(low < 0.9558 < high, "the value is inside its own interval")

    check(abs((0.9558 - 0.9499) - 0.0059) < 1e-4, "the two corrected runs differ by 0.006")
    check(0.9558 - 0.9499 < sigma(2048), "which is inside one sigma")
    check(0.9558 - 0.4858 > 4 * sigma(2048), "and the control is more than forty sigmas away")

    for bad in (0, -1):
        try:
            sigma(bad)
        except ValueError:
            check(True, f"{bad} shots is refused")
        else:
            check(False, f"{bad} shots is refused")

    for bad in (0.0, -0.01):
        try:
            shots_for(bad)
        except ValueError:
            check(True, f"a sigma of {bad} is refused")
        else:
            check(False, f"a sigma of {bad} is refused")

    try:
        interval(1.2, 1024)
    except ValueError:
        check(True, "a fidelity outside [0, 1] is refused")
    else:
        check(False, "a fidelity outside [0, 1] is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
