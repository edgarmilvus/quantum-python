"""Exercise 1 (repair): a correction table with two rows swapped.

Run: python3 chapters/chapter17/files/exercises/ex1_table.py

The table maps syndrome values 1, 2 and 3 to qubits 0, 2 and 1. Swapping the two
edge entries leaves a table that looks symmetric and corrects the wrong qubit, so a
single flip becomes two and the majority is wrong. The defect is invisible in the
circuit and obvious in the histogram.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from dyn import circuit, sim


def memory_with_table(table, prepared: int = 0, flips=()) -> circuit.Circuit:
    """The memory circuit, with a correction table supplied by the caller."""
    ops = circuit.prepare(prepared)
    ops += circuit.inject(3, flips)
    ops += circuit.syndrome(3)
    ops += circuit.measure_ancillas(3)
    ops += table
    ops += [("measure", (qubit,), qubit) for qubit in range(3)]
    return ops


CORRECT = [
    ("ifreg", ((3, 4), 1), [("x", (0,))]),
    ("ifreg", ((3, 4), 3), [("x", (1,))]),
    ("ifreg", ((3, 4), 2), [("x", (2,))]),
]

SWAPPED = [
    ("ifreg", ((3, 4), 1), [("x", (2,))]),
    ("ifreg", ((3, 4), 3), [("x", (1,))]),
    ("ifreg", ((3, 4), 2), [("x", (0,))]),
]


def clean(ops, shots: int = 300, seed: int = 1) -> float:
    return sim.sample(ops, shots, seed=seed).get("000", 0) / shots


def checks(check: Callable[[bool, str], None]) -> None:
    for flip in (0, 2):
        right = clean(memory_with_table(CORRECT, flips=(flip,)))
        wrong = clean(memory_with_table(SWAPPED, flips=(flip,)))
        check(right == 1.0, f"the correct table repairs a flip at {flip}")
        check(wrong == 0.0, f"the swapped table does not, at {flip}")

    middle_right = clean(memory_with_table(CORRECT, flips=(1,)))
    middle_wrong = clean(memory_with_table(SWAPPED, flips=(1,)))
    check(middle_right == 1.0 and middle_wrong == 1.0, "the middle row is the same in both tables")

    for flip in (0, 2):
        counts = sim.sample(memory_with_table(SWAPPED, flips=(flip,)), 300, seed=1)
        check(counts.get("101", 0) > 250 or counts.get("100", 0) > 250,
              f"the swapped table leaves two flips for an injected one at {flip}")

    check(clean(memory_with_table(CORRECT, flips=(0, 1))) == 0.0, "two flips defeat both tables")

    no_error = clean(memory_with_table(SWAPPED))
    check(no_error == 1.0, "and with no error the swapped table is harmless, which is why it ships")

    check(len(CORRECT) == len(SWAPPED) == 3, "both tables have three rows")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
