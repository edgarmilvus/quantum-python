"""Exercise 2 (extend): measure the coverage instead of trusting the formula.

A 95% interval should contain the truth 95% of the time. Simulating that is the only
way to know whether the implementation, not the formula, is right.

Run: python3 chapters/chapter05/files/exercises/ex2_coverage.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import numpy as np

from stats import wilson


def coverage(shots: int, true_p: float = 0.5, trials: int = 2000, seed: int = 1, z: float = 1.96) -> float:
    """The fraction of simulated intervals that contain the true probability."""
    if shots <= 0 or trials <= 0:
        raise ValueError("shots and trials must be positive")
    if not 0.0 < true_p < 1.0:
        raise ValueError(f"true_p must be strictly inside (0, 1), got {true_p}")
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(trials):
        count = int(rng.binomial(shots, true_p))
        low, high = wilson(count, shots, z)
        if low <= true_p <= high:
            hits += 1
    return hits / trials


def coverage_table(shots_list, numbers=(0.5, 0.9), trials=2000, seed=1) -> Dict[tuple, float]:
    return {(shots, p): coverage(shots, p, trials, seed) for shots in shots_list for p in numbers}


def checks(check: Callable[[bool, str], None]) -> None:
    for shots in (20, 100, 1000):
        value = coverage(shots, trials=1000)
        check(0.92 < value < 0.98, f"{shots} shots cover the truth between 92% and 98%")

    check(abs(coverage(1000, seed=1) - coverage(1000, seed=1)) < 1e-12,
          "the same seed reproduces the coverage")

    table = coverage_table([100, 1000], trials=500)
    check(len(table) == 4, "the table has one entry per size and probability")
    check(all(0.9 < value < 0.99 for value in table.values()), "every cell covers about 95%")

    check(coverage(100, true_p=0.9, trials=1000) > 0.9, "a skewed probability is also covered")

    for bad in ((0, 100), (100, 0)):
        try:
            coverage(*bad)
        except ValueError:
            check(True, f"coverage{bad} is refused")
        else:
            check(False, f"coverage{bad} is refused")

    try:
        coverage(100, true_p=0.0)
    except ValueError:
        check(True, "a probability of zero is refused")
    else:
        check(False, "a probability of zero is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
