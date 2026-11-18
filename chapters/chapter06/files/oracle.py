"""Oracles as permutations of the amplitude vector.

An oracle for f: {0,1}^n -> {0,1} is the map |x, y> -> |x, y xor f(x)>. On a state
vector that is a permutation of the 2^(n+1) amplitudes, and a permutation is the
easiest object in this book to get exactly right.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Tuple

import numpy as np

H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
I2 = np.eye(2, dtype=np.complex128)


def index(x: int, y: int) -> int:
    """Index of |x, y> with x as the high bits and y as the last bit."""
    return (x << 1) | y


def bits(value: int, width: int) -> List[int]:
    return [int(b) for b in format(value, f"0{width}b")]


def permutation(f: Callable[[int], int], n: int) -> np.ndarray:
    """The 2^(n+1) permutation matrix of the oracle for f on n bits."""
    if n < 1:
        raise ValueError(f"an oracle needs at least one input bit, got {n}")
    size = 1 << (n + 1)
    matrix = np.zeros((size, size), dtype=np.complex128)
    for x in range(1 << n):
        value = f(x)
        if value not in (0, 1):
            raise ValueError(f"f({x}) = {value}; an oracle returns a bit")
        for y in (0, 1):
            matrix[index(x, y ^ value), index(x, y)] = 1.0
    return matrix


def embed_hadamard(qubits: List[int], total: int) -> np.ndarray:
    """H on a subset of qubits, as a matrix on the whole register."""
    factors = [I2] * total
    for qubit in qubits:
        factors[qubit] = H
    matrix = factors[0]
    for factor in factors[1:]:
        matrix = np.kron(matrix, factor)
    return matrix


def in_phase_kickback_state(n: int) -> np.ndarray:
    """|0...0> tensor |1>, the input every oracle algorithm starts from."""
    state = np.zeros(1 << (n + 1), dtype=np.complex128)
    state[index(0, 1)] = 1.0
    return state


def hadamard_all(state: np.ndarray, n: int) -> np.ndarray:
    """H on the n input qubits and on the output qubit."""
    total = n + 1
    return embed_hadamard(list(range(total)), total) @ state


def hadamard_inputs(state: np.ndarray, n: int) -> np.ndarray:
    """H on the n input qubits only, before measuring them."""
    total = n + 1
    return embed_hadamard(list(range(n)), total) @ state


def distribution(state: np.ndarray, n: int) -> Dict[str, float]:
    """Probabilities over the 2^n input strings, the output qubit traced out."""
    total = 1 << (n + 1)
    values = np.asarray(state, dtype=np.complex128)
    if values.shape != (total,):
        raise ValueError(f"a {n}-bit algorithm has {total} amplitudes, got {values.shape}")
    probabilities = np.abs(values) ** 2
    out = {}
    for x in range(1 << n):
        out[format(x, f"0{n}b")] = float(probabilities[index(x, 0)] + probabilities[index(x, 1)])
    return out


# -- the functions ------------------------------------------------------
def constant(value: int) -> Callable[[int], int]:
    if value not in (0, 1):
        raise ValueError(f"a constant function returns 0 or 1, got {value}")
    return lambda x: value


def balanced(secret: int, n: int) -> Callable[[int], int]:
    """f(x) = parity(x and secret): balanced whenever secret is non-zero."""
    if not 0 <= secret < (1 << n):
        raise ValueError(f"secret must fit in {n} bits, got {secret}")
    if secret == 0:
        raise ValueError("a zero mask is a constant function, not a balanced one")
    return lambda x: bin(x & secret).count("1") % 2


def linear(secret: int, n: int) -> Callable[[int], int]:
    """f(x) = parity(x and secret), the Bernstein-Vazirani family."""
    if not 0 <= secret < (1 << n):
        raise ValueError(f"secret must fit in {n} bits, got {secret}")
    return lambda x: bin(x & secret).count("1") % 2


def is_constant(f: Callable[[int], int], n: int) -> bool:
    """True when every input gives the same answer."""
    return len({f(x) for x in range(1 << n)}) == 1


def is_balanced(f: Callable[[int], int], n: int) -> bool:
    """True when exactly half the inputs give zero and half give one."""
    values = [f(x) for x in range(1 << n)]
    half = len(values) // 2
    return values.count(0) == half and values.count(1) == half
