"""The quantum Fourier transform as a matrix, and its circuit decomposition.

The transform is a change of basis with entries e^{2 pi i jk / N} / sqrt(N). The circuit
is Hadamards and controlled phase rotations, and the harness checks that the two agree
exactly, because the whole chapter depends on it.
"""

from __future__ import annotations

import cmath
import math
from typing import List

import numpy as np

H2 = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
I2 = np.eye(2, dtype=np.complex128)


def dft(n: int, sign: int = 1) -> np.ndarray:
    """The 2^n by 2^n Fourier matrix, with sign +1 for the transform and -1 for its inverse."""
    if n < 1:
        raise ValueError(f"a transform needs at least one qubit, got {n}")
    if sign not in (1, -1):
        raise ValueError(f"the sign is +1 or -1, got {sign}")
    size = 1 << n
    root = cmath.exp(sign * 2j * math.pi / size)
    matrix = np.zeros((size, size), dtype=np.complex128)
    for row in range(size):
        for column in range(size):
            matrix[row, column] = root ** (row * column)
    return matrix / math.sqrt(size)


def rotation(angle: float) -> np.ndarray:
    return np.array([[1, 0], [0, cmath.exp(1j * angle)]], dtype=np.complex128)


def embed_one(gate: np.ndarray, wire: int, n: int) -> np.ndarray:
    factors = [I2] * n
    factors[wire] = gate
    matrix = factors[0]
    for factor in factors[1:]:
        matrix = np.kron(matrix, factor)
    return matrix


def controlled_phase(angle: float, control: int, target: int, n: int) -> np.ndarray:
    """A phase on the target, applied only when the control is 1."""
    if n < 2:
        raise ValueError(f"a controlled gate needs at least two qubits, got {n}")
    if control == target:
        raise ValueError("control and target must differ")
    size = 1 << n
    matrix = np.eye(size, dtype=np.complex128)
    for index in range(size):
        bits = format(index, f"0{n}b")
        if bits[control] == "1" and bits[target] == "1":
            matrix[index, index] = cmath.exp(1j * angle)
    return matrix


def swap(n: int, a: int, b: int) -> np.ndarray:
    if a == b:
        raise ValueError("a swap needs two different wires")
    size = 1 << n
    matrix = np.zeros((size, size), dtype=np.complex128)
    for index in range(size):
        bits = list(format(index, f"0{n}b"))
        bits[a], bits[b] = bits[b], bits[a]
        matrix[int("".join(bits), 2), index] = 1.0
    return matrix


def qft_schedule(n: int):
    """The wires each gate touches, in order, without building any matrix."""
    if n < 1:
        raise ValueError(f"a transform needs at least one qubit, got {n}")
    schedule = []
    for j in range(n):
        schedule.append((j,))
        for k in range(j + 1, n):
            schedule.append((k, j))
    for j in range(n // 2):
        schedule.append((j, n - 1 - j))
    return schedule


def qft_ops(n: int):
    """The gates of the transform with the wires each one touches."""
    if n < 1:
        raise ValueError(f"a transform needs at least one qubit, got {n}")
    ops = []
    for j in range(n):
        ops.append(((j,), embed_one(H2, j, n)))
        for k in range(j + 1, n):
            angle = math.pi / (2 ** (k - j))
            ops.append(((k, j), controlled_phase(angle, control=k, target=j, n=n)))
    for j in range(n // 2):
        ops.append(((j, n - 1 - j), swap(n, j, n - 1 - j)))
    return ops


def qft_circuit(n: int) -> List[np.ndarray]:
    """The gates of the transform, in application order."""
    return [gate for _, gate in qft_ops(n)]


def qft_matrix(n: int) -> np.ndarray:
    """The product of the circuit's gates, applied left to right."""
    total = np.eye(1 << n, dtype=np.complex128)
    for gate in qft_circuit(n):
        total = gate @ total
    return total


def inverse_qft_matrix(n: int) -> np.ndarray:
    return qft_matrix(n).conj().T


def circuit_depth(n: int) -> int:
    """Sequential layers, scheduled by which wires each gate holds."""
    free_at = [0] * n
    for wires in qft_schedule(n):
        layer = max(free_at[w] for w in wires) + 1
        for w in wires:
            free_at[w] = layer
    return max(free_at) if n else 0


def gate_count(n: int) -> int:
    """Hadamards, controlled phases and swaps."""
    return len(qft_schedule(n))
