"""Exercise 4 (break): where correcting costs more variance than the bias it removes.

Correction trades bias for variance. At some readout error the trade stops being worth
it, and that error is a design threshold: above it, a correction needs more shots than
the experiment has.

Run: python3 chapters/chapter05/files/exercises/ex4_breakeven.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import numpy as np

from stats import clip_and_renormalize, invert

TRUE = np.array([0.4268, 0.0732, 0.0732, 0.4268])


def synthetic_matrix(error: float) -> np.ndarray:
    """Two independent qubits, each flipping with probability `error`."""
    if not 0.0 <= error < 0.5:
        raise ValueError(f"a per-qubit error must be in [0, 0.5), got {error}")
    single = np.array([[1 - error, error], [error, 1 - error]])
    return np.kron(single, single)


def expectation(distribution: np.ndarray) -> float:
    return float(distribution[0] + distribution[3] - distribution[1] - distribution[2])


def trial(error: float, shots: int = 1024, draws: int = 400, seed: int = 3) -> Dict[str, float]:
    matrix = synthetic_matrix(error)
    inverse = invert(matrix)
    seen = matrix.T @ TRUE
    truth = expectation(TRUE)
    rng = np.random.default_rng(seed)
    raw, fixed, clipped = [], [], []
    for _ in range(draws):
        counts = rng.multinomial(shots, seen) / shots
        corrected, mass = clip_and_renormalize(inverse @ counts)
        raw.append(expectation(counts))
        fixed.append(expectation(corrected))
        clipped.append(mass)
    raw_a = np.array(raw)
    fixed_a = np.array(fixed)
    return {
        "bias_removed": abs(raw_a.mean() - truth) - abs(fixed_a.mean() - truth),
        "spread_added": fixed_a.std(ddof=1) - raw_a.std(ddof=1),
        "clipped": float(np.mean(clipped)),
    }


def scan(errors: List[float] | None = None, shots: int = 1024) -> List[Dict[str, float]]:
    out = []
    for error in errors or [0.01, 0.02, 0.05, 0.1, 0.15, 0.2]:
        row = trial(error, shots=shots)
        row["error"] = error
        out.append(row)
    return out


def checks(check: Callable[[bool, str], None]) -> None:
    low = trial(0.01)
    high = trial(0.2)

    check(low["bias_removed"] > 0, "at 1% the correction removes more than it adds")
    check(high["spread_added"] > low["spread_added"], "at 20% the spread grows faster")
    check(high["clipped"] >= low["clipped"], "clipping appears as the error grows")

    rows = scan()
    check(len(rows) == 6, "the scan has six points")
    check(all(row["bias_removed"] >= 0 for row in rows), "the correction always removes bias")

    # More shots at a high error rate narrow the spread, which is the remedy.
    at_20k = trial(0.2, shots=8192)
    check(at_20k["spread_added"] < high["spread_added"], "eight times the shots narrow the added spread")

    for bad in (-0.1, 0.5):
        try:
            synthetic_matrix(bad)
        except ValueError:
            check(True, f"error {bad} is refused")
        else:
            check(False, f"error {bad} is refused")

    check(np.allclose(synthetic_matrix(0.0), np.eye(4)), "a zero error is the identity")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
