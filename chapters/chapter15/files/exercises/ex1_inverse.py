"""Exercise 1 (repair): the overlap circuit without its inverse.

Run: python3 chapters/chapter15/files/exercises/ex1_inverse.py

The kernel is |<0|U(b)-dagger U(a)|0>|^2. Dropping the dagger gives
|<0|U(b) U(a)|0>|^2, which is not a fidelity: it is not symmetric in the two
points, it does not equal one on the diagonal, and the matrix it produces is not
a kernel.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List

import numpy as np

from qml import featuremap as fm


def run(ops) -> complex:
    state = fm.zero(2)
    for gate, wires, theta in ops:
        state = fm.apply(state, gate, wires, theta)
    return complex(state[0])


def kernel_without_inverse(a, b, reps: int = 3) -> float:
    """The defect: U(b) U(a), with the adjoint missing."""
    return float(abs(run(fm.ops_for(a, reps=reps) + fm.ops_for(b, reps=reps))) ** 2)


def kernel_with_inverse(a, b, reps: int = 3) -> float:
    return float(abs(run(fm.overlap_ops(a, b, reps=reps))) ** 2)


def matrix(kernel, points: List[tuple], reps: int = 3) -> np.ndarray:
    n = len(points)
    return np.array([[kernel(points[i], points[j], reps) for j in range(n)] for i in range(n)])


def checks(check: Callable[[bool, str], None]) -> None:
    a, b, c = (0.2, 0.7), (0.8, 0.3), (0.55, 0.1)

    good = [kernel_with_inverse(x, y) for x in (a, b, c) for y in (a, b, c)]
    check(abs(kernel_with_inverse(a, a) - 1.0) < 1e-12, "the correct kernel is one on the diagonal")
    check(abs(kernel_with_inverse(a, b) - kernel_with_inverse(b, a)) < 1e-12, "and symmetric")

    check(abs(kernel_without_inverse(a, a) - 1.0) > 1e-6, "the defect is not one on the diagonal")
    check(abs(kernel_without_inverse(a, b) - kernel_without_inverse(b, a)) > 1e-6,
          "and it is not symmetric")

    points = [a, b, c]
    broken = matrix(kernel_without_inverse, points)
    correct = matrix(kernel_with_inverse, points)
    check(not np.allclose(broken, broken.T), "the defect's matrix is not symmetric")
    check(abs(float(np.diag(broken).mean()) - 1.0) > 0.1, "its diagonal is far from one")
    check(abs(float(np.diag(correct).mean()) - 1.0) < 1e-12, "the correct diagonal is one")
    check(float(broken.max()) <= 1.0 + 1e-9, "neither matrix exceeds one, which is why the defect looks plausible")
    check(abs(broken[0, 1] - correct[0, 1]) > 0.05, "and the off-diagonal entries differ by more than 0.05")

    check(abs(kernel_without_inverse(a, a) - abs(run(fm.ops_for(a, reps=3) + fm.ops_for(a, reps=3))) ** 2) < 1e-12,
          "the defect is the square of a single amplitude, so it cannot be a kernel")
    check(len(good) == 9, "nine pairs were measured")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
