"""Exercise 5, file 1 of 3: the pure part.

A gate list plus a wire becomes a matrix; a matrix plus a state becomes a state.
No backend, no printing, no random number generator, so it is testable by calling
it with a list of tuples.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np

from gates import CNOT, H, X, Y, Z, embed

MATRICES = {"H": H, "X": X, "Y": Y, "Z": Z}

Gate = Tuple[str, int]


def matrix(gates: Sequence[Gate], wires: int = 2) -> np.ndarray:
    """The product matrix of a gate list, applied left to right."""
    if wires < 1:
        raise ValueError(f"a register has at least one wire, got {wires}")
    total = np.eye(2**wires, dtype=np.complex128)
    for name, wire in gates:
        if name == "CNOT":
            if wires != 2:
                raise ValueError("CNOT in this exercise is defined for two wires")
            if wire != 0:
                raise ValueError(f"CNOT uses wire 0 as control, got {wire}")
            step = CNOT
        elif name in MATRICES:
            step = embed(MATRICES[name], wire, wires)
        else:
            raise ValueError(f"unknown gate {name!r}")
        total = step @ total
    return total


def final_state(gates: Sequence[Gate], wires: int = 2) -> np.ndarray:
    """Apply the gate list to |00...0>."""
    initial = np.zeros(2**wires, dtype=np.complex128)
    initial[0] = 1.0
    return matrix(gates, wires) @ initial


def probability_rows(state: np.ndarray) -> List[Tuple[str, float]]:
    """One row per index: label and probability."""
    vector = np.asarray(state, dtype=np.complex128)
    size = vector.size
    if size & (size - 1):
        raise ValueError(f"a state vector has a power-of-two length, got {size}")
    wires = size.bit_length() - 1
    return [
        (format(index, f"0{wires}b"), float(abs(amplitude) ** 2))
        for index, amplitude in enumerate(vector)
    ]
