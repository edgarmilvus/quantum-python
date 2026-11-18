"""Exercise 4 (break): two rows, two shot counts, one misleading table.

Run: python3 chapters/chapter18/files/exercises/ex4_compare.py

A device measured at 256 shots has a distance of 0.068 and a simulator measured at
4,096 has 0.067, and the table says the simulator is better by a thousandth. It is
not: the device's number carries a floor of 0.023 and the simulator's 0.007, so most
of the device's distance is noise. Subtracting the floor reverses the ranking, and a
benchmark that does not state its shot count is not a comparison.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import numpy as np

from bench import task


def floor(shots: int, seeds: int = 20) -> float:
    if shots < 1:
        raise ValueError(f"shots must be positive, got {shots}")
    ideal = task.ideal_distribution(3)
    return float(np.mean([task.noise_floor(shots, ideal, seed=seed) for seed in range(seeds)]))


def excess(distance: float, shots: int) -> float:
    """The part of a distance that shot noise cannot explain."""
    return max(0.0, distance - floor(shots))


def checks(check: Callable[[bool, str], None]) -> None:
    device = 0.0681
    device_shots = 256
    simulator = 0.0670
    simulator_shots = 4096

    check(simulator < device, "on the raw distances the simulator looks better by a thousandth")

    device_excess = excess(device, device_shots)
    simulator_excess = excess(simulator, simulator_shots)
    check(device_excess < simulator_excess, "on the excess over the floor the device is better")
    check(device_excess < 0.05, "because most of the device's number is its own floor")
    check(abs(floor(device_shots) - 0.023) < 0.01, "the floor at 256 shots is about 0.023")

    check(device_excess < device, "the excess is smaller than the raw distance")
    check(device_excess > 0.03, "and still large, because the device really is off")

    check(excess(0.0, 4096) == 0.0, "an exact run has no excess")
    check(excess(0.003, 4096) == 0.0, "and a distance below the floor has none either")

    pair = [("device", device, device_shots), ("simulator", simulator, simulator_shots)]
    raw_order = sorted(pair, key=lambda item: item[1])
    fair_order = sorted(pair, key=lambda item: excess(item[1], item[2]))
    check(raw_order[0][0] == "simulator", "the raw ordering puts the simulator first")
    check(fair_order[0][0] == "device", "the fair one puts the device first")

    for bad in (0, -4):
        try:
            floor(bad)
        except ValueError:
            check(True, f"{bad} shots is refused")
        else:
            check(False, f"{bad} shots is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
