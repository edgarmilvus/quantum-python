"""Exercise 1 (repair): the CHSH combination with the wrong signs.

A dashboard computes S = E(ab) + E(ab') + E(a'b) + E(a'b'). Every individual
expectation is right, the total is wrong, and on an ideal pair it reports 1.414
instead of 2.828 — which still looks like a violation, which is why nobody checks.

Run: python3 chapters/chapter04/files/exercises/ex1_signs.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import bell


def wrong_sum(expectations: Dict[str, float]) -> float:
    """The defect: all four terms added."""
    return sum(expectations[name] for name in bell.SETTINGS)


def right_sum(expectations: Dict[str, float]) -> float:
    """S = E(ab) - E(ab') + E(a'b) + E(a'b')."""
    return bell.chsh(expectations)


def checks(check: Callable[[bool, str], None]) -> None:
    ideal = bell.simulate()

    check(abs(right_sum(ideal) - 2.8284271247461903) < 1e-12, "the repaired combination gives 2 sqrt 2")
    check(abs(wrong_sum(ideal) - 1.4142135623730951) < 1e-12, "the defect gives 1.414 on the same data")
    check(wrong_sum(ideal) < right_sum(ideal), "the defect understates the violation")

    # Both formulas agree when the second setting happens to be zero.
    flat = {"ab": 0.7, "ab_prime": 0.0, "a_prime_b": 0.7, "a_prime_b_prime": 0.7}
    check(abs(wrong_sum(flat) - right_sum(flat)) < 1e-12, "with E(ab') = 0 the two agree")

    # Sign of the second term is the whole difference.
    check(abs(right_sum(ideal) - 2 * ideal["ab"] - 2 * ideal["a_prime_b"]) < 1e-12,
          "the repaired sum is twice the two positive terms")

    zero = {name: 0.0 for name in bell.SETTINGS}
    check(right_sum(zero) == 0.0, "all-zero expectations give zero in both")

    try:
        right_sum({"ab": 0.1})
    except ValueError:
        check(True, "a partial set is refused by the repair")
    else:
        check(False, "a partial set is refused by the repair")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
