"""Exercise 5, file 1 of 3: the pure part.

Turns a state and its counts into rows of numbers. Imports nothing from the
chapter except the state type, touches no random number generator, prints
nothing, so it can be tested by calling it.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from state import StateError, StateVector

Row = Tuple[str, float, float, float, int, float]


def build_rows(state: StateVector, counts: Dict[str, int]) -> List[Row]:
    """One row per outcome: label, real part, imaginary part, p, count, frequency."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError(f"counts must contain at least one shot, got {total}")

    amplitudes = state.amplitudes
    probabilities = state.probabilities()
    labels = state.labels()

    rows: List[Row] = []
    for index, label in enumerate(labels):
        key = str(index)
        count = int(counts.get(key, 0))
        rows.append(
            (
                label,
                float(amplitudes[index].real),
                float(amplitudes[index].imag),
                float(probabilities[index]),
                count,
                count / total,
            )
        )
    return rows


def totals(rows: List[Row]) -> Dict[str, float]:
    """The three sums a reader checks first."""
    if not rows:
        raise StateError("no rows to total")
    return {
        "probability": sum(row[3] for row in rows),
        "count": float(sum(row[4] for row in rows)),
        "frequency": sum(row[5] for row in rows),
    }


def largest_gap(rows: List[Row]) -> float:
    """The biggest difference between an observed frequency and its probability."""
    if not rows:
        raise StateError("no rows to compare")
    return max(abs(row[5] - row[3]) for row in rows)
