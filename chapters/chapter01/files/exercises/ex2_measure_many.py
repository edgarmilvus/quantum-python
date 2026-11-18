"""Exercise 2 (extend): many measurements, a reproducible seed, a frequency table.

The dashboard needs frequencies, not one outcome, and a reviewer needs the run
to repeat exactly.

Run: python3 chapters/chapter01/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List, Tuple

import numpy as np

from sampling import sample_counts
from state import StateVector


def measure_many(state: StateVector, shots: int, seed: int) -> Dict[str, int]:
    """Counts for `shots` measurements, always containing both outcomes."""
    counts = sample_counts(state, shots=shots, seed=seed)
    return {"0": counts.get("0", 0), "1": counts.get("1", 0)}


def frequency_table(counts: Dict[str, int]) -> List[Tuple[str, int, float]]:
    """(label, count, frequency) rows, ordered by outcome."""
    total = sum(counts.values())
    if total == 0:
        raise ValueError("a frequency table needs at least one shot")
    return [(label, counts.get(label, 0), counts.get(label, 0) / total) for label in ("0", "1")]


def most_likely(counts: Dict[str, int]) -> str:
    """The outcome with the highest count, ties broken toward '0'."""
    if not counts or sum(counts.values()) == 0:
        raise ValueError("no counts to compare")
    return max(("0", "1"), key=lambda label: (counts.get(label, 0), label == "0"))


def checks(check: Callable[[bool, str], None]) -> None:
    half = StateVector([np.sqrt(0.5), np.sqrt(0.5)])

    first = measure_many(half, shots=1000, seed=1)
    second = measure_many(half, shots=1000, seed=1)
    check(first == second, "the same seed reproduces the counts")
    check(sum(first.values()) == 1000, "the counts add up to the shots")
    check(set(first) == {"0", "1"}, "both outcomes are present even when one is zero")
    check(abs(first["0"] / 1000 - 0.5) < 0.05, "1000 shots land within 5 points of one half")

    table = frequency_table(first)
    check(len(table) == 2, "the table has one row per outcome")
    check(abs(sum(row[2] for row in table) - 1.0) < 1e-12, "the frequencies sum to one")
    check(table[0][0] == "0" and table[1][0] == "1", "rows are ordered by outcome")

    certain = measure_many(StateVector([1.0, 0.0]), shots=50, seed=3)
    check(certain == {"0": 50, "1": 0}, "a certain outcome gets every shot")
    check(most_likely(certain) == "0", "the most likely outcome is the certain one")

    skewed = measure_many(StateVector([np.sqrt(0.9), np.sqrt(0.1)]), shots=2000, seed=4)
    check(most_likely(skewed) == "0", "the 90/10 state favours zero")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
