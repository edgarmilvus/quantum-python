"""Grover's search as two matrices and a loop.

The oracle flips the sign of one basis state; the diffusion operator inverts every
amplitude about the mean. Alternating them k times raises the marked amplitude to
sin((2k+1) theta), and the interesting part is that k has an optimum.
"""

from __future__ import annotations

import math
from typing import Dict, List

import numpy as np

H2 = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
I2 = np.eye(2, dtype=np.complex128)


def hadamards(n: int) -> np.ndarray:
    if n < 1:
        raise ValueError(f"a search needs at least one qubit, got {n}")
    matrix = H2
    for _ in range(n - 1):
        matrix = np.kron(matrix, H2)
    return matrix


def uniform(n: int) -> np.ndarray:
    """The start state: H on every qubit applied to |0...0>."""
    size = 1 << n
    state = np.zeros(size, dtype=np.complex128)
    state[0] = 1.0
    return hadamards(n) @ state


def oracle(marked: int, n: int) -> np.ndarray:
    """The phase oracle: -1 on the marked basis state, +1 elsewhere."""
    size = 1 << n
    if not 0 <= marked < size:
        raise ValueError(f"marked index must be in [0, {size - 1}], got {marked}")
    diagonal = np.ones(size, dtype=np.complex128)
    diagonal[marked] = -1.0
    return np.diag(diagonal)


def diffusion(n: int) -> np.ndarray:
    """2|s><s| - I, written as H (2|0><0| - I) H."""
    size = 1 << n
    around_zero = -np.eye(size, dtype=np.complex128)
    around_zero[0, 0] = 1.0
    matrix = hadamards(n)
    return matrix @ around_zero @ matrix


def iterate(marked: int, n: int, steps: int) -> np.ndarray:
    """Apply oracle and diffusion `steps` times to the uniform state."""
    if steps < 0:
        raise ValueError(f"steps cannot be negative, got {steps}")
    state = uniform(n)
    flip = oracle(marked, n)
    mirror = diffusion(n)
    for _ in range(steps):
        state = mirror @ (flip @ state)
    return state


def probabilities(state: np.ndarray) -> np.ndarray:
    values = np.asarray(state, dtype=np.complex128)
    if values.ndim != 1 or values.size & (values.size - 1):
        raise ValueError(f"a state has a power-of-two length, got {values.shape}")
    return np.abs(values) ** 2


def success_probability(marked: int, n: int, steps: int) -> float:
    return float(probabilities(iterate(marked, n, steps))[marked])


def theta(size: int) -> float:
    """The rotation angle per iteration: sin(theta) = 1/sqrt(size)."""
    if size < 2:
        raise ValueError(f"a search needs at least two items, got {size}")
    return math.asin(1.0 / math.sqrt(size))


def optimal_iterations(size: int) -> int:
    """The k that lands closest to a quarter turn: round(pi/(4 theta) - 1/2)."""
    return max(1, int(round(math.pi / (4.0 * theta(size)) - 0.5)))


def approx_iterations(size: int) -> int:
    """The textbook approximation round((pi/4) sqrt(N)); exact only for large N."""
    if size < 2:
        raise ValueError(f"a search needs at least two items, got {size}")
    return max(1, int(round(math.pi / 4.0 * math.sqrt(size))))


def analytic_success(size: int, steps: int) -> float:
    """sin^2((2k+1) theta) with sin(theta) = 1/sqrt(size)."""
    if size < 2:
        raise ValueError(f"a search needs at least two items, got {size}")
    theta = math.asin(1.0 / math.sqrt(size))
    return float(math.sin((2 * steps + 1) * theta) ** 2)


def curve(n: int, limit: int | None = None) -> List[Dict[str, float]]:
    """Success probability for every step count up to the first maximum."""
    size = 1 << n
    end = limit if limit is not None else optimal_iterations(size) + 2
    return [{"steps": k, "probability": success_probability(0, n, k)} for k in range(end + 1)]


def classical_queries(size: int, found: bool = True) -> int:
    """Expected linear-search queries: (size + 1) / 2 for a random position."""
    if size < 1:
        raise ValueError(f"a list has at least one item, got {size}")
    return (size + 1) // 2 if found else size


def binary_search_queries(size: int) -> int:
    """Comparisons for a sorted list, rounded up."""
    if size < 1:
        raise ValueError(f"a list has at least one item, got {size}")
    return max(1, math.ceil(math.log2(size)))
