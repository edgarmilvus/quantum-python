"""Exercise 5, file 3 of 3: the wiring.

Optimises the one-layer angles, asks the pure file for a summary, renders it, and
then reads the recorded device run to put the measured row beside the simulated
one. This is the only file that opens a file or prints.
"""

from __future__ import annotations

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

from qaoa import graph as g, optimize, qaoa

from plan_core import share_of_optimum, summarise, verdict
from plan_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]


def optimised_summary(instance: g.Graph) -> Dict[str, float]:
    optimum, _ = instance.max_cut()
    point = optimize.optimise(instance, 1)
    summary = summarise(instance, point.betas, point.gammas, optimum)
    summary["evaluations"] = float(point.evaluations)
    return summary


def measured_peak(instance: g.Graph) -> float:
    """The best mean cut the recorded device run reached, on this instance."""
    record = json.loads((ROOT / "runs/0022-ibm-fez-qaoa/result.json").read_text())
    best = 0.0
    for entry in record["results"]:
        counts = {int(key, 2): value for key, value in entry["counts"].items()}
        best = max(best, qaoa.expected_cut_from_counts(instance, counts))
    return best


def report(instance: g.Graph) -> str:
    summary = optimised_summary(instance)
    text = render(summary, "MaxCut on a square with one diagonal", verdict(summary))
    return text + f"measured peak on ibm_marrakesh: {measured_peak(instance):.4f}\n"


def checks(check: Callable[[bool, str], None]) -> None:
    instance = g.square_with_diagonal()
    text = report(instance)

    check("MaxCut on a square" in text, "the title names the instance")
    check("verdict" in text, "the table ends on a verdict")
    check("measured peak on ibm_marrakesh" in text, "and the run's row is in the report")
    check("nan" not in text.lower(), "no number failed to compute")

    summary = optimised_summary(instance)
    check(abs(summary["mean"] - 3.2371) < 1e-3, "the expected cut is 3.2371")
    check(abs(summary["ratio"] - 0.8093) < 1e-3, "the ratio is 0.8093")
    check(summary["mean"] > summary["uniform"], "the state beats the uniform guess")
    check(int(summary["best"]) in (0b0101, 0b1010), "the most likely assignment is one of the two optima")
    check(abs(summary["best probability"] - 0.1641) < 1e-3, "with probability 0.1641")
    check(abs(summary["best cut"] - 4.0) < 1e-9, "and it cuts all five edges")
    check(verdict(summary) == "above guessing", "the verdict says it is above guessing and not at the optimum")

    check(abs(share_of_optimum(instance, [0.3109], [0.5713]) - 0.3281) < 1e-3,
          "32.8% of the probability sits on an optimal assignment")
    check(report(instance) == text, "the report is deterministic")
    check(abs(measured_peak(instance) - 3.1006) < 1e-2, "the measured peak is 3.1006")

    for bad in (([], []), ([0.3], [])):
        try:
            summarise(instance, bad[0], bad[1], 4.0)
        except ValueError:
            check(True, f"angles {bad} are refused")
        else:
            check(False, f"angles {bad} are refused")

    try:
        summarise(instance, [0.3], [0.5], 0.0)
    except ValueError:
        check(True, "an optimum of zero is refused")
    else:
        check(False, "an optimum of zero is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
