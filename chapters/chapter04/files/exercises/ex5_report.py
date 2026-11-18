"""Exercise 5, file 3 of 3: the wiring.

Reads the recorded run, calls the pure part, prints the report. The only file that
touches the filesystem and the only one that writes to the terminal.
"""

from __future__ import annotations

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import bell
from report_core import expectations, rows, summary
from report_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def load_counts(path: _pathlib.Path | None = None) -> Dict[str, Dict[str, int]]:
    target = path or (ROOT / "runs/0007-ibm-chsh/result.json")
    record = json.loads(_pathlib.Path(target).read_text())
    return record["counts"]


def report(counts: Dict[str, Dict[str, int]], shots: int = 1024, title: str = "CHSH report") -> str:
    return render(rows(summary(counts, shots)), title)


def checks(check: Callable[[bool, str], None]) -> None:
    counts = load_counts()
    check(len(counts) == 4, "four settings are loaded")

    values = expectations(counts)
    check(set(values) == set(bell.SETTINGS), "every setting has an expectation")
    check(all(-1.0 <= v <= 1.0 for v in values.values()), "every expectation is in [-1, 1]")

    result = summary(counts, 1024)
    check(abs(result["S"] - 2.541) < 0.01, "S is 2.541")
    check(result["margin"] > 0, "the margin is positive")
    check(result["sigma"] > 5, "the margin is more than five sigma")
    check(abs(result["fraction"] - 0.653) < 0.01, "65% of the ideal violation survived")

    text = report(counts)
    check("CHSH report" in text, "the report has a title")
    check("S" in text and "sigma" in text, "the rows are named")
    check(text.count("\n") >= 5, "a header and four rows")
    check(report(counts) == text, "the wiring is deterministic")

    try:
        expectations({"ab": counts["ab"]})
    except ValueError:
        check(True, "a partial set is refused")
    else:
        check(False, "a partial set is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
