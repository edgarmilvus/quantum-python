"""Exercise 5, file 3 of 3: the wiring.

Chooses the sizes, prints their plans, and drops in the recorded device result for the one
size that was actually run.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import json
from typing import Callable

from plan_core import plan, rows
from plan_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def plan_text(size: int) -> str:
    return render(rows(plan(size)), f"search plan for {size} items")


def hardware_line() -> str:
    record = json.loads((ROOT / "runs/0013-ibm-grover/result.json").read_text())
    counts = record["counts"]
    total = sum(counts.values())
    hits = counts.get(record["marked_bits"], 0)
    return (f"device: {record['backend']}, {record['steps']} iterations, "
            f"{hits}/{total} = {hits / total:.4f} on the marked item")


def checks(check: Callable[[bool, str], None]) -> None:
    small = plan(8)
    check(small["bits"] == 3, "eight items is three qubits")
    check(small["steps"] == 2, "and two iterations")
    check(abs(small["probability"] - 0.9453) < 1e-3, "with a success probability of 0.945")
    check(small["linear"] == 4, "linear search costs four queries")
    check(small["binary"] == 3, "binary search costs three")
    check(abs(small["ratio_to_linear"] - 2.0) < 1e-12, "so Grover is twice as good as scanning")
    check(abs(small["ratio_to_binary"] - 2 / 3) < 1e-12, "and two thirds as good as a binary search")

    big = plan(1024)
    check(big["steps"] == 25, "a thousand items need twenty-five iterations")
    check(big["ratio_to_binary"] > 2, "and lose to a binary search by more than twice")

    two = plan(8, marked=2)
    check(two["steps"] == 1, "two marked items need one iteration")
    check(abs(two["probability"] - 1.0) < 1e-9, "which is certain")

    text = plan_text(8)
    check("search plan for 8 items" in text, "the title names the size")
    check("iterations" in text and "binary queries" in text, "the rows are named")
    check(text.count("\n") >= 9, "a header and eight rows")

    line = hardware_line()
    check("device" in line and "/" in line, "the hardware line carries the counts")

    for bad in ((3,), (8, 9)):
        try:
            plan(*bad)
        except ValueError:
            check(True, f"plan{bad} is refused")
        else:
            check(False, f"plan{bad} is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
