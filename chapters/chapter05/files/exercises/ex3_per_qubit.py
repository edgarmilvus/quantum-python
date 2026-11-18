"""Exercise 3 (measure): the readout error, per qubit, from the matrix.

The calibration file has four preparations. A reader can read the 4x4 matrix, but a
budget needs two numbers: how wrong is qubit 0, and how wrong is qubit 1.

Run: python3 chapters/chapter05/files/exercises/ex3_per_qubit.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import numpy as np

import calibrate


def per_qubit_error(matrix: np.ndarray) -> Dict[str, float]:
    """Each qubit's error, read from the rows where the other qubit is 0.

    Rows are prepared states in the order 00, 01, 10, 11. Row 01 prepares qubit 1 (the
    high bit of the key) and leaves qubit 0 at zero, so the probability that qubit 0
    flips is the mass that moves out of that row into 00 and 11.
    """
    if matrix.shape != (4, 4):
        raise ValueError(f"a two-qubit matrix is 4x4, got {matrix.shape}")
    # Row "01" prepares qubit 0 at one; its flip lands in columns 00 and 10.
    # Row "10" prepares qubit 1 at one; its flip lands in columns 00 and 01.
    return {
        "qubit_0": float(matrix[1, 0] + matrix[1, 2]),
        "qubit_1": float(matrix[2, 0] + matrix[2, 1]),
    }


def both_wrong(matrix: np.ndarray) -> float:
    """The mass that moves two bits at once, which a per-qubit model cannot explain."""
    return float(matrix[0, 3] + matrix[3, 0])


def checks(check: Callable[[bool, str], None]) -> None:
    record = calibrate.load()
    matrix = calibrate.matrix(record)
    errors = per_qubit_error(matrix)

    check(set(errors) == {"qubit_0", "qubit_1"}, "two numbers come out")
    check(0.0 < errors["qubit_0"] < 0.1, "qubit 0 is wrong less than 10% of the time")
    check(0.0 < errors["qubit_1"] < 0.1, "qubit 1 is wrong less than 10% of the time")
    check(abs(errors["qubit_0"] - 0.0324) < 0.005, "qubit 0 is about 3.2%")
    check(abs(errors["qubit_1"] - 0.0344) < 0.005, "qubit 1 is about 3.4%")

    check(both_wrong(matrix) < 0.005, "both bits flip together less than half a percent of the time")
    check(calibrate.diagonal_error(matrix) > max(errors.values()),
          "the average over four preparations is worse than either single qubit")

    try:
        per_qubit_error(np.eye(2))
    except ValueError:
        check(True, "a 2x2 matrix is refused")
    else:
        check(False, "a 2x2 matrix is refused")

    identity = np.eye(4)
    check(all(value == 0.0 for value in per_qubit_error(identity).values()),
          "a perfect matrix has no error")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
