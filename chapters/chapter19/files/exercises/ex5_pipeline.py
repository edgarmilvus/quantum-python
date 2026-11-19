"""Exercise 5, file 3 of 3: the wiring.

Runs the recorded pipeline for the BV task and for the same task priced on IonQ, which
the estimate refuses. The refusal is part of the report.
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from pipe import estimate, run, spec

from plan_core import summarise, verdict
from plan_render import render


def task(provider: str = "ibm") -> spec.Task:
    return spec.Task(name="bv-1011", qubits=4, shots=2048, provider=provider, budget_usd=5.0)


def report(provider: str = "ibm") -> str:
    chosen = task(provider)
    plan = estimate.estimate(chosen)
    if not plan.allowed:
        return f"{chosen.name} on {provider}: refused ({plan.reason})\n"
    record = run.load("chapter19/0039-bv-1011-pipeline-2048-ibm")
    summary = summarise(chosen, record)
    return render(summary, f"{chosen.name} on {provider}", verdict(summary))


def checks(check: Callable[[bool, str], None]) -> None:
    text = report("ibm")
    check("bv-1011 on ibm" in text, "the title names the task and the provider")
    check("verdict" in text, "the table ends on a verdict")
    check("nan" not in text.lower(), "no number failed to compute")

    summary = summarise(task(), run.load("chapter19/0039-bv-1011-pipeline-2048-ibm"))
    check(abs(summary["raw"] - 0.9551) < 0.005, "the raw peak is 0.9551")
    check(abs(summary["corrected"] - 0.9880) < 0.005, "the corrected one 0.9880")
    check(abs(summary["gain"] - 0.0329) < 0.005, "a gain of 3.3 points")
    check(summary["ok"] == 1.0, "and the secret is right")
    check(verdict(summary) == "recovered, and the correction mattered", "the verdict says the correction mattered")

    refused = report("ionq")
    check("refused" in refused, "the IonQ task is refused")
    check("984.84" in refused, "with the price in the message")

    check(report("ibm") == text, "the report is deterministic")

    try:
        summarise(task(), {"secret": "0110", "counts": {"1011": 1}, "shots": 1, "calibration": []})
    except ValueError:
        check(True, "a record with another secret is refused")
    else:
        check(False, "a record with another secret is refused")

    try:
        summarise(task(), {"secret": "1011", "counts": {}, "shots": 1})
    except ValueError:
        check(True, "a record with no counts is refused")
    else:
        check(False, "a record with no counts is refused")

    cosmetic = dict(summary)
    cosmetic["gain"] = 0.001
    check(verdict(cosmetic) == "recovered, and the correction was cosmetic", "a small gain is called cosmetic")
    missed = dict(summary)
    missed["ok"] = 0.0
    check(verdict(missed) == "not recovered", "and a miss is called a miss")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
