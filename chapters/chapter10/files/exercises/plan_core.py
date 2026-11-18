"""Exercise 5, file 1 of 3: the pure part.

An angle and a shot count in, a verdict out: the energy from two simulated tallies, its
uncertainty, and whether it clears chemical accuracy.
"""

from __future__ import annotations

from typing import Dict

import h2
import vqe


def evaluate(theta: float, shots: int = 10_000, seed: int = 7) -> Dict[str, float]:
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    z = vqe.tally(theta, "Z", shots, seed=seed)
    x = vqe.tally(theta, "X", shots, seed=seed + 1)
    result = vqe.energy_from_tallies(z, x)
    sigma = vqe.shot_sigma(theta, shots)
    return {
        "angle": theta,
        "shots": shots,
        "energy": result["energy"],
        "exact": h2.exact_ground(),
        "sigma": sigma,
        "gap": result["energy"] - h2.exact_ground(),
        "within_accuracy": abs(result["energy"] - h2.exact_ground()) <= h2.CHEMICAL_ACCURACY,
        "z_part": result["z_part"],
        "xx_part": result["xx_part"],
    }


def rows(result: Dict[str, float]) -> list:
    return [
        ("angle", f"{result['angle']:+.4f}"),
        ("shots per basis", str(int(result["shots"]))),
        ("energy", f"{result['energy']:+.6f}"),
        ("exact", f"{result['exact']:+.6f}"),
        ("gap (mHa)", f"{result['gap'] * 1000:+.2f}"),
        ("1 sigma (mHa)", f"{result['sigma'] * 1000:.2f}"),
        ("within accuracy", "yes" if result["within_accuracy"] else "no"),
    ]
