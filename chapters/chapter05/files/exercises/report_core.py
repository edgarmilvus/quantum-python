"""Exercise 5, file 1 of 3: the pure part.

Counts in, a summary out: raw and corrected S, the readout error, and how much mass the
correction had to clip. No file access, no printing, no globals.
"""

from __future__ import annotations

from typing import Callable, Dict, Sequence

import numpy as np

import calibrate
from stats import invert


def summary(
    calibration_counts: Dict[str, Dict[str, int]],
    preparations: Dict[str, Sequence[int]],
    chsh_counts: Dict[str, Dict[str, int]],
) -> Dict[str, float]:
    """Everything the report needs, computed from dictionaries alone."""
    matrix = calibrate.confusion_from_preparations(calibration_counts, preparations)
    inverse = invert(matrix)
    values = calibrate.corrected_chsh(chsh_counts, inverse)
    return {
        "readout_error": calibrate.diagonal_error(matrix),
        "raw_S": calibrate.chsh_from(values, "raw"),
        "corrected_S": calibrate.chsh_from(values, "corrected"),
        "clipped": max(row["clipped_mass"] for row in values.values()),
    }


def rows(result: Dict[str, float]) -> list:
    return [
        ("readout error", f"{result['readout_error']:.4f}"),
        ("S raw", f"{result['raw_S']:.4f}"),
        ("S corrected", f"{result['corrected_S']:.4f}"),
        ("clipped mass", f"{result['clipped']:.4f}"),
    ]
