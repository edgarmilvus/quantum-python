"""Exercise 5, file 3 of 3: the wiring.

Reads three recorded runs through one interface and prints a verdict per run. The same
function would run against a live provider, which is the point of the interface.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import providers as p
from plan_core import summarise
from plan_render import render

CASES = ("chapter18/0001-bell-1024-ibm", "chapter06/0011-bv-1011-1024-ibm", "chapter07/0013-grover-3qubits-1024-ibm")


def report(case: str, circuit: p.Circuit, expected: str) -> str:
    backend = p.Replay(case)
    job = backend.submit(circuit, 1024)
    result = backend.result(job)
    return render(summarise(result, expected), case)


def checks(check: Callable[[bool, str], None]) -> None:
    bell = p.Circuit(2).add("h", 0).add("cx", 0, 1)
    text = report("chapter18/0001-bell-1024-ibm", bell, "00")
    check("chapter18/0001-bell-1024-ibm" in text, "the title names the case")
    check("dbm" not in text.lower(), "no placeholder text survives")

    backend = p.Replay("chapter18/0001-bell-1024-ibm")
    result = backend.result(backend.submit(bell, 1024))
    summary = summarise(result, "00")
    check(summary["shots"] == 1024, "the summary counts the shots")
    check(summary["top"] in ("00", "11"), "the top outcome is a Bell outcome")
    check(summary["frequency"] > 0.4, "with a large share")

    check(report("chapter18/0001-bell-1024-ibm", bell, "00") == text, "the report is deterministic")

    for case in CASES:
        case_backend = p.Replay(case)
        job = case_backend.submit(bell, 1024)
        check(case_backend.result(job).shots == 1024, f"{case} returns its recorded shots")

    try:
        summarise(p.Result(job=p.Job(provider="x", backend="y", id="z", shots=0, depth=0), counts={}), "00")
    except ValueError:
        check(True, "an empty result is refused")
    else:
        check(False, "an empty result is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
