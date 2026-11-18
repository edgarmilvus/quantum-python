"""Exercise 5, file 3 of 3: the wiring.

Chooses the moduli, prints their plans, and shows the one case where the base shares a
factor with the modulus and the quantum machine is not needed at all.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import order
from plan_core import plan, rows
from plan_render import render


def plan_text(n: int, a: int) -> str:
    return render(rows(plan(n, a)), f"factoring plan for {n} base {a}")


def checks(check: Callable[[bool, str], None]) -> None:
    fifteen = plan(15, 7)
    check(fifteen["order"] == 4, "seven has order four modulo fifteen")
    check(fifteen["factors"] == (3, 5), "and the classical half gives three and five")
    check(fifteen["bits"] == 4, "four bits of modulus")
    check(fifteen["ancillas"] == 8, "eight ancillas")
    check(fifteen["qubits"] == 12, "twelve qubits in total")
    check(abs(fifteen["probability"] - 0.5) < 1e-3, "one run succeeds half the time")
    check(fifteen["attempts"] == 5, "so five runs cover ninety-five percent")

    big = plan(2048, 3)
    check(big["qubits"] == 36, "a 2048-bit modulus is thirty-six qubits wide")
    check(big["probability"] == 0.0, "a wide modulus reports no simulated probability")
    check(big["attempts"] == 0, "and no run count")

    text = plan_text(15, 7)
    check("factoring plan for 15" in text, "the title names the modulus")
    check("3 x 5" in text, "the factors are printed as a product")
    check(text.count("\n") >= 10, "a header and nine rows")

    for bad in ((3, 3), (15, 5)):
        try:
            plan(*bad)
        except ValueError:
            check(True, f"plan{bad} is refused")
        else:
            check(False, f"plan{bad} is refused")

    check(order.circuit_resources(2048)["bits"] == 12, "2048 fits in twelve bits")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
