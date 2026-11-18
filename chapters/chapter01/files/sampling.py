"""Turning a state vector into counts, the way a device does it.

Measurement is sampling. This module does exactly one sample per shot, from the
distribution p_i = |a_i|^2, and counts what came out.
"""

from __future__ import annotations

import math
from typing import Dict, Optional

import numpy as np

from state import StateError, StateVector


def _check_distribution(state: StateVector, tol: float = 1e-9) -> np.ndarray:
    p = state.probabilities()
    total = float(p.sum())
    if abs(total - 1.0) > tol:
        raise StateError(
            f"cannot sample from a distribution that sums to {total:.12f}; "
            f"normalize the state first"
        )
    if np.any(p < -tol):
        raise StateError(f"a probability is negative: {p}")
    return p


def sample_index(state: StateVector, rng: Optional[np.random.Generator] = None) -> int:
    """Draw one outcome from the state's distribution."""
    p = _check_distribution(state)
    generator = rng if rng is not None else np.random.default_rng()
    # One uniform number, compared against the cumulative sums: this is what a
    # device does, and it keeps the draw to a single call.
    return int(np.searchsorted(np.cumsum(p), generator.random(), side="right"))


def sample_counts(
    state: StateVector,
    shots: int,
    seed: Optional[int] = None,
) -> Dict[str, int]:
    """Run `shots` independent draws and count the outcomes."""
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    rng = np.random.default_rng(seed)
    draws = [sample_index(state, rng) for _ in range(shots)]
    counts = {"0": draws.count(0), "1": draws.count(1)}
    return counts


def estimated_probability(counts: Dict[str, int], index: int) -> float:
    """The frequency of one outcome, as a probability estimate."""
    total = sum(counts.values())
    if total == 0:
        raise ValueError("no shots: an estimate needs at least one outcome")
    return counts.get(str(index), 0) / total


def standard_error(p: float, shots: int) -> float:
    """The binomial standard error of a frequency estimate."""
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"p must be in [0, 1], got {p}")
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    return math.sqrt(p * (1.0 - p) / shots)
