"""Exercise 5, file 3 of 3: the wiring.

Reads the two recorded runs and reports the injection case beside its control, then
the memory case beside its own control.
"""

from __future__ import annotations

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from plan_core import summarise, verdict
from plan_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def load(name: str) -> dict:
    return json.loads((ROOT / f"runs/{name}/result.json").read_text())


def injection(flip: int = 1) -> str:
    record = load("0032-ibm-fez-inject")
    by = {(row["flip"], row["corrected"]): row for row in record["results"]}
    control = summarise(by[(flip, False)]["counts"], prepared=0)
    fixed = summarise(by[(flip, True)]["counts"], prepared=0)
    return render(fixed, control, f"injected flip at qubit {flip}", verdict(fixed, control))


def memory() -> str:
    record = load("0031-ibm-fez-dynamic")
    by = {(row["prepared"], row["idle_us"], row["corrected"]): row for row in record["results"]}
    control = summarise(by[(1, 0.0, False)]["counts"], prepared=1)
    fixed = summarise(by[(1, 0.0, True)]["counts"], prepared=1)
    return render(fixed, control, "clean one, corrected", verdict(fixed, control))


def checks(check: Callable[[bool, str], None]) -> None:
    text = injection()
    check("injected flip at qubit 1" in text, "the title names the injected error")
    check("codeword repaired, logical rate worse" in text, "the verdict separates the repair from the rate")
    check("nan" not in text.lower(), "no number failed to compute")

    by = {(row["flip"], row["corrected"]): row for row in load("0032-ibm-fez-inject")["results"]}
    fixed = summarise(by[(1, True)]["counts"], 0)
    control = summarise(by[(1, False)]["counts"], 0)
    check(abs(fixed["clean"] - 0.904) < 0.01, "the corrected codeword is clean 90.4% of the time")
    check(abs(control["clean"] - 0.010) < 0.01, "the control 1.0%")
    check(fixed["clean"] > 50 * control["clean"], "a factor of ninety")

    text2 = memory()
    check("clean one, corrected" in text2, "the second report names the memory case")
    check("correction hurt" in text2, "and the verdict says it hurt")

    clean_rows = {(row["prepared"], row["idle_us"], row["corrected"]): row
                  for row in load("0031-ibm-fez-dynamic")["results"]}
    fixed2 = summarise(clean_rows[(1, 0.0, True)]["counts"], 1)
    control2 = summarise(clean_rows[(1, 0.0, False)]["counts"], 1)
    check(abs(fixed2["logical"] - 0.0325) < 0.005, "the corrected logical error is 0.0325")
    check(abs(control2["logical"] - 0.0005) < 0.001, "the control's is 0.0005")

    check(injection() == text, "the report is deterministic")

    for bad in (({"00": 10}, 2), ({}, 0)):
        try:
            summarise(*bad)
        except ValueError:
            check(True, f"{bad} is refused")
        else:
            check(False, f"{bad} is refused")

    try:
        summarise({"000": 1, "00": 1}, 0)
    except ValueError:
        check(True, "a short codeword is refused")
    else:
        check(False, "a short codeword is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
