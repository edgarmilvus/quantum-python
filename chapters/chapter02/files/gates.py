"""The gate matrices, and the one function that puts a gate on a wire.

A gate is a 2x2 complex matrix. Applying it to one wire of a two-wire register is
a tensor product with the identity on the other wire, and the order of that
product is the whole chapter.
"""

from __future__ import annotations

import numpy as np

I2 = np.eye(2, dtype=np.complex128)
X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
S = np.array([[1, 0], [0, 1j]], dtype=np.complex128)
T = np.array([[1, 0], [0, np.exp(1j * np.pi / 4)]], dtype=np.complex128)

NAMED = {"I": I2, "X": X, "Y": Y, "Z": Z, "H": H, "S": S, "T": T}

# CNOT with wire 0 as control and wire 1 as target, in the convention of this
# chapter (wire 0 is the left factor, so it is the high bit of the index).
CNOT = np.array(
    [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ],
    dtype=np.complex128,
)


def Rx(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=np.complex128)


def Ry(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)


def Rz(theta: float) -> np.ndarray:
    return np.array(
        [[np.exp(-1j * theta / 2), 0], [0, np.exp(1j * theta / 2)]], dtype=np.complex128
    )


def embed(gate: np.ndarray, wire: int, wires: int = 2) -> np.ndarray:
    """The 2**wires matrix that applies `gate` to `wire` and nothing elsewhere.

    wire 0 is the left factor, wire 1 the right factor. That choice is the
    convention this chapter argues about; the code states it once, here.
    """
    if wires < 1:
        raise ValueError(f"a register has at least one wire, got {wires}")
    if not 0 <= wire < wires:
        raise ValueError(f"wire must be in [0, {wires - 1}], got {wire}")
    factors = [I2] * wires
    factors[wire] = gate
    matrix = factors[0]
    for factor in factors[1:]:
        matrix = np.kron(matrix, factor)
    return matrix


def apply_one(state: np.ndarray, gate: np.ndarray, wire: int, wires: int = 2) -> np.ndarray:
    """Apply `gate` to `wire` of a state vector."""
    vector = np.asarray(state, dtype=np.complex128)
    expected = 2**wires
    if vector.shape != (expected,):
        raise ValueError(f"a {wires}-wire state has {expected} amplitudes, got {vector.shape}")
    return embed(gate, wire, wires) @ vector
