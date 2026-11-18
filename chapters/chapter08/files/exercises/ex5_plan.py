"""Exercise 5, file 3 of 3: the wiring.

Chooses a precision and a phase, prints the plan, and prints the estimation on its own so
the two can be compared by eye.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import phase
from plan_core import bits_for, plan, rows, runs_for
from plan_render import render


def plan_text(precision: float, phi: float = 1 / 3) -> str:
    return render(rows(plan(precision, phi)), f"estimation plan for precision {precision}")


def checks(check: Callable[[bool, str], None]) -> None:
    check(bits_for(0.125) == 3, "one eighth needs three bits")
    check(bits_for(0.1) == 4, "a tenth needs four")
    check(bits_for(0.01) == 7, "a hundredth needs seven")
    check(bits_for(1 / 1024) == 10, "one part in a thousand needs ten")

    result = plan(0.1, 1 / 3)
    check(result["bits"] == 4, "the plan uses four bits")
    check(result["single_shot"] > 0.6, "a single shot is better than sixty percent")
    check(result["runs"] % 2 == 1, "the run count is odd")
    check(result["runs"] >= 3, "and at least three")
    check(result["gates"] > 0 and result["depth"] > 0, "the cost is positive")
    check(result["total_gates"] == result["gates"] * result["runs"], "the total is the product")

    text = plan_text(0.1)
    check("estimation plan" in text, "the title names the plan")
    check("runs for target" in text, "the rows are named")
    check(text.count("\n") >= 8, "a header and seven rows")
    check(plan_text(0.1) == plan_text(0.1), "the wiring is deterministic")

    for bad in (0.0, 1.0, -0.5):
        try:
            bits_for(bad)
        except ValueError:
            check(True, f"precision {bad} is refused")
        else:
            check(False, f"precision {bad} is refused")

    check(runs_for(4, 0.25) == 1, "a representable phase needs one run")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
