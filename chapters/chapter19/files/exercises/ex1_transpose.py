"""Exercise 1 (repair): the correction applied on the wrong side.

Run: python3 chapters/chapter19/files/exercises/ex1_transpose.py

The measured distribution is M times the prepared one, so the correction is M-inverse
on the left. Writing it as a row-vector product applies the transpose, which on this
16 by 16 matrix takes the peak from 0.988 down to 0.973 — still an improvement on the
raw 0.955, which is why the defect survives a review: it helps, just not as much.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import numpy as np

from pipe import run


def correct_transposed(counts: Dict[str, int], model: run.Readout) -> Dict[str, float]:
    """The defect: p times the inverse, which is the inverse transposed."""
    n = len(model.p_one_given_zero)
    keys = [format(index, f"0{n}b") for index in range(2 ** n)]
    raw = np.array([counts.get(key, 0) for key in keys], dtype=float)
    wrong = (raw / raw.sum()) @ np.linalg.inv(model.matrix())
    wrong = np.clip(wrong, 0, None)
    return dict(zip(keys, (float(value) for value in wrong / wrong.sum())))


def checks(check: Callable[[bool, str], None]) -> None:
    record = run.load("0039-ibm-fez-pipeline")
    model = run.readout(record)
    correct = run.correct(record["counts"], model)
    transposed = correct_transposed(record["counts"], model)
    raw_share = record["counts"]["1011"] / sum(record["counts"].values())

    check(abs(correct["1011"] - 0.988) < 0.005, "the correct orientation gives 0.988")
    check(abs(transposed["1011"] - 0.9732) < 0.005, "the transposed one gives 0.973")
    check(abs(raw_share - 0.9551) < 0.005, "and the raw peak was 0.955")

    check(transposed["1011"] > raw_share, "so the transpose still improves on the raw peak")
    check(correct["1011"] > raw_share, "while the correct one improves it")
    check(correct["1011"] > transposed["1011"] + 0.01, "but the correct one is a point and a half better")

    check(abs(sum(correct.values()) - 1.0) < 1e-9, "the correct distribution sums to one")
    check(abs(sum(transposed.values()) - 1.0) < 1e-9, "and so does the transposed one")

    truth = np.zeros(16)
    truth[0b1011] = 1.0
    seen = model.matrix() @ truth
    counts = {format(index, "04b"): int(round(100_000 * seen[index])) for index in range(16)}
    check(abs(run.correct(counts, model)["1011"] - 1.0) < 0.01, "the round trip is exact")
    check(abs(correct_transposed(counts, model)["1011"] - 1.0) > 0.02, "the transposed round trip is not")

    check(not np.allclose(model.matrix(), model.matrix().T), "and the matrix is not symmetric")

    check(len(correct) == 16, "sixteen outcomes")
    check(min(correct.values()) >= 0.0, "no negative probability survives")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
