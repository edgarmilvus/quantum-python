"""Exercise 2 (extend): a third feature, and the accuracy it costs.

Run: python3 chapters/chapter15/files/exercises/ex2_features.py

Adding the radius to the two coordinates is one line of feature engineering and one
extra qubit, and it makes the kernel sharper: the off-diagonal mean falls from 0.25
to 0.12. On six training points a sharper kernel is a worse one, and the accuracy
falls from 1.000 to 0.833 even at the penalty that suits it.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List, Sequence, Tuple

import numpy as np

from qml import classifier, data, featuremap as fm


def with_radius(points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float, float]]:
    """Two coordinates plus the distance from the centre, which is a real feature."""
    out = []
    for x, y in points:
        out.append((x, y, float(np.hypot(x - 0.5, y - 0.5))))
    return out


def kernel_of(points: Sequence[tuple], n: int, reps: int = 3) -> np.ndarray:
    states = [fm.state_for(point, n=n, reps=reps) for point in points]
    size = len(points)
    out = np.zeros((size, size))
    for i in range(size):
        for j in range(i, size):
            out[i, j] = out[j, i] = fm.fidelity(states[i], states[j])
    return out


def score(dataset: data.Dataset, points: Sequence[tuple], n: int, lam: float) -> Dict[str, float]:
    train_idx, test_idx = dataset.split_indices(3)
    train = [points[i] for i in train_idx]
    test = [points[i] for i in test_idx]
    labels = [dataset.labels[i] for i in train_idx]
    test_labels = [dataset.labels[i] for i in test_idx]
    k_train = np.array([[fm.fidelity(fm.state_for(a, n=n, reps=3), fm.state_for(b, n=n, reps=3))
                         for b in train] for a in train])
    k_cross = np.array([[fm.fidelity(fm.state_for(a, n=n, reps=3), fm.state_for(b, n=n, reps=3))
                         for b in test] for a in train])
    run = classifier.run(train, labels, test, test_labels, k_train, k_cross, lam)
    return {
        "accuracy": run["quantum"],
        "off_diagonal": float(k_train[~np.eye(len(train), dtype=bool)].mean()),
        "condition": float(np.linalg.cond(k_train)),
    }


def checks(check: Callable[[bool, str], None]) -> None:
    spiral = data.spiral()

    two = score(spiral, spiral.points, 2, 0.1)
    three = score(spiral, with_radius(spiral.points), 3, 1.0)

    check(abs(two["accuracy"] - 1.0) < 1e-9, "two features classify perfectly")
    check(abs(three["accuracy"] - 0.833) < 1e-3, "three features reach 0.833 at the penalty that suits them")
    check(three["accuracy"] < two["accuracy"], "so the extra feature costs accuracy")

    check(three["off_diagonal"] < two["off_diagonal"], "because the kernel is sharper")
    check(abs(two["off_diagonal"] - 0.252) < 0.02, "the two-feature off-diagonal is about 0.25")
    check(abs(three["off_diagonal"] - 0.120) < 0.02, "and the three-feature one about 0.12")

    check(three["condition"] < two["condition"], "the sharper kernel is better conditioned, not worse")
    check(two["condition"] < 20, "the two-feature matrix is already well conditioned")

    triple = with_radius([(0.5, 0.5)])
    check(abs(triple[0][2]) < 1e-12, "a point at the centre has radius zero")
    far = with_radius([(0.5, 0.9)])
    check(abs(far[0][2] - 0.4) < 1e-12, "and one at distance 0.4 has radius 0.4")

    check(len(with_radius(spiral.points)) == 12, "the dataset still has twelve points")

    state = fm.state_for((0.2, 0.3, 0.4), n=3, reps=1)
    check(abs(fm.norm(state) - 1.0) < 1e-12, "the three-qubit state is normalised")
    check(len(fm.ops_for((0.2, 0.3, 0.4), n=3, reps=1)) == 9, "a three-feature layer is nine gates")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
