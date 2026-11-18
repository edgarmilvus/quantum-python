"""Exercise 3 (measure): how many gates before an average stops working.

Run: python3 chapters/chapter12/files/exercises/ex3_leverage.py

Two models, one device. The average rate fitted on CHSH is 0.0166 per gate; the
per-gate table from the calibration runs from 0.0033 to 0.0046. On one gate they
differ by one point in the peak. On forty-five they differ by a third of the
experiment, and the count where they part is five.
"""

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import numpy as np

from noise import device, fit

IDEAL = 0.9453125
RATE_AVERAGE = 0.01661
CALIBRATION = device.load_json(device.CALIBRATION_RUN)
EDGES = [float(op["error"]) for op in CALIBRATION["ops"] if len(op["qubits"]) == 2]
SINGLES = [float(op["error"]) for op in CALIBRATION["ops"] if len(op["qubits"]) == 1]


def edge_survival(gates: int) -> float:
    """The product over the first `gates` recorded edges, cycling when asked for more."""
    if gates < 0:
        raise ValueError(f"gates must be non-negative, got {gates}")
    if not EDGES:
        raise ValueError("the calibration has no two-qubit gates")
    product = 1.0
    for index in range(gates):
        product *= 1 - EDGES[index % len(EDGES)]
    return product


def peaks(gates: int) -> Dict[str, float]:
    """Both models' predicted probability of the intended outcome."""
    average = IDEAL * fit.predict(RATE_AVERAGE, gates)
    edge = IDEAL * edge_survival(gates)
    return {"average": average, "edge": edge, "gap": edge - average}


def table(counts: List[int]) -> List[Dict[str, float]]:
    return [{"gates": gates, **peaks(gates)} for gates in counts]


def first_disagreement(threshold: float = 0.05, limit: int = 500) -> int:
    """The first gate count at which the two models differ by more than `threshold`."""
    if threshold <= 0:
        raise ValueError(f"a threshold must be positive, got {threshold}")
    for gates in range(1, limit + 1):
        if peaks(gates)["gap"] > threshold:
            return gates
    raise ValueError(f"the models never disagree by {threshold} below {limit} gates")


def half_signal(rate: float) -> int:
    """The number of gates after which half the ideal peak is left."""
    if not 0 < rate < 1:
        raise ValueError(f"a rate is in (0, 1), got {rate}")
    return int(np.ceil(np.log(0.5) / np.log(1 - rate)))


def checks(check: Callable[[bool, str], None]) -> None:
    check(len(EDGES) == 45, "the calibration carries 45 two-qubit edges")

    one = peaks(1)
    check(abs(one["average"] - 0.9296) < 1e-3, "one gate: the average model predicts 0.9296")
    check(abs(one["edge"] - 0.9410) < 1e-3, "the per-gate model predicts 0.9410")
    check(one["gap"] < 0.02, "so on a single gate they are within two points")

    five = peaks(5)
    check(five["gap"] > 0.05, "five gates: the gap passes five points")
    check(first_disagreement(0.05) == 5, "and five is the first count where it does")

    forty_five = peaks(45)
    check(abs(forty_five["average"] - 0.4449) < 1e-3, "forty-five gates: the average says 0.4449")
    check(abs(forty_five["edge"] - 0.7920) < 1e-3, "the per-gate table says 0.7920 on two-qubit gates alone")
    check(forty_five["gap"] > 0.3, "a gap larger than the signal the average model still claims")

    check(half_signal(RATE_AVERAGE) == 42, "the average loses half the signal after 42 gates")
    check(half_signal(0.0033) == 210, "a median edge takes 210")
    check(half_signal(0.0033) > 4 * half_signal(RATE_AVERAGE), "a factor of more than four")

    rows = table([1, 5, 10, 45])
    check(len(rows) == 4, "four rows")
    check(all(row["average"] < row["edge"] for row in rows), "the average is pessimistic at every count")
    check(rows[-1]["gap"] == max(row["gap"] for row in rows), "and the gap grows with the count")
    check(abs(peaks(0)["average"] - IDEAL) < 1e-12, "zero gates leaves the ideal peak")

    check(edge_survival(46) < edge_survival(45), "the product keeps falling past the last recorded edge")
    single_survival = 1.0
    for rate in SINGLES:
        single_survival *= 1 - rate
    check(abs(forty_five["edge"] * single_survival - 0.7779) < 1e-3,
          "the 169 single-qubit gates take 0.7920 down to the 0.7779 the chapter quotes")

    for bad in (0.0, -0.1):
        try:
            first_disagreement(bad)
        except ValueError:
            check(True, f"a threshold of {bad} is refused")
        else:
            check(False, f"a threshold of {bad} is refused")

    try:
        half_signal(1.0)
    except ValueError:
        check(True, "a rate of one has no half point")
    else:
        check(False, "a rate of one has no half point")

    try:
        edge_survival(-1)
    except ValueError:
        check(True, "a negative gate count is refused")
    else:
        check(False, "a negative gate count is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
