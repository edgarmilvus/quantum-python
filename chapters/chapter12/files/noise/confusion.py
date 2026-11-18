"""The readout matrix: build it, invert it, and say what the inversion cost.

Chapter 5 taught the inversion for a four-outcome experiment. This module does
the same arithmetic for any number of wires, and adds the two things a chapter
about mitigation needs: the independence check (does the tensor product of
per-qubit flips reproduce the measured matrix?) and the amplification factor
(how much variance the inversion adds).
"""

from __future__ import annotations

import itertools
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

ORDER = ("00", "01", "10", "11")


def matrix_from_record(record: dict) -> np.ndarray:
    """Rows are prepared states, columns measured, both in Qiskit key order."""
    if "preparations" not in record:
        raise ValueError("not a readout calibration record")
    matrix = np.zeros((4, 4))
    for name, wires in record["preparations"].items():
        expected = 0
        for wire in wires:
            expected |= 1 << wire
        prepared = format(expected, "02b")
        row = record["counts"][name]
        total = sum(row.values())
        for measured, count in row.items():
            matrix[ORDER.index(measured), ORDER.index(prepared)] = count / total
    return matrix


def tensor(flips: Sequence[float], n: Optional[int] = None) -> np.ndarray:
    """The matrix implied by independent per-wire flips, in key order."""
    width = n if n is not None else len(flips)
    if width != len(flips):
        raise ValueError(f"{len(flips)} flips cannot cover {width} wires")
    size = 2 ** width
    matrix = np.zeros((size, size))
    for prepared in range(size):
        for measured in range(size):
            probability = 1.0
            for wire in range(width):
                same = ((prepared >> wire) & 1) == ((measured >> wire) & 1)
                probability *= (1 - flips[wire]) if same else flips[wire]
            matrix[measured, prepared] = probability
    return matrix


def independence_error(record: dict, flips: Sequence[float]) -> float:
    """The largest gap between the measured matrix and the tensor product."""
    measured = matrix_from_record(record)
    predicted = tensor(flips)
    return float(np.abs(measured - predicted).max())


def inverse(matrix: np.ndarray) -> np.ndarray:
    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError(f"a matrix is square, got {matrix.shape}")
    if abs(np.linalg.det(matrix)) < 1e-12:
        raise ValueError("the readout matrix is singular and cannot be inverted")
    return np.linalg.inv(matrix)


def correct(counts: Dict[str, int], matrix: np.ndarray) -> Tuple[Dict[str, float], float]:
    """Apply the inverse, clip the negatives, renormalise.

    Returns the corrected distribution and the mass that had to be clipped:
    a large clipped mass means the correction is out of its depth, and the
    number belongs in the report next to the corrected value.
    """
    width = int(round(np.log2(matrix.shape[0])))
    if 2 ** width != matrix.shape[0]:
        raise ValueError(f"{matrix.shape[0]} outcomes is not a power of two")
    keys = [format(index, f"0{width}b") for index in range(matrix.shape[0])]
    raw = np.array([counts.get(key, 0) for key in keys], dtype=float)
    total = raw.sum()
    if total <= 0:
        raise ValueError("an empty histogram has nothing to correct")
    distribution = raw / total
    # p_measured = M p_prepared, so p_prepared = M-inverse p_measured: the
    # inverse multiplies on the left. The other order is the transpose,
    # which looks right and returns a distribution off by the asymmetry.
    corrected = inverse(matrix) @ distribution
    clipped = float(max(0.0, -corrected[corrected < 0].sum()))
    corrected = np.clip(corrected, 0, None)
    if corrected.sum() <= 0:
        raise ValueError("the correction left no positive mass")
    corrected = corrected / corrected.sum()
    return dict(zip(keys, (float(value) for value in corrected))), clipped


def amplification(matrix: np.ndarray) -> float:
    """The worst-case factor by which the inverse stretches an L1 error.

    The row sums of |M-inverse| bound how much a perturbation of the measured
    distribution is magnified. For the chapter's matrix the worst factor is
    about 1.6, which is the price of the correction and the reason its error
    bar is wider than the raw one.
    """
    return float(np.abs(inverse(matrix)).sum(axis=1).max())


def total_variation(a: Dict[str, float], b: Dict[str, float]) -> float:
    """Half the L1 distance between two distributions on the same keys."""
    keys = set(a) | set(b)
    return 0.5 * sum(abs(a.get(key, 0.0) - b.get(key, 0.0)) for key in keys)


def correlation(distribution: Dict[str, float]) -> float:
    """E = P(same) - P(different) for a two-wire distribution."""
    return (
        distribution.get("00", 0.0)
        + distribution.get("11", 0.0)
        - distribution.get("01", 0.0)
        - distribution.get("10", 0.0)
    )


def parities(distribution: Dict[str, float]) -> Dict[str, float]:
    """The four correlators of a CHSH run, from four distributions."""
    return {name: correlation(value) for name, value in distribution.items()}


def chsh(correlators: Dict[str, float]) -> float:
    """S = E(a,b) - E(a,b') + E(a',b) + E(a',b'), the chapter 4 convention."""
    required = ("ab", "ab_prime", "a_prime_b", "a_prime_b_prime")
    missing = [name for name in required if name not in correlators]
    if missing:
        raise KeyError(f"CHSH needs {missing}")
    return (
        correlators["ab"]
        - correlators["ab_prime"]
        + correlators["a_prime_b"]
        + correlators["a_prime_b_prime"]
    )


def chsh_sigma(correlators: Dict[str, float], shots: int, shots_per_setting: Optional[int] = None) -> float:
    """The propagated error on S, one correlator at a time.

    Each E is a difference of four frequencies, so var(E) = (1 - E^2)/shots to
    first order, and the four settings are independent: var(S) = 4 var(E).
    """
    if missing := [k for k in ("ab", "ab_prime", "a_prime_b", "a_prime_b_prime") if k not in correlators]:
        raise KeyError(f"CHSH needs {missing}")
    n = shots_per_setting or shots
    variance = 0.0
    for value in correlators.values():
        variance += (1 - value ** 2) / n
    return float(np.sqrt(variance))
