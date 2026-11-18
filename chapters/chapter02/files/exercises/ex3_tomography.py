"""Exercise 3 (measure): the Bloch vector you can actually measure.

A report claims a qubit is at 45 degrees. The only data is three histograms, one
per measurement axis. This file turns those histograms into a vector and says how
far it is from the truth.

Run: python3 chapters/chapter02/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Dict

import numpy as np

from bloch import angle_error_deg, estimate_vector


def tomography(counts_by_axis: Dict[str, Dict[str, int]]) -> np.ndarray:
    """Three histograms in, one Bloch vector out."""
    return estimate_vector(counts_by_axis)


def azimuth_deg(vector: np.ndarray) -> float:
    if abs(vector[0]) < 1e-12 and abs(vector[1]) < 1e-12:
        raise ValueError("the vector has no azimuth")
    return math.degrees(math.atan2(vector[1], vector[0]))


def polar_deg(vector: np.ndarray) -> float:
    return math.degrees(math.atan2(float(vector[0]), float(vector[2])))


def checks(check: Callable[[bool, str], None]) -> None:
    truth = np.array([np.sin(math.radians(45)), 0.0, np.cos(math.radians(45))])
    counts = {
        "x": {"0": 7071, "1": 2929},
        "y": {"0": 5000, "1": 5000},
        "z": {"0": 7071, "1": 2929},
    }

    measured = tomography(counts)
    check(measured.shape == (3,), "tomography returns three numbers")
    check(abs(measured[0] - 0.4142) < 1e-3, "x is 0.7071 - 0.2929 = 0.4142")
    check(abs(measured[1]) < 1e-12, "a balanced y histogram gives zero")
    check(abs(measured[2] - 0.4142) < 1e-3, "z matches x for a 45 degree state")
    check(angle_error_deg(measured, truth) < 5.0, "the estimate is within five degrees of the truth")
    check(abs(azimuth_deg(np.array([1.0, 0.0, 0.0])) - 0.0) < 1e-12, "the azimuth of +x is zero")
    check(abs(azimuth_deg(np.array([0.0, 1.0, 0.0])) - 90.0) < 1e-12, "the azimuth of +y is 90 degrees")
    check(abs(polar_deg(np.array([np.sin(0.5), 0.0, np.cos(0.5)])) - math.degrees(0.5)) < 1e-9,
          "the polar angle of a Ry state is recovered")

    try:
        tomography({"x": counts["x"], "z": counts["z"]})
    except ValueError:
        check(True, "two axes are not enough")
    else:
        check(False, "two axes are not enough")

    try:
        azimuth_deg(np.array([0.0, 0.0, 1.0]))
    except ValueError:
        check(True, "the pole has no azimuth")
    else:
        check(False, "the pole has no azimuth")

    empty = tomography({"x": {"0": 1, "1": 1}, "y": {"0": 1, "1": 1}, "z": {"0": 1, "1": 1}})
    check(np.allclose(empty, 0.0), "balanced histograms on every axis give the centre")
    check(angle_error_deg(measured, measured) < 1e-9, "an estimate is zero degrees from itself")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
