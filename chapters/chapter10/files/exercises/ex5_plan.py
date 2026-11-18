"""Exercise 5, file 3 of 3: the wiring.

Chooses three angles and two shot counts, prints the reports, and shows that the same
angle is inside chemical accuracy at one size and outside at another.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import h2
from plan_core import evaluate, rows
from plan_render import render


def report(theta: float, shots: int) -> str:
    return render(rows(evaluate(theta, shots)), f"energy at theta={theta:.4f}, {shots} shots")


def checks(check: Callable[[bool, str], None]) -> None:
    optimum = evaluate(-0.2235, 10_000)
    check(abs(optimum["energy"] - h2.exact_ground()) < 0.02, "at the optimum the estimate is close")
    check(abs(optimum["gap"]) * 1000 < 20, "within twenty mHa")
    check(optimum["sigma"] > 0, "the uncertainty is positive")

    hartree_fock = evaluate(0.0, 10_000)
    check(abs(hartree_fock["energy"] - h2.energy(0.0)) < 0.02, "at zero it lands near Hartree-Fock")
    check(hartree_fock["energy"] > optimum["energy"], "which is above the optimum")

    small = evaluate(-0.2235, 200)
    check(small["sigma"] > optimum["sigma"], "fewer shots mean a bigger sigma")
    check(not small["within_accuracy"], "and two hundred shots miss chemical accuracy")

    big = evaluate(-0.2235, 40_000)
    check(big["sigma"] < optimum["sigma"], "more shots mean a smaller sigma")

    text = report(-0.2235, 10_000)
    check("energy at theta" in text, "the title names the angle")
    check("within accuracy" in text, "the verdict is a row")
    check(text.count("\n") >= 9, "a header and seven rows")
    check(report(-0.2235, 10_000) == text, "the same seed gives the same report")

    for bad in (0, -1):
        try:
            evaluate(-0.2235, bad)
        except ValueError:
            check(True, f"{bad} shots are refused")
        else:
            check(False, f"{bad} shots are refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
