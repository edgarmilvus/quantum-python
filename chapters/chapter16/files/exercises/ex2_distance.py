"""Exercise 2 (extend): a seventh qubit, and a zero that is not a zero.

Run: python3 chapters/chapter16/files/exercises/ex2_distance.py

At a five percent physical rate the logical error falls from 0.00725 to 0.00116 to
0.00019 as the distance goes 3, 5, 7: a factor of six per two qubits. A device run
that returns zero logical errors in 4,096 shots has not measured zero, and the
Wilson interval is what turns that zero into a number the report can carry.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from ecc import code, sim

DISTANCES = (3, 5, 7)


def table(p: float) -> List[Dict[str, float]]:
    rows = []
    previous = None
    for distance in DISTANCES:
        value = code.logical_error_ideal(distance, p)
        rows.append({"distance": distance, "logical": value, "ratio": (previous / value) if previous else 0.0})
        previous = value
    return rows


def zero_interval(shots: int) -> Dict[str, float]:
    low, high = code.wilson(0.0, shots)
    return {"low": low, "high": high}


def checks(check: Callable[[bool, str], None]) -> None:
    rows = {row["distance"]: row for row in table(0.05)}

    check(abs(rows[3]["logical"] - 0.00725) < 1e-4, "d=3 at p=0.05 is 0.00725")
    check(abs(rows[5]["logical"] - 0.00116) < 1e-4, "d=5 is 0.00116")
    check(abs(rows[7]["logical"] - 0.00019) < 2e-5, "d=7 is 0.00019")

    check(abs(rows[5]["ratio"] - 6.24) < 0.2, "each step of two qubits divides by six")
    check(abs(rows[7]["ratio"] - 6.16) < 0.2, "and the second step by six again")
    check(rows[7]["logical"] < rows[5]["logical"] < rows[3]["logical"], "so more distance is monotonically better")

    check(abs(code.logical_error_ideal(7, 0.0)) < 1e-15, "at p=0 the code is exact")
    check(code.logical_error_ideal(7, 0.5) == 0.5, "at p=0.5 it is a coin flip")
    check(code.logical_error_ideal(7, 0.1) < code.logical_error_ideal(5, 0.1), "and it stays ordered at p=0.1")

    interval = zero_interval(4096)
    check(interval["high"] < 0.001, "a zero in 4,096 shots is below 0.001")
    check(interval["low"] == 0.0, "the interval starts at zero")
    wider = zero_interval(100)
    check(wider["high"] > interval["high"], "fewer shots widen it")

    wrong, trials = sim.sample_bitflips(7, 0.05, 40000, seed=4)
    check(abs(wrong / trials - rows[7]["logical"]) < 0.001, "the Monte Carlo agrees for d=7")

    for bad in (2, 4, 0):
        try:
            code.Repetition(bad)
        except ValueError:
            check(True, f"a distance of {bad} is refused")
        else:
            check(False, f"a distance of {bad} is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
