"""Exercise 2 (extend): the shot count that makes the peak visible.

Run: python3 chapters/chapter19/files/exercises/ex2_shots.py

The pipeline's estimate says what a run costs; it does not say whether the run can
answer the question. This exercise adds the second half: the shots needed to measure a
peak of p to a standard error of sigma, and the cost of those shots.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from pipe import estimate, spec


def shots_for(peak: float, sigma: float) -> int:
    """The shots that give a proportion near `peak` an error of `sigma`."""
    if not 0 < peak < 1:
        raise ValueError(f"a peak is in (0, 1), got {peak}")
    if sigma <= 0:
        raise ValueError(f"a sigma is positive, got {sigma}")
    return int((peak * (1 - peak) / sigma**2) + 0.5)


def plan(task: spec.Task, sigma: float, peak: float = 0.95) -> Dict[str, float]:
    """The shots and the price for a run whose peak is expected to be `peak`."""
    shots = shots_for(peak, sigma)
    priced = spec.Task(**{**task.__dict__, "shots": shots})
    return {"shots": float(shots), "usd": estimate.price(priced.provider, priced.circuits, shots)}


def checks(check: Callable[[bool, str], None]) -> None:
    check(shots_for(0.95, 0.005) == 1900, "a 0.95 peak to 0.005 needs 1,900 shots")
    check(shots_for(0.95, 0.01) == 475, "to 0.01 it needs 475")
    check(shots_for(0.5, 0.01) == 2500, "a coin to 0.01 needs 2,500")
    check(shots_for(0.95, 0.0025) == 7600, "half the error, four times the shots")

    task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm", budget_usd=5.0)
    small = plan(task, 0.005)
    check(small["shots"] == 1900, "the plan for a 0.005 error is 1,900 shots")
    check(small["usd"] == 0.0, "and free on IBM")

    ionq = spec.Task(**{**task.__dict__, "provider": "ionq"})
    expensive = plan(ionq, 0.005)
    check(expensive["usd"] > 900, "the same precision is nearly a thousand dollars on IonQ")
    check(expensive["usd"] > 100 * small["usd"] + 900, "which is the whole argument")

    for bad in (0.0, 1.0):
        try:
            shots_for(bad, 0.01)
        except ValueError:
            check(True, f"a peak of {bad} is refused")
        else:
            check(False, f"a peak of {bad} is refused")

    for bad in (0.0, -0.1):
        try:
            shots_for(0.95, bad)
        except ValueError:
            check(True, f"a sigma of {bad} is refused")
        else:
            check(False, f"a sigma of {bad} is refused")

    check(shots_for(0.9, 0.01) < shots_for(0.5, 0.01),
          "a peak away from a half needs fewer shots than a coin does")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
