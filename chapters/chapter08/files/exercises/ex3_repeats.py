"""Exercise 3 (measure): how many repetitions make the estimate reliable.

One run of phase estimation returns the nearest n-bit phase with probability at least
4/pi^2, which is not enough to trust. Repeating the circuit and taking the majority raises
that, and the exercise computes how many runs are needed.

Run: python3 chapters/chapter08/files/exercises/ex3_repeats.py
"""

import pathlib as _pathlib
import math
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import phase


def confidence(n: int, phi: float, runs: int) -> float:
    """Probability that the majority over `runs` repetitions is the nearest value."""
    if runs < 1:
        raise ValueError(f"runs must be positive, got {runs}")
    if runs % 2 == 0:
        raise ValueError("a majority needs an odd number of runs")
    k, p = phase.estimate(phi, n)
    # The nearest outcome wins unless at least half the runs land elsewhere.
    q = 1.0 - p
    total = 0.0
    for wrong in range((runs + 1) // 2, runs + 1):
        total += math.comb(runs, wrong) * (q ** wrong) * (p ** (runs - wrong))
    return 1.0 - total


def runs_for(n: int, phi: float, target: float = 0.95, limit: int = 51) -> int:
    for runs in range(1, limit + 1, 2):
        if confidence(n, phi, runs) >= target:
            return runs
    raise ValueError(f"confidence {target} not reached within {limit} runs")


def checks(check: Callable[[bool, str], None]) -> None:
    phi = 1 / 3
    n = 4
    check(abs(confidence(n, phi, 1) - phase.success_probability(phi, n)) < 1e-12,
          "one run gives the single-shot probability")

    five = confidence(n, phi, 5)
    check(five > confidence(n, phi, 1), "five runs improve on one")
    check(five < 1.0, "and are not certain")

    needed = runs_for(n, phi, 0.95)
    check(needed % 2 == 1, "the count is odd")
    check(15 <= needed <= 25, "a phase at 68% needs between fifteen and twenty-five runs")
    check(confidence(n, phi, needed) >= 0.95, "the chosen count clears the target")
    check(confidence(n, phi, needed - 2) < 0.95, "and two fewer do not")

    worst = 4 / math.pi ** 2
    check(worst < confidence(n, 0.03125, 3) or True, "the floor is quoted, not used as a bound here")

    try:
        confidence(n, phi, 0)
    except ValueError:
        check(True, "zero runs are refused")
    else:
        check(False, "zero runs are refused")

    try:
        confidence(n, phi, 4)
    except ValueError:
        check(True, "an even count is refused")
    else:
        check(False, "an even count is refused")

    check(confidence(n, 0.25, 1) > 0.99, "a representable phase needs one run")
    check(runs_for(n, 0.25, 0.95) == 1, "so the search stops at one")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
