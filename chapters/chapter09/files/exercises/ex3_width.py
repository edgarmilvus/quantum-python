"""Exercise 3 (measure): how many ancillas a reliable run needs.

For N=21 at eight ancillas one run succeeds 0.2856 of the time. The exercise measures how
that rate moves with the width, and finds the width at which the success probability is
better than even.

Run: python3 chapters/chapter09/files/exercises/ex3_width.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import order


def rate(n: int, a: int, bits: int, ancillas: int) -> float:
    return order.quantum_success(a, n, bits, ancillas)["probability"]


def scan(n: int, a: int, bits: int, widths: List[int]) -> Dict[int, float]:
    return {width: rate(n, a, bits, width) for width in widths}


def first_above(n: int, a: int, bits: int, target: float, limit: int = 11) -> int:
    for width in range(bits, limit + 1):
        if rate(n, a, bits, width) >= target:
            return width
    raise ValueError(f"no width below {limit} reaches {target}")


def attempts_for(probability: float, target: float = 0.95) -> int:
    """How many runs until the chance of at least one success reaches the target."""
    if not 0.0 < probability < 1.0:
        raise ValueError(f"a success probability is in (0, 1), got {probability}")
    import math

    runs = 1
    while 1.0 - (1.0 - probability) ** runs < target:
        runs += 1
        if runs > 10_000:
            raise ValueError("unreachable target")
    return runs


def checks(check: Callable[[bool, str], None]) -> None:
    check(abs(rate(15, 7, 4, 6) - 0.5) < 1e-3, "fifteen at six ancillas succeeds half the time")
    check(abs(rate(21, 2, 5, 8) - 0.2856) < 1e-3, "twenty-one at eight ancillas succeeds 0.286")

    table = scan(21, 2, 5, [6, 7, 8, 9, 10])
    check(len(table) == 5, "the scan has five widths")
    check(table[6] < 0.01, "at six ancillas the phase grid is too coarse to work")
    check(table[10] > table[8] > table[6], "the rate climbs with the width")
    check(table[10] < 1 / 3, "and never passes the ceiling the order sets")

    width = first_above(21, 2, 5, 0.30)
    check(width == 9, "nine ancillas are the first to clear thirty percent")
    check(rate(21, 2, 5, width) >= 0.30, "and they do clear it")

    check(abs(2 / 6 - 1 / 3) < 1e-12, "the ceiling for order six is one third")
    check(abs(rate(15, 7, 4, 4) - rate(15, 7, 4, 8)) < 1e-9, "fifteen is already at its ceiling at four ancillas")
    check(abs(rate(15, 7, 4, 8) - 0.5) < 1e-9, "which is one half for order four")

    check(attempts_for(0.5) == 5, "a half chance needs five runs for 95%")
    check(attempts_for(0.2856) > attempts_for(0.5), "a smaller chance needs more runs")
    check(attempts_for(0.9) == 2, "a ninety percent chance needs two")

    try:
        attempts_for(0.0)
    except ValueError:
        check(True, "a zero probability is refused")
    else:
        check(False, "a zero probability is refused")

    try:
        first_above(21, 2, 5, 0.9, limit=10)
    except ValueError:
        check(True, "an unreachable target is refused")
    else:
        check(False, "an unreachable target is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
