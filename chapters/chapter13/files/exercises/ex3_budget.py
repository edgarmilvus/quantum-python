"""Exercise 3 (measure): what one optimisation costs before it starts.

Run: python3 chapters/chapter13/files/exercises/ex3_budget.py

Two budgets multiply. The gradient's circuit count grows with the layers and the
edges, and each circuit's shot count grows with the square of the precision the
optimiser wants. The exercise finds the depth at which twenty steps stop fitting
in a five-minute runtime allowance.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import numpy as np

from qaoa import optimize

SPREAD = 1.13          # the per-shot standard deviation of the cut, measured in demo 05
SECONDS_PER_CIRCUIT = 0.333   # the recorded run's 12 seconds for 36 circuits
ALLOWANCE = 300.0      # seconds of runtime the exercise is allowed to spend
EDGES = 5


def plan(p: int, shots: int, steps: int) -> Dict[str, float]:
    """Circuits, shots and seconds for one optimisation."""
    budget = optimize.budget(p, EDGES, shots, steps)
    return {
        "circuits per gradient": budget["circuits per gradient"],
        "circuits": budget["circuits for the run"],
        "shots": budget["shots for the run"],
        "seconds": budget["circuits for the run"] * SECONDS_PER_CIRCUIT,
    }


def deepest(shots: int, steps: int, allowance: float = ALLOWANCE, limit: int = 12) -> int:
    """The largest p whose twenty-step optimisation fits the allowance."""
    if allowance <= 0:
        raise ValueError(f"an allowance is positive, got {allowance}")
    best = 0
    for p in range(1, limit + 1):
        if plan(p, shots, steps)["seconds"] <= allowance:
            best = p
    if best == 0:
        raise ValueError(f"not even one layer fits {allowance} seconds")
    return best


def checks(check: Callable[[bool, str], None]) -> None:
    first = plan(1, 1024, 20)
    check(first["circuits per gradient"] == 12, "one layer on five edges needs twelve circuits a gradient")
    check(first["circuits"] == 240, "twenty steps need 240 circuits")
    check(first["shots"] == 245760, "and 245,760 shots")
    check(abs(first["seconds"] - 79.9) < 0.5, "which is about eighty seconds of runtime")

    rows = [plan(p, 1024, 20) for p in (1, 2, 3, 4)]
    check([row["circuits"] for row in rows] == [240, 480, 720, 960], "the circuit count is linear in p")
    check(rows[3]["seconds"] > ALLOWANCE, "four layers do not fit the allowance")
    check(deepest(1024, 20) == 3, "so the deepest affordable is three layers")
    check(abs(rows[2]["seconds"] - 240.0) < 1.0, "at 240 seconds for twenty steps")

    check(deepest(1024, 20, allowance=100.0) == 1, "a hundred seconds allows one layer")
    check(deepest(1024, 40) == 1, "forty steps at the same allowance allows one")

    for gap in (0.4, 0.2, 0.1, 0.05):
        check(optimize.shots_to_resolve(gap, SPREAD) > 0, f"a gap of {gap} has a shot count")
    check(optimize.shots_to_resolve(0.2, SPREAD) == 128, "resolving 0.2 needs 128 shots")
    check(optimize.shots_to_resolve(0.1, SPREAD) == 511, "halving the gap quadruples the shots")
    check(optimize.shots_to_resolve(0.05, SPREAD) == 2044, "and halving it again quadruples them again")
    check(abs(optimize.shots_to_resolve(0.1, SPREAD) / optimize.shots_to_resolve(0.2, SPREAD) - 4.0) < 0.01,
          "the ratio is four to within a rounding shot")

    doubled = plan(1, 4096, 20)
    check(doubled["circuits"] == first["circuits"], "four times the shots buys no extra circuits")
    check(doubled["shots"] == 4 * first["shots"], "only four times the shots")
    check(abs(doubled["seconds"] - first["seconds"]) < 0.1,
          "so at 0.333 s a circuit the runtime tracks circuits, not shots")
    check(SECONDS_PER_CIRCUIT * 36 < 15.0,
          "the recorded run spent 12 seconds on 36 circuits, so overhead dominates a 1,024-shot circuit")

    for bad in (0.0, -0.5):
        try:
            deepest(1024, 20, allowance=bad)
        except ValueError:
            check(True, f"an allowance of {bad} is refused")
        else:
            check(False, f"an allowance of {bad} is refused")

    try:
        optimize.shots_to_resolve(0.0, SPREAD)
    except ValueError:
        check(True, "a zero gap is refused")
    else:
        check(False, "a zero gap is refused")

    check(np.isfinite(first["seconds"]), "every planned number is finite")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
