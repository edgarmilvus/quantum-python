"""Exercise 5, file 3 of 3: the wiring.

Reads the two recorded files, calls the pure part, prints the report.
"""

from __future__ import annotations

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from report_core import rows, summary
from report_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def load_run(name: str) -> dict:
    return json.loads((ROOT / "runs" / name / "result.json").read_text())


def report() -> str:
    calibration = load_run("0009-ibm-readout")
    chsh = load_run("0007-ibm-chsh")
    result = summary(calibration["counts"], calibration["preparations"], chsh["counts"])
    return render(rows(result))


def checks(check: Callable[[bool, str], None]) -> None:
    calibration = load_run("0009-ibm-readout")
    chsh = load_run("0007-ibm-chsh")
    result = summary(calibration["counts"], calibration["preparations"], chsh["counts"])

    check(abs(result["readout_error"] - 0.0434) < 0.001, "the readout error is 4.3%")
    check(abs(result["raw_S"] - 2.541) < 0.01, "the raw S is 2.541")
    check(abs(result["corrected_S"] - 2.7796) < 0.01, "the corrected S is 2.780")
    check(result["corrected_S"] > result["raw_S"], "correction raises S")
    check(result["clipped"] == 0.0, "nothing was clipped")
    check(abs(result["corrected_S"] - 2.8284) < 0.05, "the corrected S is within 0.05 of ideal")

    text = report()
    check("readout report" in text, "the report has a title")
    check(text.count("\n") >= 5, "a header and four rows")
    check("S corrected" in text, "the corrected value is named")
    check(report() == text, "the wiring is deterministic")

    try:
        summary({"00": {"00": 1}}, {"00": []}, chsh["counts"])
    except (KeyError, ValueError):
        check(True, "an incomplete calibration is refused")
    else:
        check(False, "an incomplete calibration is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
