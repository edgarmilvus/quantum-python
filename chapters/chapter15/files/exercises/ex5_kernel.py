"""Exercise 5, file 3 of 3: the wiring.

Builds the exact kernel from the feature map, reads the device's kernel from the
recorded run, and asks the pure file for a report on each. This is the only file
that knows a directory exists.
"""

from __future__ import annotations

import json
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import numpy as np

from qml import classifier, featuremap as fm, kernel

from plan_core import summarise, verdict
from plan_render import render

ROOT = _pathlib.Path(__file__).resolve().parents[4]
RECORD = ROOT / "runs/chapter15/0026-kernel-12points-57x1024-ibm/result.json"


def load() -> Dict[str, object]:
    record = json.loads(RECORD.read_text())
    device, _ = kernel.device_matrix(record)
    points = [tuple(point) for point in record["points"]]
    exact = np.array([
        [fm.fidelity(fm.state_for(points[a], reps=record["reps"]), fm.state_for(points[b], reps=record["reps"]))
         for b in range(len(points))]
        for a in range(len(points))
    ])
    return {"record": record, "device": device, "exact": exact, "points": points}


def two_reports(lam: float = 0.1) -> str:
    loaded = load()
    record, device, exact, points = loaded["record"], loaded["device"], loaded["exact"], loaded["points"]
    train, test = record["train"], record["test"]
    train_labels = [record["labels"][i] for i in train]
    test_labels = [record["labels"][i] for i in test]

    lines = []
    for name, matrix in (("exact", exact), ("device", device)):
        summary = summarise(matrix[np.ix_(train, train)], train_labels,
                            matrix[np.ix_(train, test)], test_labels, lam)
        lines.append(render(summary, f"{name} kernel on the spiral", verdict(summary)))
    return "\n".join(lines)


def checks(check: Callable[[bool, str], None]) -> None:
    text = two_reports()
    check("exact kernel on the spiral" in text, "the first report names the exact kernel")
    check("device kernel on the spiral" in text, "the second names the device's")
    check(text.count("verdict") == 2, "each report ends on a verdict")
    check("nan" not in text.lower(), "no number failed to compute")

    loaded = load()
    record, device, exact = loaded["record"], loaded["device"], loaded["exact"]
    train, test = record["train"], record["test"]
    train_labels = [record["labels"][i] for i in train]
    test_labels = [record["labels"][i] for i in test]

    exact_summary = summarise(exact[np.ix_(train, train)], train_labels,
                              exact[np.ix_(train, test)], test_labels, 0.1)
    device_summary = summarise(device[np.ix_(train, train)], train_labels,
                               device[np.ix_(train, test)], test_labels, 0.1)

    check(abs(exact_summary["test accuracy"] - 1.0) < 1e-9, "the exact kernel is perfect")
    check(abs(device_summary["test accuracy"] - 0.833) < 1e-3, "the device's reaches 0.833")
    check(device_summary["test accuracy"] < exact_summary["test accuracy"], "so the device is worse")
    check(abs(exact_summary["off diagonal"] - 0.252) < 0.02, "the exact off-diagonal is about 0.25")
    check(verdict(exact_summary) == "well above the baseline", "which is well above the baseline")
    check(verdict(device_summary) == "well above the baseline", "and the device is above it too, by 0.17 instead of 0.33")

    check(two_reports() == text, "the report is deterministic")

    try:
        summarise(np.zeros((3, 2)), [1, -1, 1], np.zeros((3, 2)), [1, -1], 0.1)
    except ValueError:
        check(True, "a non-square training kernel is refused")
    else:
        check(False, "a non-square training kernel is refused")

    try:
        summarise(np.eye(3), [1, -1, 1], np.zeros((4, 2)), [1, -1], 0.1)
    except ValueError:
        check(True, "a cross kernel with the wrong row count is refused")
    else:
        check(False, "a cross kernel with the wrong row count is refused")

    try:
        summarise(np.eye(3), [1, -1, 1], np.zeros((3, 2)), [1, -1], 0.0)
    except ValueError:
        check(True, "a zero penalty is refused")
    else:
        check(False, "a zero penalty is refused")

    check(abs(classifier.accuracy([1.0], [1]) - 1.0) < 1e-12, "the accuracy of one right answer is one")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
