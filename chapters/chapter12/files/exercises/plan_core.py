"""Exercise 5, file 1 of 3: the pure part.

Four histograms, a readout matrix and three extrapolation points in; a verdict
out. No file is read, no backend is built, nothing is printed. Everything the
wiring does that could be wrong lives outside this file.
"""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

from noise import confusion, zne

SETTINGS = ("ab", "ab_prime", "a_prime_b", "a_prime_b_prime")


def distribution(counts: Dict[str, int]) -> Dict[str, float]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no distribution")
    return {key: value / total for key, value in counts.items()}


def summarise(
    raw: Dict[str, Dict[str, int]],
    matrix: np.ndarray,
    points: Sequence[zne.Point],
    ideal: float,
) -> Dict[str, float]:
    """The three numbers a mitigation report owes: raw, corrected, extrapolated."""
    missing = [name for name in SETTINGS if name not in raw]
    if missing:
        raise ValueError(f"missing settings: {missing}")
    if ideal <= 0:
        raise ValueError(f"an ideal value is positive, got {ideal}")
    if len(points) < 2:
        raise ValueError(f"an extrapolation needs two points, got {len(points)}")

    raw_correlators = {name: confusion.correlation(distribution(raw[name])) for name in SETTINGS}
    fixed_correlators = {
        name: confusion.correlation(confusion.correct(raw[name], matrix)[0]) for name in SETTINGS
    }
    raw_s = confusion.chsh(raw_correlators)
    fixed_s = confusion.chsh(fixed_correlators)

    fit = zne.linear(points)
    if ideal <= raw_s:
        closed = float("nan")
    else:
        closed = (fixed_s - raw_s) / (ideal - raw_s)

    return {
        "raw": raw_s,
        "corrected": fixed_s,
        "extrapolated": fit.value,
        "sigma": fit.sigma,
        "closed": closed,
        "remaining": ideal - fit.value,
        "z": (fit.value - ideal) / fit.sigma if fit.sigma > 0 else float("inf"),
        "ideal": ideal,
    }


def verdict(summary: Dict[str, float], threshold: float = 2.0) -> str:
    """Whether the extrapolated value is inside `threshold` sigma of the ideal."""
    if threshold <= 0:
        raise ValueError(f"a threshold must be positive, got {threshold}")
    return "consistent" if abs(summary["z"]) <= threshold else "gap"
