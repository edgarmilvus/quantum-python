"""Exercise 3 (measure): the floor moves with the shot count, as a square root.

Run: python3 chapters/chapter18/files/exercises/ex3_floor.py

A distance computed from n shots carries a floor set by the sampling, so comparing
two rows at different shot counts compares two floors. The exercise measures the
floor at four counts, checks the scaling, and finds the count at which the floor is
small enough that a device's distance is the signal.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import numpy as np

from bench import task

DEVICE = 0.0681


def mean_floor(shots: int, seeds: int = 20) -> float:
    ideal = task.ideal_distribution(3)
    return float(np.mean([task.noise_floor(shots, ideal, seed=seed) for seed in range(seeds)]))


def shots_for(target: float) -> int:
    """The smallest power of four whose floor is below the target."""
    if target <= 0:
        raise ValueError(f"a target is positive, got {target}")
    shots = 256
    while mean_floor(shots) > target:
        shots *= 4
    return shots


def checks(check: Callable[[bool, str], None]) -> None:
    values: Dict[int, float] = {n: mean_floor(n) for n in (256, 1024, 4096, 16384)}

    check(abs(values[1024] - 0.0123) < 0.004, "1,024 shots give a floor near 0.012")
    check(abs(values[4096] - 0.0069) < 0.003, "4,096 near 0.007")
    check(values[1024] > values[4096] > values[16384], "more shots lower the floor")

    ratio = values[256] / values[4096]
    check(1.8 < ratio < 5.5, "four times the shots roughly halve it")

    check(shots_for(DEVICE / 10) >= 1024, "a tenth of the device's distance needs thousands of shots")
    check(mean_floor(4096) < DEVICE / 5, "at 4,096 shots the floor is well below the device")

    ideal = task.ideal_distribution(3)
    check(task.total_variation({"000": 2048, "111": 2048}, ideal) == 0.0,
          "a floor is not a defect: an exact histogram has none")

    for bad in (0, -1):
        try:
            shots_for(bad)
        except ValueError:
            check(True, f"a target of {bad} is refused")
        else:
            check(False, f"a target of {bad} is refused")

    check(abs(mean_floor(4096) - task.noise_floor(4096, ideal, seed=0)) < 0.01,
          "one seed is within a point of the mean")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
