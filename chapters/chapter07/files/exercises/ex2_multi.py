"""Exercise 2 (extend): several marked items.

With M marked items out of N the rotation angle grows, sin(theta) = sqrt(M/N), so fewer
iterations are needed and the ceiling is lower. The exercise extends the search and checks
the formula against the simulation.

Run: python3 chapters/chapter07/files/exercises/ex2_multi.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, List

import numpy as np

import grover


def oracle_multi(marked: List[int], n: int) -> np.ndarray:
    size = 1 << n
    diagonal = np.ones(size, dtype=np.complex128)
    for item in marked:
        if not 0 <= item < size:
            raise ValueError(f"marked item {item} is outside [0, {size - 1}]")
        diagonal[item] = -1.0
    return np.diag(diagonal)


def run_multi(marked: List[int], n: int, steps: int) -> np.ndarray:
    state = grover.uniform(n)
    flip = oracle_multi(marked, n)
    mirror = grover.diffusion(n)
    for _ in range(steps):
        state = mirror @ (flip @ state)
    return state


def success_multi(marked: List[int], n: int, steps: int) -> float:
    probabilities = np.abs(run_multi(marked, n, steps)) ** 2
    return float(sum(probabilities[item] for item in marked))


def theta_multi(size: int, count: int) -> float:
    if count < 1:
        raise ValueError(f"at least one item must be marked, got {count}")
    if count > size:
        raise ValueError(f"{count} marked items do not fit in {size}")
    return math.asin(math.sqrt(count / size))


def optimal_multi(size: int, count: int) -> int:
    return max(1, int(round(math.pi / (4 * theta_multi(size, count)) - 0.5)))


def checks(check: Callable[[bool, str], None]) -> None:
    n, size = 3, 8

    one = success_multi([5], n, grover.optimal_iterations(size))
    check(abs(one - 0.9453125) < 1e-9, "one marked item reproduces the single-item result")

    two = success_multi([1, 5], n, optimal_multi(size, 2))
    check(abs(two - 1.0) < 1e-9, "two marked items are certain at their optimum")
    check(optimal_multi(size, 2) < optimal_multi(size, 1), "and need fewer iterations")

    half = success_multi([1, 3, 5, 7], n, 1)
    check(abs(half - 0.5) < 1e-9, "half the items marked gives one half after one iteration")

    check(abs(theta_multi(8, 1) - math.asin(math.sqrt(1 / 8))) < 1e-12, "the angle uses sqrt(M/N)")

    try:
        optimal_multi(8, 0)
    except ValueError:
        check(True, "zero marked items are refused")
    else:
        check(False, "zero marked items are refused")

    try:
        optimal_multi(8, 9)
    except ValueError:
        check(True, "more marked items than items is refused")
    else:
        check(False, "more marked items than items is refused")

    try:
        oracle_multi([9], 3)
    except ValueError:
        check(True, "a marked item outside the register is refused")
    else:
        check(False, "a marked item outside the register is refused")

    check(np.allclose(oracle_multi([1, 3], 3) @ oracle_multi([1, 3], 3), np.eye(8)),
          "the multi oracle is its own inverse")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
