"""Density matrices, gates, and the three numbers a state has to report.

A density matrix is what a noisy circuit produces, because noise turns a pure
state into a mixture. Everything here is small on purpose: the chapter never
needs more than four wires, so a matrix is at most 16 by 16 and every operation
is a multiplication a reader can check by hand.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Sequence, Tuple

import numpy as np

Matrix = np.ndarray
Op = Tuple[str, Tuple[int, ...], "float | None"]


# -- gates ---------------------------------------------------------------
def _gate(name: str, theta: "float | None" = None) -> Matrix:
    """The 2x2 or 4x4 matrix of one gate, in the book's convention."""
    if name == "h":
        return np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
    if name == "x":
        return np.array([[0, 1], [1, 0]], dtype=complex)
    if name == "y":
        return np.array([[0, -1j], [1j, 0]], dtype=complex)
    if name == "z":
        return np.array([[1, 0], [0, -1]], dtype=complex)
    if name == "s":
        return np.array([[1, 0], [0, 1j]], dtype=complex)
    if name == "t":
        return np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=complex)
    if name in ("rx", "ry", "rz"):
        if theta is None:
            raise ValueError(f"{name} needs an angle")
        half = theta / 2
        cos, sin = np.cos(half), np.sin(half)
        if name == "rx":
            return np.array([[cos, -1j * sin], [-1j * sin, cos]], dtype=complex)
        if name == "ry":
            return np.array([[cos, -sin], [sin, cos]], dtype=complex)
        return np.array([[np.exp(-1j * half), 0], [0, np.exp(1j * half)]], dtype=complex)
    if name in ("cx", "cnot"):
        return np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex
        )
    if name == "cz":
        return np.diag([1, 1, 1, -1]).astype(complex)
    raise ValueError(f"unknown gate {name!r}")


def full(matrix: Matrix, wires: Sequence[int], n: int) -> Matrix:
    """Lift a gate on `wires` to the whole register of `n` wires.

    The gate's own matrix uses `wires[0]` as its most significant bit, so the
    common gates keep their textbook form. The lifted operator uses wire 0 as
    the least significant bit of the basis index, which is the convention the
    book's counts use (`00` is 0, `11` is 3). The wires the gate does not touch
    are carried through unchanged, which is what makes the lift block-diagonal.
    """
    width = int(round(np.log2(matrix.shape[0])))
    if width != len(wires):
        raise ValueError(f"{matrix.shape[0]}x{matrix.shape[0]} does not fit {wires}")
    if len(set(wires)) != len(wires) or any(not 0 <= w < n for w in wires):
        raise ValueError(f"wires {wires} are not distinct wires of {n}")
    untouched = [wire for wire in range(n) if wire not in wires]

    def gate_index(full: int) -> int:
        index = 0
        for position, wire in enumerate(wires):
            index |= ((full >> wire) & 1) << (width - 1 - position)
        return index

    def rest(full: int) -> int:
        value = 0
        for position, wire in enumerate(untouched):
            value |= ((full >> wire) & 1) << position
        return value

    operator = np.zeros((2 ** n, 2 ** n), dtype=complex)
    for row in range(2 ** n):
        for column in range(2 ** n):
            if rest(row) != rest(column):
                continue
            operator[row, column] = matrix[gate_index(row), gate_index(column)]
    return operator


# -- states --------------------------------------------------------------
def zero(n: int) -> Matrix:
    """|0...0><0...0| on n wires."""
    if n < 1:
        raise ValueError(f"a state has at least one wire, got {n}")
    rho = np.zeros((2 ** n, 2 ** n), dtype=complex)
    rho[0, 0] = 1.0
    return rho


def ket(n: int, index: int) -> Matrix:
    """|index><index|, with wire 0 as the least significant bit."""
    if not 0 <= index < 2 ** n:
        raise ValueError(f"{index} is not a basis state of {n} wires")
    rho = np.zeros((2 ** n, 2 ** n), dtype=complex)
    rho[index, index] = 1.0
    return rho


def apply(rho: Matrix, matrix: Matrix, wires: Sequence[int], n: int) -> Matrix:
    """rho -> U rho U-dagger for a gate on `wires`."""
    operator = full(matrix, wires, n)
    return operator @ rho @ operator.conj().T


def probabilities(rho: Matrix) -> np.ndarray:
    """The diagonal, which is the distribution a computational measurement sees."""
    values = np.array(np.real(np.diag(rho)), dtype=float)
    values[np.abs(values) < 1e-15] = 0.0
    return values / values.sum()


def purity(rho: Matrix) -> float:
    """Tr(rho^2): 1 for a pure state, 1/d for the maximally mixed one."""
    return float(np.real(np.trace(rho @ rho)))


def coherence(rho: Matrix, i: int, j: int) -> float:
    """|rho_ij|: how much of the superposition survives between two levels."""
    return float(abs(rho[i, j]))


def labels(n: int) -> List[str]:
    """The basis strings in counting order, wire 0 rightmost, as Qiskit prints them."""
    return [format(index, f"0{n}b") for index in range(2 ** n)]


def fidelity_to(rho: Matrix, index: int) -> float:
    """<index|rho|index>, the population of one basis state."""
    return float(np.real(rho[index, index]))


def bloch(rho: Matrix) -> Tuple[float, float, float]:
    """The Bloch vector of a one-qubit state (x, y, z)."""
    if rho.shape != (2, 2):
        raise ValueError("the Bloch vector is defined for one wire")
    x = 2 * float(np.real(rho[0, 1]))
    y = -2 * float(np.imag(rho[0, 1]))
    z = float(np.real(rho[0, 0] - rho[1, 1]))
    return x, y, z


def trace_distance(a: Matrix, b: Matrix) -> float:
    """Half the trace norm of the difference: 0 equal, 1 orthogonal."""
    difference = a - b
    values = np.linalg.eigvalsh(difference)
    return float(0.5 * np.abs(values).sum())


def paulis(n: int) -> List[Tuple[str, Matrix]]:
    """The 4^n Pauli strings on n wires, identity first."""
    single = [
        ("I", np.eye(2, dtype=complex)),
        ("X", np.array([[0, 1], [1, 0]], dtype=complex)),
        ("Y", np.array([[0, -1j], [1j, 0]], dtype=complex)),
        ("Z", np.array([[1, 0], [0, -1]], dtype=complex)),
    ]
    out: List[Tuple[str, Matrix]] = []
    for names in itertools.product(single, repeat=n):
        label = "".join(name for name, _ in names)
        matrix = names[0][1]
        for _, factor in names[1:]:
            matrix = np.kron(matrix, factor)
        out.append((label, matrix))
    return out
