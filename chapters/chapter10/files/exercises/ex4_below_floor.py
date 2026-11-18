"""Exercise 4 (break): the variational principle does not apply to estimates.

No state has an energy below the exact ground state, so VQE's expectation never does. A
*measurement* of that expectation does, about half the time, because shot noise scatters
both ways. The exercise measures how often a small tally crosses the floor.

Run: python3 chapters/chapter10/files/exercises/ex4_below_floor.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import h2
import vqe


def below_floor_rate(theta: float, shots: int, trials: int = 400, seed: int = 5) -> float:
    """How often a measured energy lands below the exact ground state."""
    if trials < 1:
        raise ValueError(f"trials must be positive, got {trials}")
    exact = h2.exact_ground()
    hits = 0
    for trial in range(trials):
        z = vqe.tally(theta, "Z", shots, seed=seed * 1000 + trial)
        x = vqe.tally(theta, "X", shots, seed=seed * 1000 + trial + 7919)
        if vqe.energy_from_tallies(z, x)["energy"] < exact:
            hits += 1
    return hits / trials


def checks(check: Callable[[bool, str], None]) -> None:
    theta = -0.2235
    exact = h2.exact_ground()

    check(h2.energy(theta) >= exact - 1e-12, "the expectation itself never crosses the floor")

    small = below_floor_rate(theta, 200, trials=300)
    check(0.35 < small < 0.65, "with two hundred shots, about half the runs land below")
    check(small > 0.3, "so a single run can look better than physics allows")

    large = below_floor_rate(theta, 20_000, trials=200)
    check(abs(large - small) < 0.2, "the rate does not fall with more shots")
    check(0.3 < large < 0.7, "it stays near one half at every size")

    for shots in (100, 1000):
        rate = below_floor_rate(theta, shots, trials=200)
        check(0.3 < rate < 0.7, f"{shots} shots also cross about half the time")
        check(abs(rate - small) < 0.2, f"and {shots} shots is no different from {200}")

    check(vqe.shot_sigma(theta, 20_000) < 2 * h2.CHEMICAL_ACCURACY,
          "at twenty thousand shots the excursions are about two chemical accuracies")
    check(vqe.shot_sigma(theta, 30_000) < h2.CHEMICAL_ACCURACY,
          "at thirty thousand they fall inside it")
    check(vqe.shot_sigma(theta, 200) > 10 * h2.CHEMICAL_ACCURACY,
          "at two hundred they are ten times outside it")

    try:
        below_floor_rate(theta, 200, trials=0)
    except ValueError:
        check(True, "zero trials are refused")
    else:
        check(False, "zero trials are refused")

    check(vqe.shot_sigma(theta, 200) > 3 * h2.CHEMICAL_ACCURACY,
          "two hundred shots are far from chemical accuracy")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
