"""Exercise 4 (break): where the first-order error model stops being usable.

Budget arithmetic usually adds errors: n gates at e each cost n*e. The exact
composition is 1-(1-e)^n, and the two agree only while n*e is small. This file finds
the gate count where adding is no longer good enough.

Run: python3 chapters/chapter03/files/exercises/ex4_first_order.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Tuple


def exact(error: float, gates: int) -> float:
    if not 0.0 <= error < 1.0:
        raise ValueError(f"an error rate must be inside [0, 1), got {error}")
    if gates < 0:
        raise ValueError(f"gates cannot be negative, got {gates}")
    return 1.0 - (1.0 - error) ** gates


def first_order(error: float, gates: int) -> float:
    if not 0.0 <= error < 1.0:
        raise ValueError(f"an error rate must be inside [0, 1), got {error}")
    if gates < 0:
        raise ValueError(f"gates cannot be negative, got {gates}")
    return error * gates


def relative_gap(error: float, gates: int) -> float:
    """How far the added error is from the exact one, as a fraction of the exact one."""
    exact_value = exact(error, gates)
    if exact_value == 0.0:
        return 0.0
    return abs(first_order(error, gates) - exact_value) / exact_value


def first_gap_above(error: float, threshold: float, limit: int = 100_000) -> int:
    if not 0.0 < threshold < 1.0:
        raise ValueError(f"threshold must be inside (0, 1), got {threshold}")
    for gates in range(1, limit + 1):
        if relative_gap(error, gates) > threshold:
            return gates
    raise ValueError(f"the gap never exceeds {threshold} within {limit} gates")


def checks(check: Callable[[bool, str], None]) -> None:
    e = 0.01
    check(abs(exact(e, 1) - 0.01) < 1e-12, "one gate is the same in both models")
    check(abs(exact(e, 2) - 0.0199) < 1e-12, "two gates compose to 0.0199, not 0.02")
    check(first_order(e, 2) > exact(e, 2), "adding always overestimates")

    crossing = first_gap_above(e, 0.10)
    check(15 <= crossing <= 30, "at 1% per gate the 10% gap arrives around twenty gates")
    check(relative_gap(e, crossing) > 0.10, "the crossing is where the gap passes 10%")
    check(relative_gap(e, crossing - 1) <= 0.10, "and the gate before it does not")

    check(relative_gap(e, 100) > relative_gap(e, 10), "the gap grows with the gate count")
    check(abs(exact(e, 10_000) - 1.0) < 1e-12, "ten thousand gates at 1% are saturated")

    check(first_gap_above(0.0001, 0.10) > crossing, "a smaller error rate buys more gates")

    for bad in (-0.1, 1.0, 1.5):
        try:
            exact(bad, 1)
        except ValueError:
            check(True, f"error rate {bad} is refused")
        else:
            check(False, f"error rate {bad} is refused")

    try:
        first_gap_above(e, 0.0)
    except ValueError:
        check(True, "a zero threshold is refused")
    else:
        check(False, "a zero threshold is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
