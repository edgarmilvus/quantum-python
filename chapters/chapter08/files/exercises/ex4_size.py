"""Exercise 4 (break): the size at which the transform stops fitting.

The dense matrix of the transform is 2^n squared complex numbers, and the circuit that
replaces it is quadratic in n. The exercise finds where the matrix stops fitting and
compares the two costs.

Run: python3 chapters/chapter08/files/exercises/ex4_size.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Dict, List

import qft

BYTES = 16
GIB = 1024**3


def matrix_bytes(n: int) -> int:
    if n < 1:
        raise ValueError(f"a transform needs at least one qubit, got {n}")
    side = 1 << n
    return side * side * BYTES


def first_above(limit_bytes: int, max_bits: int = 40) -> int:
    if limit_bytes <= 0:
        raise ValueError(f"a limit must be positive, got {limit_bytes}")
    for n in range(1, max_bits + 1):
        if matrix_bytes(n) > limit_bytes:
            return n
    raise ValueError(f"no size crosses {limit_bytes}")


def comparison(n: int) -> Dict[str, float]:
    return {
        "n": n,
        "matrix_gib": matrix_bytes(n) / GIB,
        "gates": qft.gate_count(n),
        "depth": qft.circuit_depth(n),
        "ratio": matrix_bytes(n) / (qft.gate_count(n) * BYTES),
    }


def checks(check: Callable[[bool, str], None]) -> None:
    check(matrix_bytes(4) == 16 * 16 * 16, "four qubits are 4 KiB")
    check(abs(matrix_bytes(10) / GIB - 0.015625) < 1e-9, "ten qubits are 16 MiB")
    check(abs(matrix_bytes(14) / GIB - 4.0) < 1e-9, "fourteen qubits are 4 GiB")
    check(abs(matrix_bytes(15) / GIB - 16.0) < 1e-9, "fifteen are exactly 16 GiB")

    check(first_above(4 * GIB) == 15, "the first size above 4 GiB is fifteen")
    check(first_above(16 * GIB) == 16, "the first above 16 GiB is sixteen")

    row = comparison(20)
    check(row["gates"] == 220, "twenty qubits are 220 gates")
    check(row["depth"] == 40, "and forty layers")
    check(row["ratio"] > 1e6, "the matrix is more than a million times the circuit")

    check(qft.gate_count(10) < 100, "ten qubits are under a hundred gates")
    check(qft.circuit_depth(10) == 20, "and twenty layers")

    try:
        matrix_bytes(0)
    except ValueError:
        check(True, "zero qubits are refused")
    else:
        check(False, "zero qubits are refused")

    try:
        first_above(0)
    except ValueError:
        check(True, "a zero limit is refused")
    else:
        check(False, "a zero limit is refused")

    check(matrix_bytes(2) * 4 == matrix_bytes(3), "each qubit quadruples the matrix")
    check(qft.gate_count(2) < qft.gate_count(3), "and adds linearly to the circuit")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
