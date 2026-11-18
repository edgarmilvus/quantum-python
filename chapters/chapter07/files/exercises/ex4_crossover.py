"""Exercise 4 (break): the iteration count at which the search is worse than guessing.

The success curve is a sine, so it comes back down. The crossover is the first k whose
probability is below 1/N, the chance of finding the item by pointing at random. Past that
point the circuit is a worse guess than a coin.

Run: python3 chapters/chapter07/files/exercises/ex4_crossover.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Dict, List

import grover


def first_below_uniform(n: int, limit: int = 10_000) -> int:
    """The first k whose success probability is under 1/N."""
    if n < 2:
        raise ValueError(f"a search needs at least two items, got n={n}")
    baseline = 1.0 / (1 << n)
    for steps in range(1, limit + 1):
        if grover.success_probability(0, n, steps) < baseline:
            return steps
    raise ValueError(f"no crossover within {limit} iterations at n={n}")


def curve_above(n: int, steps: int) -> float:
    baseline = 1.0 / (1 << n)
    return grover.success_probability(0, n, steps) / baseline


def summary(n: int) -> Dict[str, float]:
    size = 1 << n
    optimal = grover.optimal_iterations(size)
    crossover = first_below_uniform(n)
    return {
        "N": size,
        "optimal": optimal,
        "peak": grover.success_probability(0, n, optimal),
        "crossover": crossover,
        "at_crossover": grover.success_probability(0, n, crossover),
    }


def checks(check: Callable[[bool, str], None]) -> None:
    three = summary(3)
    check(three["optimal"] == 2, "at n=3 the peak is at two iterations")
    check(abs(three["peak"] - 0.9453125) < 1e-9, "and the peak is 0.9453")
    check(three["crossover"] == 4, "the crossover is the fourth iteration")
    check(abs(three["at_crossover"] - 0.01220703125) < 1e-9, "where the chance is 1.2%")
    check(three["at_crossover"] < 1 / 8, "which is below uniform guessing")

    for n in (3, 4, 5):
        row = summary(n)
        check(row["crossover"] > row["optimal"], f"n={n}: the crossover is past the optimum")
        check(row["at_crossover"] < 1 / row["N"], f"n={n}: and it is below uniform")

    check(curve_above(3, 2) > 7, "at the peak the odds are more than seven times uniform")
    check(curve_above(3, 4) < 0.1, "at the crossover they are under a tenth")

    try:
        first_below_uniform(1)
    except ValueError:
        check(True, "one qubit is refused")
    else:
        check(False, "one qubit is refused")

    check(grover.success_probability(0, 3, 4) < grover.success_probability(0, 3, 5),
          "the curve resumes climbing after the trough")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
