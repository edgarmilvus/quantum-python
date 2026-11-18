"""Exercise 2 (extend): continued fractions with a noisy phase.

The measured k carries no error in the chapter's simulation, and a device would add some.
The exercise measures how much error the continued-fraction step tolerates, and shows that
the tolerance depends on the number of ancillas rather than on the order alone.

Run: python3 chapters/chapter09/files/exercises/ex2_noise.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List

import order


def band(centre: int, ancillas: int, n: int, limit: int = 64) -> int:
    """How many consecutive k around `centre` recover the same denominator."""
    target = order.recover_order(centre, ancillas, n)
    width = 0
    for offset in range(1, limit):
        if order.recover_order(centre + offset, ancillas, n) != target:
            break
        width += 1
    return width


def checks(check: Callable[[bool, str], None]) -> None:
    check(order.recover_order(16, 6, 15) == 4, "the exact phase recovers four")
    check(order.recover_order(15, 6, 15) == 13, "one unit below lands on thirteen")
    check(order.recover_order(17, 6, 15) == 15, "one unit above lands on fifteen")
    check(order.recover_order(18, 6, 15) == 7, "and two units above on seven")

    check(order.recover_order(21, 6, 15) == 3, "one third of the register recovers three")
    check(order.recover_order(0, 6, 15) == 1, "k equal to zero recovers one, which is a failure")

    wide = [order.recover_order(k, 10, 21) for k in (341, 342, 343, 344)]
    check(set(wide) == {3}, "at ten ancillas four consecutive k all recover three")
    check(band(342, 10, 21) >= 3, "so the band is at least three wide")

    check(band(16, 6, 15) == 0, "at six ancillas the band around sixteen is empty")
    check(band(342, 10, 21) > band(16, 6, 15), "more ancillas widen it")

    for k in range(0, 64):
        value = order.recover_order(k, 6, 15)
        check(1 <= value <= 15, f"k={k} gives a denominator between one and the modulus")

    check(order.recover_order(5, 6, 15) == 13, "a phase near 5/64 also lands on thirteen")
    check(order.recover_order(9, 6, 15) == 7, "and nine on seven")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
