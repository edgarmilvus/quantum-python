"""The two algorithms, and the classical programs they are compared with.

Each algorithm is four lines: prepare, Hadamard, oracle, Hadamard, read. The
interesting part is what the Hadamards do to the phases the oracle wrote, and the
distribution is the only evidence.
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple

import numpy as np

from oracle import (
    bits,
    distribution,
    hadamard_all,
    hadamard_inputs,
    in_phase_kickback_state,
    linear,
    permutation,
)


def deutsch_jozsa(f: Callable[[int], int], n: int) -> Dict[str, float]:
    """The distribution over the n input strings after one oracle query."""
    state = hadamard_all(in_phase_kickback_state(n), n)
    state = permutation(f, n) @ state
    state = hadamard_inputs(state, n)
    return distribution(state, n)


def bernstein_vazirani(secret: int, n: int) -> Dict[str, float]:
    """The distribution over the n input strings for the linear oracle."""
    if not 0 <= secret < (1 << n):
        raise ValueError(f"secret must fit in {n} bits, got {secret}")
    return deutsch_jozsa(linear(secret, n), n)


def most_likely(distribution_: Dict[str, float]) -> Tuple[str, float]:
    if not distribution_:
        raise ValueError("an empty distribution has no most likely outcome")
    label = max(distribution_, key=distribution_.get)
    return label, distribution_[label]


def deutsch_jozsa_answer(distribution_: Dict[str, float]) -> str:
    """'constant' if the zero string dominates, 'balanced' otherwise."""
    label, probability = most_likely(distribution_)
    return "constant" if label.count("1") == 0 and probability > 0.99 else "balanced"


def classical_queries_deutsch_jozsa(f: Callable[[int], int], n: int) -> int:
    """Queries a deterministic classical program needs in the worst case.

    It must look until it finds a disagreement. A constant function forces 2^(n-1) + 1
    queries: after that many equal answers, a balanced function would have run out of
    the half of its inputs that could still disagree.
    """
    values = [f(x) for x in range(1 << n)]
    first = values[0]
    for position, value in enumerate(values[1:], start=1):
        if value != first:
            return position + 1
    return (1 << (n - 1)) + 1


def classical_queries_bernstein_vazirani(secret: int, n: int) -> int:
    """A classical program needs one query per bit: query x = 1 << i."""
    if not 0 <= secret < (1 << n):
        raise ValueError(f"secret must fit in {n} bits, got {secret}")
    return n


def query_counts(n: int, secret: int) -> Dict[str, Tuple[int, int]]:
    """Classical and quantum queries for both problems, at a given size."""
    constant_function = lambda x: 0
    balanced_function = lambda x: bin(x & secret).count("1") % 2
    return {
        "deutsch_jozsa_constant": (classical_queries_deutsch_jozsa(constant_function, n), 1),
        "deutsch_jozsa_balanced": (classical_queries_deutsch_jozsa(balanced_function, n), 1),
        "bernstein_vazirani": (classical_queries_bernstein_vazirani(secret, n), 1),
    }


def amplitude_pattern(f: Callable[[int], int], n: int) -> Dict[str, float]:
    """The signed amplitudes after the oracle, before the final Hadamards.

    This is the object that explains the algorithm: the oracle writes (-1)^f(x) onto
    the uniform superposition, and the final Hadamards turn that sign pattern into a
    peak at zero (constant) or a peak away from it (balanced).
    """
    state = hadamard_all(in_phase_kickback_state(n), n)
    state = permutation(f, n) @ state
    pattern = {}
    for x in range(1 << n):
        pattern[format(x, f"0{n}b")] = float(np.real(state[(x << 1) | 0]))
    return pattern
