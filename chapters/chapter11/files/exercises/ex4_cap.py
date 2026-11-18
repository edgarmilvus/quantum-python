"""Exercise 4 (break): the shot count at which the cap refuses.

A budget is a hard stop, and the stop has a shot count attached. The exercise finds it for
two providers and shows how far the same money goes on each.

Run: python3 chapters/chapter11/files/exercises/ex4_cap.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import providers as p


def first_refused(provider: str, cap: float, max_shots: int = 100_000) -> int:
    """The smallest shot count whose quote exceeds the cap."""
    if cap <= 0:
        raise ValueError(f"a cap must be positive, got {cap}")
    price = p.PRICES[provider]
    for shots in range(1, max_shots + 1):
        if price.quote(shots) > cap:
            return shots
    raise ValueError(f"no shot count below {max_shots} exceeds {cap}")


def largest_affordable(provider: str, cap: float) -> int:
    return first_refused(provider, cap) - 1


def comparison(cap: float) -> Dict[str, Dict[str, float]]:
    return {
        name: {
            "first refused": first_refused(name, cap),
            "largest affordable": largest_affordable(name, cap),
            "cost at that size": p.PRICES[name].quote(largest_affordable(name, cap)),
        }
        for name in ("ionq", "braket-qpu")
    }


def checks(check: Callable[[bool, str], None]) -> None:
    check(first_refused("ionq", 5.0) == 59, "with five dollars, IonQ refuses at 59 shots")
    check(largest_affordable("ionq", 5.0) == 58, "so 58 is the largest affordable")
    check(p.PRICES["ionq"].quote(58) <= 5.0, "and it fits")
    check(p.PRICES["ionq"].quote(59) > 5.0, "while 59 does not")

    check(first_refused("braket-qpu", 5.0) > 2000, "Braket's cheaper shots stretch to thousands")
    check(largest_affordable("braket-qpu", 5.0) > largest_affordable("ionq", 5.0),
          "the same money buys more shots there")

    table = comparison(5.0)
    check(set(table) == {"ionq", "braket-qpu"}, "two providers compared")
    check(all(row["cost at that size"] <= 5.0 for row in table.values()), "every affordable quote fits")

    check(first_refused("ionq", 100.0) > first_refused("ionq", 5.0), "a bigger cap buys more shots")

    for bad in (0, -1):
        try:
            first_refused("ionq", bad)
        except ValueError:
            check(True, f"a cap of {bad} is refused")
        else:
            check(False, f"a cap of {bad} is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
