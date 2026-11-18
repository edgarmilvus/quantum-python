"""H2 at equilibrium in STO-3G, reduced to two qubits, and one knob.

The Hamiltonian is five Pauli terms plus a nuclear constant. The ansatz is three gates.
Everything here is exact arithmetic until the section on shots.
"""

from __future__ import annotations

import cmath
import math
from typing import Dict, List, Tuple

import numpy as np

I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)

PAULI = {"I": I2, "X": X, "Y": Y, "Z": Z}

# STO-3G at 0.735 A, parity mapping with two-qubit reduction. Qollab's table,
# which reproduces the PySCF and qiskit-nature rows.
TERMS: Dict[str, float] = {
    "II": -1.052373,
    "IZ": 0.397937,
    "ZI": -0.397937,
    "ZZ": -0.011280,
    "XX": 0.180931,
}
NUCLEAR = 0.719969
CHEMICAL_ACCURACY = 1.6e-3  # hartree
HARTREE_TO_KCAL = 627.509474


def operator(label: str) -> np.ndarray:
    """A two-qubit Pauli string.

    The published table names qubit 1 first and qubit 0 second, so "IZ" is Z on qubit 0.
    The label is reversed here because this module's kron puts qubit 0 first; getting the
    order wrong swaps IZ with ZI and moves the Hartree-Fock energy by 0.8 hartree.
    """
    if len(label) != 2:
        raise ValueError(f"a two-qubit label has two letters, got {label!r}")
    matrix = np.eye(1, dtype=np.complex128)
    for letter in reversed(label):
        if letter not in PAULI:
            raise ValueError(f"unknown Pauli letter {letter!r}")
        matrix = np.kron(matrix, PAULI[letter])
    return matrix


def hamiltonian() -> np.ndarray:
    """The electronic Hamiltonian, four by four."""
    total = np.zeros((4, 4), dtype=np.complex128)
    for label, coefficient in TERMS.items():
        total += coefficient * operator(label)
    return total


def total_with_nuclear() -> np.ndarray:
    return hamiltonian() + NUCLEAR * np.eye(4)


def exact_energies() -> np.ndarray:
    return np.linalg.eigvalsh(total_with_nuclear())


def exact_ground() -> float:
    return float(exact_energies()[0])


# -- the ansatz ---------------------------------------------------------
def ansatz_state(theta: float) -> np.ndarray:
    """X on qubit 0, Ry on qubit 1, CNOT from 1 to 0, applied to |00>.

    Qubit 0 is the left factor, so the Hartree-Fock string |01> is the index 1: qubit 0
    is zero and qubit 1 is one, which is both electrons in the lower orbital.
    """
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    # |00> -> |10>: flip qubit 0, which writes the Hartree-Fock string |10>.
    # Ry on qubit 1 mixes |10> with |11>, and the CNOT sends that part to |01>,
    # so the state is sin(t/2)|01> + cos(t/2)|10> in the index order (q0 q1).
    return np.array([0.0, s, c, 0.0], dtype=np.complex128)


def energy(theta: float) -> float:
    """The exact expectation of the total Hamiltonian in the ansatz state."""
    state = ansatz_state(theta)
    return float(np.real(np.vdot(state, total_with_nuclear() @ state)))


def best_angle(lo: float = -math.pi, hi: float = math.pi, steps: int = 200_000) -> Tuple[float, float]:
    """The minimum on a fine grid, which is the reference the optimiser is checked against."""
    if lo >= hi:
        raise ValueError(f"the interval is empty: {lo} >= {hi}")
    angles = np.linspace(lo, hi, steps)
    values = [energy(float(a)) for a in angles]
    index = int(np.argmin(values))
    return float(angles[index]), float(values[index])


def analytic_minimum() -> Tuple[float, float, float]:
    """The exact minimum over the ansatz, by projecting the Hamiltonian.

    The ansatz spans a two-dimensional subspace, so the best energy it can reach is the
    lowest eigenvalue of the Hamiltonian restricted to that subspace — no optimiser and
    no grid. The angle is read from the eigenvector.
    """
    h = total_with_nuclear()
    s0 = ansatz_state(0.0)
    s1 = ansatz_state(math.pi / 2)
    v0 = s0 / np.linalg.norm(s0)
    v1 = s1 - np.vdot(v0, s1) * v0
    v1 = v1 / np.linalg.norm(v1)
    basis = np.column_stack([v0, v1])
    projected = basis.conj().T @ h @ basis
    values, vectors = np.linalg.eigh(projected)
    c0, c1 = complex(vectors[0, 0]), complex(vectors[1, 0])
    angle = 2 * math.atan2(c1.real, c0.real)
    if angle > math.pi:
        angle -= 2 * math.pi
    return float(angle), float(values[0]), float(abs(c0) ** 2 + abs(c1) ** 2)


def hartree_to_kcal(value: float) -> float:
    return value * HARTREE_TO_KCAL
