"""Exercise 5, file 3 of 3: the wiring.

The only file that knows about sampling, printing and the order of the two.
It contains no arithmetic of its own: every number comes from report_core and
every character from report_render.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from report_core import build_rows, largest_gap, totals
from report_render import render_report
from sampling import sample_counts, standard_error
from state import StateVector


def report(state: StateVector, shots: int, seed: int, title: str = "one-qubit report") -> str:
    """Sample, assemble, render. One call, one string."""
    counts = sample_counts(state, shots=shots, seed=seed)
    rows = build_rows(state, counts)
    return render_report(title, shots, rows, totals(rows))


def report_with_error(state: StateVector, shots: int, seed: int) -> str:
    """The same report, plus the error bar of the first outcome."""
    text = report(state, shots, seed)
    p0 = state.probabilities()[0]
    bar = standard_error(float(p0), shots)
    return text + f"\nP(0) = {p0:.5f} +/- {bar:.5f} (1 sigma, {shots} shots)\n"


def checks(check: Callable[[bool, str], None]) -> None:
    import numpy as np

    state = StateVector([np.sqrt(0.75), np.sqrt(0.25)])

    text = report(state, shots=1000, seed=7, title="demo")
    check("demo" in text, "the title reaches the report")
    check("shots: 1000" in text, "the shot count reaches the report")
    check("|0>" in text and "|1>" in text, "both outcomes are rendered")
    check(text.count("\n") >= 5, "the report has a header, two rows and a footer")

    again = report(state, shots=1000, seed=7, title="demo")
    check(text == again, "the same seed renders the same report")
    different = report(state, shots=1000, seed=8, title="demo")
    check(text != different, "a different seed changes the counts")

    counts = sample_counts(state, shots=1000, seed=7)
    rows = build_rows(state, counts)
    check(len(rows) == 2, "one row per outcome")
    check(abs(sum(row[4] for row in rows) - 1000) < 1e-9, "the rendered counts add up to the shots")
    check(abs(totals(rows)["probability"] - 1.0) < 1e-12, "the probabilities add up to one")
    check(largest_gap(rows) < 0.05, "the observed frequencies stay within 5 points of p at 1000 shots")
    check(build_rows(state, counts) == rows, "the pure part is deterministic with no seed")

    with_error = report_with_error(state, shots=1000, seed=7)
    check("1 sigma" in with_error, "the error bar is appended, not mixed into the table")

    try:
        build_rows(state, {"0": 0, "1": 0})
    except ValueError:
        check(True, "a report with no shots is refused")
    else:
        check(False, "a report with no shots is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
