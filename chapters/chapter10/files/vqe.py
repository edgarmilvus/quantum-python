"""The optimiser, the two tallies, and the shot noise they bring.

VQE is a loop: the circuit is prepared, the energy is measured, the knob moves, repeat.
This module holds the loop and the estimator, and it counts what the loop costs.
"""

from __future__ import annotations

from typing import Callable, Dict, Tuple

import numpy as np

import h2


def expectation(state: np.ndarray, label: str) -> float:
    """<psi|P|psi> for a two-qubit Pauli string."""
    matrix = h2.operator(label)
    return float(np.real(np.vdot(state, matrix @ state)))


def energy_exact(theta: float) -> float:
    return h2.energy(theta)


def golden_section(
    f: Callable[[float], float],
    lo: float = -1.0,
    hi: float = 1.0,
    tolerance: float = 1e-8,
    max_evaluations: int = 200,
) -> Dict[str, float]:
    """A derivative-free minimiser, with the number of energy evaluations it used."""
    if lo >= hi:
        raise ValueError(f"the interval is empty: {lo} >= {hi}")
    if tolerance <= 0:
        raise ValueError(f"a tolerance must be positive, got {tolerance}")
    ratio = (np.sqrt(5.0) - 1.0) / 2.0
    a, b = lo, hi
    c = b - ratio * (b - a)
    d = a + ratio * (b - a)
    fc, fd = f(c), f(d)
    evaluations = 2
    while abs(b - a) > tolerance and evaluations < max_evaluations:
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - ratio * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + ratio * (b - a)
            fd = f(d)
        evaluations += 1
    best = (a + b) / 2
    return {"angle": best, "energy": f(best), "evaluations": float(evaluations + 1)}


def tally(theta: float, basis: str, shots: int, seed: int | None = None) -> Dict[str, int]:
    """Sample one measurement basis: 'Z' as it is, 'X' after a Hadamard on both qubits."""
    if basis not in ("Z", "X"):
        raise ValueError(f"a basis is Z or X, got {basis!r}")
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    state = h2.ansatz_state(theta)
    if basis == "X":
        state = _hadamard_pair() @ state
    probabilities = np.abs(state) ** 2
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(shots, probabilities)
    return {format(index, "02b"): int(count) for index, count in enumerate(draws) if count}


def _hadamard_pair() -> np.ndarray:
    h = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
    return np.kron(h, h)


def average(counts: Dict[str, int], label: str) -> float:
    """The signed average of one Pauli string over a tally."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty tally has no average")
    if len(label) != 2:
        raise ValueError(f"a two-qubit label has two letters, got {label!r}")
    value = 0
    for bits, count in counts.items():
        sign = 1
        for position, letter in enumerate(reversed(label)):
            if letter != "I" and bits[position] == "1":
                sign = -sign
        value += sign * count
    return value / total


def energy_from_tallies(z_counts: Dict[str, int], x_counts: Dict[str, int]) -> Dict[str, float]:
    """The energy from two tallies, with the constant terms added."""
    z_terms = sum(h2.TERMS[label] * average(z_counts, label) for label in ("II", "IZ", "ZI", "ZZ"))
    xx = h2.TERMS["XX"] * average(x_counts, "XX")
    return {
        "constant": h2.TERMS["II"] + h2.NUCLEAR,
        "z_part": z_terms - h2.TERMS["II"],
        "xx_part": xx,
        "energy": z_terms + xx + h2.NUCLEAR,
    }


def _shot_value(bits: str, labels) -> float:
    """The energy contribution of one shot, given the term labels measured in that basis."""
    total = 0.0
    for label in labels:
        sign = 1
        for position, letter in enumerate(reversed(label)):
            if letter != "I" and bits[position] == "1":
                sign = -sign
        total += h2.TERMS[label] * sign
    return total


def shot_sigma(theta: float, shots: int) -> float:
    """The standard deviation of the energy from two tallies of `shots` each.

    The variance is taken over the outcomes of each tally, not summed per term: the three
    Z terms are measured in one tally and therefore correlated. Summing per-term variances
    gives 6.83 mHa at a thousand shots; the exact value is 7.89, and the published table
    quotes the second.
    """
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    state = h2.ansatz_state(theta)
    z_state = state
    x_state = _hadamard_pair() @ state
    total_variance = 0.0
    for projected, labels in ((z_state, ("IZ", "ZI", "ZZ")), (x_state, ("XX",))):
        probabilities = np.abs(projected) ** 2
        values = np.array([_shot_value(format(index, "02b"), labels) for index in range(4)])
        mean = float((values * probabilities).sum())
        variance = float((values**2 * probabilities).sum()) - mean**2
        total_variance += variance
    return float(np.sqrt(total_variance / shots))


def shots_for(theta: float, target: float = h2.CHEMICAL_ACCURACY) -> int:
    """The shots per basis that give a standard deviation of `target` at this angle."""
    if target <= 0:
        raise ValueError(f"a target must be positive, got {target}")
    sigma_one = shot_sigma(theta, 1)
    return int(np.ceil((sigma_one / target) ** 2))
