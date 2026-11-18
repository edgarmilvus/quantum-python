"""Exercise 3 (measure): which term costs the most shots.

The XX term has a near-zero expectation at the optimum, and a near-zero expectation is the
noisiest thing a tally can measure. The exercise splits the variance and shows the split.

Run: python3 chapters/chapter10/files/exercises/ex3_variance.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Dict

import numpy as np

import h2
import vqe


def part_variance(theta: float) -> Dict[str, float]:
    """The variance each tally contributes, in hartree squared per shot."""
    state = h2.ansatz_state(theta)
    values_z = []
    for index in range(4):
        bits = format(index, "02b")
        total = 0.0
        for label in ("IZ", "ZI", "ZZ"):
            sign = 1
            for position, letter in enumerate(reversed(label)):
                if letter != "I" and bits[position] == "1":
                    sign = -sign
            total += h2.TERMS[label] * sign
        values_z.append(total)
    probabilities_z = np.abs(state) ** 2
    mean_z = float((np.array(values_z) * probabilities_z).sum())
    variance_z = float((np.array(values_z) ** 2 * probabilities_z).sum()) - mean_z**2

    x_state = vqe._hadamard_pair() @ state
    probabilities_x = np.abs(x_state) ** 2
    values_x = []
    for index in range(4):
        bits = format(index, "02b")
        sign = 1
        for position, letter in enumerate(reversed("XX")):
            if bits[position] == "1":
                sign = -sign
        values_x.append(h2.TERMS["XX"] * sign)
    mean_x = float((np.array(values_x) * probabilities_x).sum())
    variance_x = float((np.array(values_x) ** 2 * probabilities_x).sum()) - mean_x**2
    return {"z": variance_z, "x": variance_x, "total": variance_z + variance_x}


def checks(check: Callable[[bool, str], None]) -> None:
    theta = -0.2235
    parts = part_variance(theta)
    check(parts["total"] > 0, "the total variance is positive")
    check(abs(parts["z"] + parts["x"] - parts["total"]) < 1e-15, "the parts add to the total")
    check(parts["x"] > parts["z"], "the X tally carries more variance than the Z tally")
    check(abs(parts["x"] / parts["total"] - 0.5) < 0.05, "half of it: the two tallies are equally noisy")

    check(abs(math.sqrt(parts["total"] / 1000) * 1000 - 7.89) < 0.01,
          "the total variance reproduces the 7.89 mHa sigma")

    naive = sum(
        h2.TERMS[label] ** 2 * (1 - vqe.expectation(h2.ansatz_state(theta), label) ** 2)
        for label in ("IZ", "ZI", "ZZ", "XX")
    )
    check(naive < parts["total"], "summing per-term variances understates the total")
    check(abs(math.sqrt(naive / 1000) * 1000 - 6.83) < 0.01, "it gives 6.83 instead of 7.89")

    check(vqe.shots_for(theta) > 20_000, "chemical accuracy needs more than twenty thousand shots")
    check(vqe.shots_for(theta) < 30_000, "and fewer than thirty thousand")

    for bad in (0, -5):
        try:
            vqe.shots_for(theta, bad)
        except ValueError:
            check(True, f"a target of {bad} is refused")
        else:
            check(False, f"a target of {bad} is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
