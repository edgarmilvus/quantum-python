"""Frequencies, intervals, and the arithmetic that turns counts into claims.

Every number here is either an estimate, an interval, or a correction. The module
refuses inputs it cannot defend, because a silent zero is how a statistical claim dies.
"""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

Z95 = 1.959963984540054


def frequency(count: int, shots: int) -> float:
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    if not 0 <= count <= shots:
        raise ValueError(f"count must be inside [0, {shots}], got {count}")
    return count / shots


def standard_error(p: float, shots: int) -> float:
    if not 0.0 <= p <= 1.0:
        raise ValueError(f"p must be in [0, 1], got {p}")
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    return math.sqrt(p * (1.0 - p) / shots)


def wilson(count: int, shots: int, z: float = Z95) -> Tuple[float, float]:
    """The Wilson score interval: the one that stays inside [0, 1]."""
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    if not 0 <= count <= shots:
        raise ValueError(f"count must be inside [0, {shots}], got {count}")
    p = count / shots
    denominator = 1.0 + z * z / shots
    centre = (p + z * z / (2 * shots)) / denominator
    half = z * math.sqrt(p * (1 - p) / shots + z * z / (4 * shots * shots)) / denominator
    low = max(0.0, centre - half)
    high = min(1.0, centre + half)
    if low < 1e-12:
        low = 0.0
    if high > 1.0 - 1e-12:
        high = 1.0
    return low, high


def interval_width(count: int, shots: int, z: float = Z95) -> float:
    low, high = wilson(count, shots, z)
    return high - low


def shots_for(precision: float, p: float = 0.5, z: float = Z95) -> int:
    """Shots needed for a half-width of `precision` around p."""
    if precision <= 0:
        raise ValueError(f"precision must be positive, got {precision}")
    if not 0.0 < p < 1.0:
        raise ValueError(f"p must be strictly inside (0, 1), got {p}")
    return math.ceil(p * (1.0 - p) * (z / precision) ** 2)


def z_score(observed: int, shots: int, expected: float) -> float:
    """How many standard errors an observed count sits from an expected probability."""
    p = frequency(observed, shots)
    error = standard_error(expected, shots)
    if error == 0:
        raise ValueError("a certain expectation has no z score")
    return (p - expected) / error


def combine_independent(values: Sequence[float], errors: Sequence[float]) -> Tuple[float, float]:
    """Sum of independent estimates, with errors added in quadrature."""
    if len(values) != len(errors):
        raise ValueError(f"{len(values)} values and {len(errors)} errors")
    if not values:
        raise ValueError("nothing to combine")
    return float(sum(values)), float(math.sqrt(sum(e * e for e in errors)))


def bonferroni(alpha: float, tests: int) -> float:
    """The per-test threshold that keeps the family error at alpha."""
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be inside (0, 1), got {alpha}")
    if tests < 1:
        raise ValueError(f"tests must be at least one, got {tests}")
    return alpha / tests


# -- readout ------------------------------------------------------------
DEFAULT_ORDER = ("00", "01", "10", "11")


def counts_to_distribution(counts: Dict[str, int], order: Iterable[str] = DEFAULT_ORDER) -> np.ndarray:
    labels = list(order)
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no distribution")
    return np.array([counts.get(label, 0) / total for label in labels], dtype=float)


def confusion(counts_by_preparation: Dict[str, Dict[str, int]], order: Iterable[str] = DEFAULT_ORDER) -> np.ndarray:
    """Rows are prepared states, columns are measured states."""
    labels = list(order)
    matrix = np.zeros((len(labels), len(labels)), dtype=float)
    for row, prepared in enumerate(labels):
        if prepared not in counts_by_preparation:
            raise ValueError(f"no calibration for prepared state {prepared}")
        distribution = counts_to_distribution(counts_by_preparation[prepared], labels)
        matrix[row, :] = distribution
    return matrix


def invert(matrix: np.ndarray, floor: float = 1e-3) -> np.ndarray:
    """Invert a confusion matrix, refusing one that is too close to singular.

    A matrix with a zero diagonal cannot be inverted, and a pseudo-inverse would hide
    the fact. The floor keeps the result finite and the refusal keeps it honest.
    """
    m = np.asarray(matrix, dtype=float)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise ValueError(f"a confusion matrix is square, got {m.shape}")
    if np.any(m < 0):
        raise ValueError("a confusion matrix cannot have negative entries")
    if not np.allclose(m.sum(axis=1), 1.0, atol=1e-9):
        raise ValueError("every row must sum to one")
    determinant = float(np.linalg.det(m))
    if abs(determinant) < floor:
        raise ValueError(f"the matrix is too close to singular: determinant {determinant:.2e}")
    return np.linalg.inv(m)


def correct(counts: Dict[str, int], inverse: np.ndarray, order: Iterable[str] = DEFAULT_ORDER) -> np.ndarray:
    """Correct a measured distribution with an inverted confusion matrix.

    The raw correction can contain negative entries, which are not probabilities. They
    are clipped to zero and the vector is renormalized, and the caller is expected to
    report how much clipping happened.
    """
    measured = counts_to_distribution(counts, order)
    corrected = inverse @ measured
    return corrected


def clip_and_renormalize(values: np.ndarray) -> Tuple[np.ndarray, float]:
    """Clip negatives to zero, renormalize, and report how much mass was clipped."""
    v = np.asarray(values, dtype=float)
    if v.ndim != 1 or v.size == 0:
        raise ValueError(f"expected a vector, got {v.shape}")
    positive = float(np.clip(v, 0.0, None).sum())
    negative = float(-np.clip(v, None, 0.0).sum())
    if positive <= 0:
        raise ValueError("the vector has no positive mass and cannot be renormalized")
    # The reported mass is the fraction of the final distribution that came from
    # entries the correction made negative: what the clipping had to remove.
    mass = negative / positive
    clipped = np.clip(v, 0.0, None)
    return clipped / positive, mass


def total_variation(a: Iterable[float], b: Iterable[float]) -> float:
    """Half the L1 distance between two distributions."""
    left = np.asarray(list(a), dtype=float)
    right = np.asarray(list(b), dtype=float)
    if left.shape != right.shape:
        raise ValueError(f"shapes differ: {left.shape} and {right.shape}")
    if abs(left.sum() - 1.0) > 1e-9 or abs(right.sum() - 1.0) > 1e-9:
        raise ValueError("both inputs must be distributions")
    return float(0.5 * np.abs(left - right).sum())


def bootstrap_error(counts: Dict[str, int], statistic, draws: int = 2000, seed: int = 7) -> float:
    """Standard deviation of a statistic over resampled histograms.

    `statistic` takes a dictionary of counts and returns one number. Resampling is the
    honest way to put an error on a quantity that is not a simple sum.
    """
    if draws < 2:
        raise ValueError(f"draws must be at least two, got {draws}")
    labels: List[str] = list(counts)
    totals = sum(counts.values())
    if totals <= 0:
        raise ValueError("an empty histogram cannot be resampled")
    stacked = np.array([counts[label] for label in labels], dtype=float)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(draws):
        resampled = rng.multinomial(totals, stacked / stacked.sum())
        values.append(statistic({label: int(n) for label, n in zip(labels, resampled)}))
    return float(np.std(values, ddof=1))
