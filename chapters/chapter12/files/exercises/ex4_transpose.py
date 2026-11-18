"""Exercise 4 (break): the transpose that looks right.

Run: python3 chapters/chapter12/files/exercises/ex4_transpose.py

The measured distribution is M times the prepared one, so the correction is
M-inverse on the left. Writing it as a row-vector product applies the inverse
transposed, which is exact when the readout errors are symmetric and wrong when
they are not. On this device they are not: 0.9% one way, 3.4% the other.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import numpy as np

from noise import confusion, device, states


def correct_transposed(counts: Dict[str, int], matrix: np.ndarray) -> Dict[str, float]:
    """The defect: p times M-inverse, which is the inverse transposed."""
    keys = [format(index, f"0{int(round(np.log2(matrix.shape[0])))}b")
            for index in range(matrix.shape[0])]
    raw = np.array([counts.get(key, 0) for key in keys], dtype=float)
    if raw.sum() <= 0:
        raise ValueError("an empty histogram has nothing to correct")
    wrong = (raw / raw.sum()) @ confusion.inverse(matrix)
    wrong = np.clip(wrong, 0, None)
    return dict(zip(keys, (float(value) for value in wrong / wrong.sum())))


def synthetic(asymmetry: float) -> np.ndarray:
    """A two-wire matrix whose two columns disagree by `asymmetry`."""
    if not 0 <= asymmetry < 0.4:
        raise ValueError(f"an asymmetry is in [0, 0.4), got {asymmetry}")
    low = 0.01
    high = low + asymmetry
    single = np.array([[1 - low, high], [low, 1 - high]])
    return np.kron(single, single)


def damage(matrix: np.ndarray, truth: np.ndarray) -> Dict[str, float]:
    """Send a known distribution through the matrix, correct it both ways."""
    prepared = {key: int(round(float(value) * 10_000)) for key, value in zip(states.labels(2), truth)}
    seen = matrix @ truth
    counts = {key: int(round(float(value) * 10_000)) for key, value in zip(states.labels(2), seen)}
    right, _ = confusion.correct(counts, matrix)
    wrong = correct_transposed(counts, matrix)
    return {
        "right": float(sum(abs(right[key] - truth[i]) for i, key in enumerate(states.labels(2)))),
        "wrong": float(sum(abs(wrong[key] - truth[i]) for i, key in enumerate(states.labels(2)))),
        "prepared": prepared,
    }


def checks(check: Callable[[bool, str], None]) -> None:
    matrix = device.readout_from_record().matrix()
    truth = np.array([0.5, 0.0, 0.0, 0.5])

    result = damage(matrix, truth)
    check(result["right"] < 0.002, "the correct orientation round-trips within a rounding error")
    check(result["wrong"] > 0.01, "the transposed one misses by more than one percent")
    check(result["wrong"] > 3 * result["right"], "and by more than three times as much")

    bell = device.load_json(device.ROOT / "runs/0001-ibm-fez-bell/result.json")
    right, _ = confusion.correct(bell["counts"], matrix)
    wrong = correct_transposed(bell["counts"], matrix)
    right_correlation = right["00"] + right["11"]
    wrong_correlation = wrong["00"] + wrong["11"]
    check(abs(right_correlation - 0.9896) < 1e-3, "on the Bell run the right orientation gives 0.9896")
    check(abs(wrong_correlation - 0.9865) < 1e-3, "the transposed one gives 0.9865")
    check(wrong_correlation < right_correlation, "which understates the correction")

    symmetric = device.Readout.independent((0.02, 0.02)).matrix()
    same = damage(symmetric, truth)
    check(abs(same["right"] - same["wrong"]) < 1e-9, "with symmetric errors the two are identical")
    check(same["wrong"] < 0.002, "so the bug is invisible on a symmetric model")

    gap = damage(synthetic(0.04), truth)
    check(gap["wrong"] > 10 * gap["right"], "with a four-point asymmetry the transposed error is ten times larger")
    check(gap["wrong"] > 0.002, "and above a fifth of a percent of the distribution")

    for bad in (-0.1, 0.5):
        try:
            synthetic(bad)
        except ValueError:
            check(True, f"an asymmetry of {bad} is refused")
        else:
            check(False, f"an asymmetry of {bad} is refused")

    try:
        confusion.correct({"00": 10, "01": 10}, np.ones((4, 4)) / 4)
    except ValueError:
        check(True, "a two-outcome histogram cannot be corrected with a four-outcome matrix")
    else:
        check(False, "a two-outcome histogram cannot be corrected with a four-outcome matrix")

    check(confusion.total_variation({"00": 1.0}, {"00": 0.5, "11": 0.5}) == 0.5,
          "total variation measures half the distance")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
