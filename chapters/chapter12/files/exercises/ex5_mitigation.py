"""Exercise 5, file 3 of 3: the wiring.

Reads the recorded CHSH run, builds the readout matrix, runs the model at three
noise scales to get the extrapolation points, then asks the pure file for a
summary and the renderer for text. This is the only file that touches the disk.
"""

from __future__ import annotations

import json
import math
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from noise import confusion, device, simulate, zne

from plan_core import SETTINGS, summarise, verdict
from plan_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]
IDEAL = 2 * math.sqrt(2)


def load_run(name: str = "chapter04/0007-chsh-1024-ibm") -> Dict[str, Dict[str, int]]:
    record = json.loads((ROOT / f"runs/{name}/result.json").read_text())
    return record["counts"]


def model_points(matrix, rate: float, shots: int = 4096) -> List[zne.Point]:
    """The extrapolation points, from the model calibrated on the measured data."""
    simulator = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=rate), readout=None, seed=11)
    points = []
    for scale in (1, 3, 5):
        correlators = {}
        for name in SETTINGS:
            alpha, beta = {"ab": (0, 45), "ab_prime": (0, 135),
                           "a_prime_b": (90, 45), "a_prime_b_prime": (90, 135)}[name]
            ops, basis = simulate.chsh_setting(alpha, beta)
            counts = simulator.run(2, zne.fold(ops, scale), shots, basis=basis)
            correlators[name] = confusion.correlation(
                {key: value / shots for key, value in counts.items()}
            )
        points.append(zne.Point(scale, confusion.chsh(correlators), confusion.chsh_sigma(correlators, shots)))
    return points


def report(raw: Dict[str, Dict[str, int]], matrix) -> str:
    rate = 1 - 2.7815 / IDEAL
    points = model_points(matrix, rate)
    summary = summarise(raw, matrix, points, IDEAL)
    return render(summary, "CHSH through two mitigations", verdict(summary))


def checks(check: Callable[[bool, str], None]) -> None:
    matrix = device.readout_from_record().matrix()
    raw = load_run()
    text = report(raw, matrix)

    check("CHSH through two mitigations" in text, "the title names the experiment")
    check("verdict" in text, "and the table ends on a verdict")
    check("nan" not in text.lower(), "no number failed to compute")

    rate = 1 - 2.7815 / IDEAL
    summary = summarise(raw, matrix, model_points(matrix, rate), IDEAL)
    check(abs(summary["raw"] - 2.541) < 1e-3, "the raw value is 2.541")
    check(abs(summary["corrected"] - 2.7815) < 1e-3, "readout takes it to 2.7815")
    check(0.8 < summary["closed"] < 0.9, "which closes 84% of the gap to the ideal")
    check(abs(summary["extrapolated"] - IDEAL) < 0.05, "the extrapolation lands within 0.05 of 2.8284")
    check(abs(summary["z"]) < 2.0, "inside two sigma")
    check(verdict(summary) == "consistent", "so the verdict is consistent")

    check(report(raw, matrix) == text, "the report is deterministic")

    try:
        summarise({"ab": raw["ab"]}, matrix, model_points(matrix, rate), IDEAL)
    except ValueError:
        check(True, "a missing setting is refused")
    else:
        check(False, "a missing setting is refused")

    try:
        summarise(raw, matrix, [], IDEAL)
    except ValueError:
        check(True, "no extrapolation points is refused")
    else:
        check(False, "no extrapolation points is refused")

    try:
        summarise(raw, matrix, model_points(matrix, rate), 0.0)
    except ValueError:
        check(True, "an ideal value of zero is refused")
    else:
        check(False, "an ideal value of zero is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
