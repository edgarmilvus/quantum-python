"""Exercise 1 (repair): the diffusion applied before the oracle.

The two operators do not commute. Swapping them still produces a unitary circuit, still
produces a peak, and rotates in the wrong direction: at three qubits two iterations give
the marked item 0.012 instead of 0.945.

Run: python3 chapters/chapter07/files/exercises/ex1_order.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import numpy as np

import grover


def steps_wrong(marked: int, n: int, count: int) -> np.ndarray:
    """The defect: mirror first, then flip."""
    state = grover.uniform(n)
    flip = grover.oracle(marked, n)
    mirror = grover.diffusion(n)
    for _ in range(count):
        state = flip @ (mirror @ state)
    return state


def steps_right(marked: int, n: int, count: int) -> np.ndarray:
    return grover.iterate(marked, n, count)


def probability(state: np.ndarray, index: int) -> float:
    return float(np.abs(state[index]) ** 2)


def checks(check: Callable[[bool, str], None]) -> None:
    n, marked = 3, 5

    right = probability(steps_right(marked, n, 2), marked)
    wrong = probability(steps_wrong(marked, n, 2), marked)

    check(abs(right - 0.9453125) < 1e-9, "the repair gives 0.9453 after two iterations")
    check(abs(wrong - 0.78125) < 1e-9, "the defect gives 0.7813: one iteration behind")
    check(abs(right - wrong) > 0.15, "the two differ by more than fifteen points")

    check(abs(probability(steps_wrong(marked, n, 1), marked) - 0.125) < 1e-9,
          "one wrong iteration returns to the uniform state exactly")
    check(np.allclose(grover.probabilities(steps_wrong(marked, n, 2)),
                      grover.probabilities(steps_right(marked, n, 1))),
          "two wrong iterations equal one correct one")
    check(np.allclose(grover.probabilities(steps_wrong(marked, n, 3)),
                      grover.probabilities(steps_right(marked, n, 2))),
          "and three wrong iterations equal two correct ones")

    check(np.allclose(steps_wrong(marked, n, 0), steps_right(marked, n, 0)),
          "with no iterations the two agree")

    check(abs(probability(steps_right(marked, n, 0), marked) - 0.125) < 1e-12,
          "with no iterations the marked item is at one eighth")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
