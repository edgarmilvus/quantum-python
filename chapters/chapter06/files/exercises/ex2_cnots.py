"""Exercise 2 (extend): the same oracle built from CNOTs.

On hardware an oracle is a circuit, not a matrix. For a linear function the circuit is
one CNOT per set bit, from the input wire to the output wire, and this exercise checks
that the circuit form and the permutation form agree.

Run: python3 chapters/chapter06/files/exercises/ex2_cnots.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List

import numpy as np

from oracle import index, linear, permutation


def cnot_oracle(controls: List[int], n: int) -> np.ndarray:
    """A permutation that flips the output bit once per control wire."""
    if n < 1:
        raise ValueError(f"an oracle needs at least one input bit, got {n}")
    for control in controls:
        if not 0 <= control < n:
            raise ValueError(f"control {control} is outside {n} input bits")
    size = 1 << (n + 1)
    matrix = np.zeros((size, size), dtype=np.complex128)
    for x in range(1 << n):
        parity = 0
        for control in controls:
            parity ^= (x >> control) & 1
        for y in (0, 1):
            matrix[index(x, y ^ parity), index(x, y)] = 1.0
    return matrix


def controls_of(secret: int, n: int) -> List[int]:
    return [bit for bit in range(n) if secret >> bit & 1]


def matrix_of(secret: int, n: int) -> np.ndarray:
    """Independent construction: the truth table, not the wire list."""
    return permutation(linear(secret, n), n)


def checks(check: Callable[[bool, str], None]) -> None:
    for n in (2, 3, 4):
        for secret in range(1, 1 << n):
            circuit = cnot_oracle(controls_of(secret, n), n)
            table = matrix_of(secret, n)
            check(np.allclose(circuit, table), f"n={n} secret {secret}: circuit equals table")

    check(controls_of(5, 3) == [0, 2], "secret 101 uses controls 0 and 2")
    check(np.allclose(cnot_oracle([], 2), np.eye(8)), "no controls is the identity")

    try:
        cnot_oracle([3], 3)
    except ValueError:
        check(True, "a control outside the inputs is refused")
    else:
        check(False, "a control outside the inputs is refused")

    check(np.allclose(cnot_oracle([0, 0], 2), np.eye(8)), "two CNOTs from the same wire cancel")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
