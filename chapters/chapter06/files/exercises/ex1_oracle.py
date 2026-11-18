"""Exercise 1 (repair): an oracle that flips the input instead of the output.

Two lines are swapped in the permutation builder, so the oracle maps |x, y> to
|x ^ f(y), y> — a function nobody asked for. Deutsch-Jozsa still returns a peak, still
returns "constant" or "balanced", and is wrong half the time.

Run: python3 chapters/chapter06/files/exercises/ex1_oracle.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import numpy as np

from algorithms import deutsch_jozsa, deutsch_jozsa_answer
from oracle import balanced, constant, distribution, hadamard_all, hadamard_inputs, in_phase_kickback_state


def oracle_wrong(f, n: int) -> np.ndarray:
    """The defect: the flip is applied to the input bits."""
    size = 1 << (n + 1)
    matrix = np.zeros((size, size), dtype=np.complex128)
    for x in range(1 << n):
        for y in (0, 1):
            matrix[((x ^ f(y)) << 1) | y, (x << 1) | y] = 1.0
    return matrix


def oracle_right(f, n: int) -> np.ndarray:
    """The repair: the flip is applied to the output bit."""
    size = 1 << (n + 1)
    matrix = np.zeros((size, size), dtype=np.complex128)
    for x in range(1 << n):
        for y in (0, 1):
            matrix[((x << 1) | (y ^ f(x))), (x << 1) | y] = 1.0
    return matrix


def run_with(oracle_matrix: np.ndarray, n: int):
    state = hadamard_all(in_phase_kickback_state(n), n)
    state = oracle_matrix @ state
    state = hadamard_inputs(state, n)
    return distribution(state, n)


def checks(check: Callable[[bool, str], None]) -> None:
    n = 2
    right = oracle_right(balanced(1, n), n)
    wrong = oracle_wrong(balanced(1, n), n)
    check(np.allclose(right.sum(axis=0), 1.0), "the repair is a permutation")
    check(np.allclose(wrong.sum(axis=0), 1.0), "the defect is a permutation too")

    good = run_with(right, n)
    bad = run_with(wrong, n)
    check(abs(max(good.values()) - 1.0) < 1e-12, "the repair gives a certain answer")
    check(deutsch_jozsa_answer(good) == "balanced", "and it is the right one")

    check(not np.allclose(right, wrong), "the two oracles differ")
    check(abs(bad[format(0, "02b")] - good[format(0, "02b")]) > 1e-6 or max(bad.values()) < 0.99,
          "the defect does not reproduce the repair")

    constant_right = run_with(oracle_right(constant(0), n), n)
    constant_wrong = run_with(oracle_wrong(constant(0), n), n)
    check(abs(constant_right["00"] - 1.0) < 1e-12, "a constant function on the repair gives 00")
    check(abs(max(constant_wrong.values()) - 1.0) < 1e-12, "the defect still gives a certain outcome")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
