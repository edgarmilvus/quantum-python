"""Exercise 4 (break): a kernel so sharp it forgets the data.

Run: python3 chapters/chapter15/files/exercises/ex4_sharp.py

Each layer of the feature map sharpens the kernel: the off-diagonal mean falls from
0.62 to 0.25 to 0.19 and the condition number from 658 to 9 to 5. Three layers
classify the split perfectly and four drop to 0.833, so the sharpest kernel is not
the best one and the condition number alone does not predict which.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import numpy as np

from qml import classifier, data, featuremap as fm


def run_reps(spiral: data.Dataset, reps: int, lam: float = 0.1) -> Dict[str, float]:
    train_idx, test_idx = spiral.split_indices(3)
    train = [spiral.points[i] for i in train_idx]
    test = [spiral.points[i] for i in test_idx]
    labels = [spiral.labels[i] for i in train_idx]
    test_labels = [spiral.labels[i] for i in test_idx]

    def k(a, b) -> float:
        return fm.fidelity(fm.state_for(a, reps=reps), fm.state_for(b, reps=reps))

    gram = np.array([[k(a, b) for b in train] for a in train])
    cross = np.array([[k(a, b) for b in test] for a in train])
    result = classifier.run(train, labels, test, test_labels, gram, cross, lam)
    return {
        "accuracy": result["quantum"],
        "off_diagonal": float(gram[~np.eye(len(train), dtype=bool)].mean()),
        "condition": float(np.linalg.cond(gram)),
        "gates": float(len(fm.ops_for(train[0], reps=reps))),
    }


def curve(spiral: data.Dataset) -> List[Dict[str, float]]:
    return [{"reps": float(reps), **run_reps(spiral, reps)} for reps in (1, 2, 3, 4)]


def checks(check: Callable[[bool, str], None]) -> None:
    spiral = data.spiral()
    rows = {int(row["reps"]): row for row in curve(spiral)}

    check(abs(rows[1]["accuracy"] - 0.333) < 1e-3, "one layer reaches 0.333")
    check(abs(rows[3]["accuracy"] - 1.0) < 1e-9, "three layers reach 1.000")
    check(abs(rows[4]["accuracy"] - 0.833) < 1e-3, "four layers fall back to 0.833")

    check(rows[4]["accuracy"] < rows[3]["accuracy"], "so the fourth layer costs accuracy")
    check(rows[1]["accuracy"] < rows[2]["accuracy"] < rows[3]["accuracy"], "and the first three rise")

    check(rows[1]["off_diagonal"] > rows[3]["off_diagonal"], "a layer sharpens the kernel")
    check(rows[4]["off_diagonal"] < rows[3]["off_diagonal"], "four is sharper than three")

    check(rows[4]["condition"] < rows[3]["condition"], "and better conditioned")
    check(rows[3]["condition"] < rows[1]["condition"], "three is better conditioned than one")
    check(rows[4]["condition"] < 10, "the sharpest kernel has a condition below ten")

    check(rows[1]["gates"] == 5, "one layer is five gates")
    check(rows[4]["gates"] == 14, "four layers are fourteen")
    check(rows[4]["gates"] > rows[3]["gates"], "depth grows with the layers")

    check(all(0.0 <= row["accuracy"] <= 1.0 for row in rows.values()), "every accuracy is a fraction")

    for bad in (0, -1):
        try:
            run_reps(spiral, bad)
        except ValueError:
            check(True, f"reps={bad} is refused")
        else:
            check(False, f"reps={bad} is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
