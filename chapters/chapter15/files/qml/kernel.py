"""The kernel matrix: from states, from shots, and from a device.

Three estimates of the same matrix, and the chapter's argument is that they differ
in ways a report has to name. The exact one comes from two statevectors; the
sampled one comes from counting all-zero outcomes; the device's one comes from
the same counts with the device's own noise on top.
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

from . import featuremap as fm

Point = Tuple[float, float]


def matrix(points: Sequence[Point], reps: int = 1) -> np.ndarray:
    """The exact Gram matrix, one fidelity per pair, symmetric by construction."""
    states = [fm.state_for(point, reps=reps) for point in points]
    n = len(points)
    gram = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            value = fm.fidelity(states[i], states[j])
            gram[i, j] = gram[j, i] = value
    return gram


def from_counts(counts: Dict[str, int]) -> float:
    """The all-zero frequency, which estimates the squared overlap."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no frequency")
    zeros = sum(count for key, count in counts.items() if set(key) == {"0"})
    return zeros / total


def sampled(points: Sequence[Point], shots: int, seed: int = 0, reps: int = 1) -> np.ndarray:
    """The matrix a noiseless sampler would return at this shot count."""
    if shots < 1:
        raise ValueError(f"shots must be positive, got {shots}")
    rng = np.random.default_rng(seed)
    exact = np.clip(matrix(points, reps), 0.0, 1.0)
    n = len(points)
    out = np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            draws = rng.binomial(shots, float(exact[i, j])) / shots
            out[i, j] = out[j, i] = draws
    return out


def device_matrix(record: dict) -> Tuple[np.ndarray, np.ndarray]:
    """The matrix a recorded run measured, and the shots behind each entry.

    The record holds one row per submitted pair, with the counts of the overlap
    circuit; the all-zero frequency estimates the squared overlap. Entries the run
    did not measure stay at zero and are marked with zero shots, so a caller can
    tell "not measured" from "measured as zero".
    """
    points = record["points"]
    n = len(points)
    gram = np.zeros((n, n))
    shots = np.zeros((n, n))
    for row in record["results"]:
        i, j = int(row["i"]), int(row["j"])
        total = sum(row["counts"].values())
        value = from_counts({str(key): int(count) for key, count in row["counts"].items()})
        gram[i, j] = gram[j, i] = value
        shots[i, j] = shots[j, i] = total
    return gram, shots


def off_diagonal_mean(gram: np.ndarray) -> float:
    n = gram.shape[0]
    if n < 2:
        raise ValueError("a kernel matrix has at least two rows")
    mask = ~np.eye(n, dtype=bool)
    return float(gram[mask].mean())


def condition(gram: np.ndarray) -> float:
    return float(np.linalg.cond(gram))


def distance_to(gram: np.ndarray, other: np.ndarray) -> float:
    """The largest absolute difference, for comparing two estimates."""
    if gram.shape != other.shape:
        raise ValueError(f"{gram.shape} and {other.shape} do not match")
    return float(np.abs(gram - other).max())


def mean_diagonal(gram: np.ndarray) -> float:
    return float(np.diag(gram).mean())


def report(gram: np.ndarray, labels: Sequence[int]) -> str:
    n = gram.shape[0]
    lines = [f"kernel matrix {n}x{n}: diagonal mean {mean_diagonal(gram):.4f}, "
             f"off-diagonal mean {off_diagonal_mean(gram):.4f}, condition {condition(gram):.1f}"]
    for i in range(n):
        row = " ".join(f"{gram[i, j]:.2f}" for j in range(n))
        lines.append(f"  {labels[i]:+d} {row}")
    return "\n".join(lines)
