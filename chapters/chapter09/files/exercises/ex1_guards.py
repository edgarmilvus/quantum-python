"""Exercise 1 (repair): a factor function that skips the two guards.

The classical half of Shor has two ways to fail: an odd order, and a half that is 1 or -1.
A function that forgets them returns gcds that are trivially right — 1 and N — and reports
them as factors.

Run: python3 chapters/chapter09/files/exercises/ex1_guards.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Optional, Tuple

import order


def unguarded(a: int, n: int, r: int) -> Tuple[int, int]:
    """The defect: two gcds, no checks."""
    half = pow(a, r // 2, n)
    return math.gcd(half - 1, n), math.gcd(half + 1, n)


def guarded(a: int, n: int, r: int) -> Optional[Tuple[int, int]]:
    return order.factors_from_order(a, n, r)


def checks(check: Callable[[bool, str], None]) -> None:
    check(guarded(7, 15, 4) == (3, 5), "the guard lets a good case through")
    check(unguarded(7, 15, 4) == (3, 5), "and the defect agrees on it")

    check(guarded(11, 35, 3) is None, "an odd order is refused by the guard")
    check(unguarded(11, 35, 3) == (5, 1), "the defect returns a factor and a one for an odd order")

    check(guarded(14, 15, 2) is None, "a half of minus one is refused by the guard")
    check(unguarded(14, 15, 2) == (1, 15), "the defect reports the trivial factorisation again")

    check(unguarded(4, 15, 2) == (3, 5), "a half of four works in both")
    check(guarded(4, 15, 2) == (3, 5), "and the guard does not block it")

    check(unguarded(14, 15, 0) == (15, 1), "a zero order gives a trivial pair in the defect")
    trivial = unguarded(14, 15, 2)
    check(trivial in ((1, 15), (15, 1)), "the minus-one failure reports the trivial factorisation")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
