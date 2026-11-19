"""Exercise 5, file 3 of 3: the wiring.

Loads the recorded run, builds the summary, prints the page. The other two files do not
know where the record lives.
"""

from __future__ import annotations

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from memo_core import summarise, verdict
from memo_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def record() -> Dict:
    path = ROOT / "runs/chapter20/0042-teleport-pi3-pi4-2048-ibm/result.json"
    return json.loads(path.read_text())


def memo(data: Dict = None) -> str:
    summary = summarise(data if data is not None else record())
    return render(summary, verdict(summary), "Teleportation on ibm_kingston")


def checks(check: Callable[[bool, str], None]) -> None:
    text = memo()
    check(text.startswith("Teleportation on ibm_kingston"), "the memo is titled")
    check("0.9558" in text, "the dynamic fidelity is in the page")
    check("0.4858" in text, "and the control")
    check("+0.470" in text, "and the gap")
    check("2048" in text, "and the shot count")
    check("nan" not in text.lower(), "no number failed to compute")
    check(text.endswith("\n"), "the page ends on a newline")

    summary = summarise(record())
    check(abs(summary["fidelity"]["dynamic"] - 0.9558) < 0.005, "the summary scores the dynamic run")
    check(summary["best"] == "dynamic", "the best run is the dynamic one")
    check(abs(summary["gap"] - 0.470) < 0.01, "the gap is 0.470")
    check(summary["shots"] == 2048, "at 2,048 shots")
    check("0.9558" in summary["headline"], "the headline carries the fidelity")
    check(verdict(summary).startswith("the state arrived"), "the sentence says the state arrived")

    check(memo() == text, "the memo is deterministic")

    try:
        summarise({})
    except ValueError:
        check(True, "a record with no prepared state is refused")
    else:
        check(False, "a record with no prepared state is refused")

    try:
        summarise({"prepared": {"theta": 1.0, "phi": 0.0}})
    except (KeyError, ValueError):
        check(True, "a record with no calibration is refused")
    else:
        check(False, "a record with no calibration is refused")

    try:
        render(summary, "")
    except ValueError:
        check(True, "a memo with no sentence is refused")
    else:
        check(False, "a memo with no sentence is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
