"""Reading the readout calibration, and correcting counts with it.

A device measures wrongly a known fraction of the time. Calibrating means preparing
states whose answer you know, measuring them, and recording how often the answer came
back wrong. Correcting means inverting that record and applying it to the data you care
about — which works, and which also amplifies noise, and the chapter measures both.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np

from stats import DEFAULT_ORDER, clip_and_renormalize, confusion, counts_to_distribution, invert

ROOT = Path(__file__).resolve().parents[3]


def load(path: Path | None = None) -> dict:
    target = Path(path) if path else (ROOT / "runs/0009-ibm-readout/result.json")
    record = json.loads(Path(target).read_text())
    if "counts" not in record or "preparations" not in record:
        raise ValueError(f"{target} is not a calibration file")
    return record


def expected_key(wires: list, width: int = 2) -> str:
    """The Qiskit key a preparation should produce.

    Qiskit's bitstring puts qubit 0 last, so X on wire 1 is "10", not "01". The
    calibration run made that concrete: the prepared |01> came back as "10" and the
    matrix was transposed until this function existed.
    """
    value = 0
    for wire in wires:
        value |= 1 << wire
    return format(value, f"0{width}b")


def confusion_from_preparations(
    counts_by_preparation: Dict[str, Dict[str, int]],
    preparations: Dict[str, list],
) -> np.ndarray:
    """Build the matrix from counts and the wires each preparation flipped."""
    rows = {}
    for name, wires in preparations.items():
        rows[expected_key(list(wires))] = counts_by_preparation[name]
    return confusion(rows, DEFAULT_ORDER)


def matrix(record: dict) -> np.ndarray:
    """Rows are prepared states, columns measured, both in Qiskit's key order."""
    return confusion_from_preparations(record["counts"], record["preparations"])


def diagonal_error(matrix_: np.ndarray) -> float:
    """The average chance of reading the prepared state correctly, inverted."""
    return float(1.0 - np.mean(np.diag(matrix_)))


def inverse_matrix(matrix_: np.ndarray) -> np.ndarray:
    return invert(matrix_)


def correct_distribution(distribution: np.ndarray, inverse: np.ndarray) -> Tuple[np.ndarray, float]:
    """Apply the inverse and report the mass that had to be clipped."""
    corrected = inverse @ np.asarray(distribution, dtype=float)
    return clip_and_renormalize(corrected)


def expectation(distribution: np.ndarray, order=DEFAULT_ORDER) -> float:
    """E = P(same) - P(different) from a four-outcome distribution."""
    labels = list(order)
    if distribution.size != len(labels):
        raise ValueError(f"expected {len(labels)} outcomes, got {distribution.size}")
    same = sum(distribution[labels.index(label)] for label in ("00", "11"))
    different = sum(distribution[labels.index(label)] for label in ("01", "10"))
    return float(same - different)


def corrected_chsh(counts_by_setting: Dict[str, Dict[str, int]], inverse: np.ndarray) -> Dict[str, Dict[str, float]]:
    """Per setting: the raw expectation, the corrected one, and the clipped mass."""
    out = {}
    for name, counts in counts_by_setting.items():
        distribution = counts_to_distribution(counts, DEFAULT_ORDER)
        corrected, mass = correct_distribution(distribution, inverse)
        out[name] = {
            "raw": expectation(distribution),
            "corrected": expectation(corrected),
            "clipped_mass": mass,
        }
    return out


def chsh_from(values: Dict[str, Dict[str, float]], key: str) -> float:
    return (
        values["ab"][key]
        - values["ab_prime"][key]
        + values["a_prime_b"][key]
        + values["a_prime_b_prime"][key]
    )
