"""Exercise 1 (repair): a correction that clips by throwing mass away.

Run: python3 chapters/chapter12/files/exercises/ex1_clip.py

The defective function zeroes every negative entry and stops there. The
negatives were subtracting, so removing them inflates the total: the result
sums to more than one, every frequency is larger than it should be, and the
first impossible number is a probability above the one that the state allows.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import numpy as np

from noise import confusion, device

DEFECT_RECORD = "chapter12/0009-readout-4circuits-4096-ibm"


def correct_without_renormalising(counts: Dict[str, int], matrix: np.ndarray) -> Dict[str, float]:
    """The defect: negatives become zero and the total is left alone."""
    keys = [format(index, "02b") for index in range(matrix.shape[0])]
    raw = np.array([counts.get(key, 0) for key in keys], dtype=float)
    if raw.sum() <= 0:
        raise ValueError("an empty histogram has nothing to correct")
    corrected = confusion.inverse(matrix) @ (raw / raw.sum())
    corrected = np.clip(corrected, 0, None)
    return dict(zip(keys, (float(value) for value in corrected)))


def correct_with_renormalising(counts: Dict[str, int], matrix: np.ndarray) -> Dict[str, float]:
    """The repair: clip, then divide by what is left, and report what was clipped."""
    corrected, _ = confusion.correct(counts, matrix)
    return corrected


def checks(check: Callable[[bool, str], None]) -> None:
    matrix = device.readout_from_record().matrix()

    # A distribution that the inverse pushes negative: three outcomes, no 11.
    counts = {"00": 950, "01": 0, "10": 0, "11": 50}
    broken = correct_without_renormalising(counts, matrix)
    fixed = correct_with_renormalising(counts, matrix)

    total = sum(broken.values())
    check(abs(total - 1.0) > 0.01, "the defect returns a distribution that does not sum to one")
    check(total > 1.0, "and it is long, because the negatives it removed were subtracting")
    check(abs(sum(fixed.values()) - 1.0) < 1e-9, "the repair sums to exactly one")
    check(min(fixed.values()) >= 0.0, "and has no negative entry")

    check(fixed["00"] < broken["00"], "every surviving frequency is smaller after the repair")
    check(abs(broken["00"] / total - fixed["00"]) < 1e-9, "the repair is the defect divided by its total")

    raw = np.array([counts[key] for key in ("00", "01", "10", "11")], dtype=float)
    pre = confusion.inverse(matrix) @ (raw / raw.sum())
    clipped = float(max(0.0, -pre[pre < 0].sum()))
    check(clipped > 0.0, "the inverse really does push an entry negative here")
    check(
        abs(sum(broken.values()) - (float(pre.sum()) + clipped)) < 1e-12,
        "clipping changes the total by exactly the mass it removed",
    )

    real = device.load_json(device.ROOT / f"runs/{DEFECT_RECORD}/result.json")
    bell = device.load_json(device.ROOT / "runs/chapter18/0001-bell-1024-ibm/result.json")
    honest, honest_clipped = confusion.correct(bell["counts"], matrix)
    check(honest_clipped < 1e-9, "a well-conditioned histogram clips nothing")
    check(abs(sum(honest.values()) - 1.0) < 1e-9, "so the two functions agree there")

    one_parameter = device.Readout.independent(device.estimate_flips(real))
    rough = correct_without_renormalising(counts, one_parameter.matrix())
    check(abs(sum(rough.values()) - 1.0) > 1e-6, "a symmetric matrix breaks the defective function too")
    check(abs(confusion.amplification(matrix) - confusion.amplification(one_parameter.matrix())) < 0.01,
          "and the two matrices amplify by almost the same factor, from very different errors")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
