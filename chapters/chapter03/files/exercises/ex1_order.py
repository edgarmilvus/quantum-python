"""Exercise 1 (repair): a unitary built by applying the gates backwards.

A small simulator multiplies the matrices in the order the gates were written. The
result is still unitary, still normalized, and describes a different circuit, so
every downstream check passes and the answers are wrong.

Run: python3 chapters/chapter03/files/exercises/ex1_order.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List, Sequence, Tuple

import numpy as np

from circuit import Circuit, gate_matrix

Op = Tuple[str, int]


def unitary_wrong(ops: Sequence[Op]) -> np.ndarray:
    """The defect: right-multiply, so the first gate written ends up leftmost."""
    total = np.eye(2, dtype=np.complex128)
    for name, wire in ops:
        total = total @ gate_matrix(name)
    return total


def unitary_right(ops: Sequence[Op]) -> np.ndarray:
    """The repair: the first gate written is the last matrix applied."""
    circuit = Circuit(1)
    for name, wire in ops:
        circuit.add(name, wire)
    return circuit.unitary()


def checks(check: Callable[[bool, str], None]) -> None:
    h_then_x: List[Op] = [("h", 0), ("x", 0)]

    right = unitary_right(h_then_x)
    wrong = unitary_wrong(h_then_x)
    check(not np.allclose(right, wrong), "the two orders disagree")
    check(np.allclose(right.conj().T @ right, np.eye(2)), "the repaired unitary is unitary")
    check(np.allclose(wrong.conj().T @ wrong, np.eye(2)), "the defect is unitary too")

    # The repaired product equals X @ H, the mathematical reading of "H then X".
    check(np.allclose(right, gate_matrix("x") @ gate_matrix("h")), "H then X is X @ H")
    check(np.allclose(wrong, gate_matrix("h") @ gate_matrix("x")), "the defect computes H @ X")

    single: List[Op] = [("h", 0)]
    check(np.allclose(unitary_right(single), unitary_wrong(single)), "one gate cannot be reversed")

    identity: List[Op] = [("x", 0), ("x", 0)]
    check(np.allclose(unitary_right(identity), np.eye(2)), "X twice is the identity in both readings")

    three: List[Op] = [("h", 0), ("t", 0), ("h", 0)]
    check(np.allclose(unitary_right(three), gate_matrix("h") @ gate_matrix("t") @ gate_matrix("h")),
          "three gates reverse to H @ T @ H")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
