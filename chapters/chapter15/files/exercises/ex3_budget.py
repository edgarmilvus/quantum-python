"""Exercise 3 (measure): the number of points the budget buys.

Run: python3 chapters/chapter15/files/exercises/ex3_budget.py

A kernel matrix costs one circuit per pair, so the bill is quadratic in the points
before the classifier runs. The recorded run measured 0.298 seconds per circuit;
at that rate, the 600-second free tier buys forty-four training points and not
forty-five.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

SECONDS_PER_CIRCUIT = 17.0 / 57.0
ALLOWANCE = 600.0


def circuits(n_train: int, n_test: int) -> int:
    """The distinct pairs: symmetric inside the training block, rectangular across."""
    if n_train < 1 or n_test < 0:
        raise ValueError(f"a split needs a training set, got {n_train} and {n_test}")
    return n_train * (n_train + 1) // 2 + n_train * n_test


def plan(n_train: int, shots: int = 1024) -> Dict[str, float]:
    if shots < 1:
        raise ValueError(f"shots must be positive, got {shots}")
    pairs = circuits(n_train, n_train // 2)
    return {
        "pairs": pairs,
        "shots": pairs * shots,
        "seconds": pairs * SECONDS_PER_CIRCUIT,
        "hours": pairs * SECONDS_PER_CIRCUIT / 3600,
    }


def deepest(allowance: float = ALLOWANCE, limit: int = 500) -> int:
    """The largest training set whose matrix fits the allowance."""
    if allowance <= 0:
        raise ValueError(f"an allowance is positive, got {allowance}")
    best = 0
    for n in range(1, limit + 1):
        if plan(n)["seconds"] <= allowance:
            best = n
    if best == 0:
        raise ValueError(f"not even one point fits {allowance} seconds")
    return best


def checks(check: Callable[[bool, str], None]) -> None:
    check(circuits(6, 6) == 57, "the recorded run needed 57 circuits")
    check(circuits(1, 0) == 1, "one point is one pair")
    check(circuits(6, 0) == 21, "six training points are twenty-one pairs")
    check(abs(SECONDS_PER_CIRCUIT - 0.298) < 0.005, "the measured cost is 0.298 seconds a circuit")

    check(deepest() == 44, "the free tier buys forty-four training points")
    check(plan(44)["seconds"] <= ALLOWANCE, "whose matrix fits")
    check(plan(45)["seconds"] > ALLOWANCE, "and forty-five does not")

    small = plan(12)
    check(small["pairs"] == 150, "twelve training points are 150 pairs")
    check(abs(small["seconds"] - 44.7) < 1.0, "which is about forty-five seconds")
    check(small["hours"] < 0.02, "well under an hour")

    big = plan(1000)
    check(big["pairs"] == 1000500, "a thousand points are a million pairs")
    check(big["hours"] > 80, "which is more than eighty hours of runtime")

    check(plan(10)["seconds"] < plan(11)["seconds"], "the cost grows with the points")
    check(plan(20)["shots"] == plan(20)["pairs"] * 1024, "the shots are the pairs times the shot count")

    for bad in (0, -5):
        try:
            deepest(allowance=bad)
        except ValueError:
            check(True, f"an allowance of {bad} is refused")
        else:
            check(False, f"an allowance of {bad} is refused")

    try:
        circuits(0, 1)
    except ValueError:
        check(True, "a split with no training points is refused")
    else:
        check(False, "a split with no training points is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
