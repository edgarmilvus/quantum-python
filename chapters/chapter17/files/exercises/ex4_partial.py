"""Exercise 4 (break): a correction that tests one syndrome and ignores the rest.

Run: python3 chapters/chapter17/files/exercises/ex4_partial.py

The full table has three rows. A table with one row still compiles, still runs, and
still fixes the encoder's favourite error, so a test that injects only that error
passes. The other two errors stay in the codeword, and the logical bit survives only
because the majority is forgiving.

The exercise measures the codeword, not the logical bit, because the logical bit is
the wrong metric here: a single flip never breaks a majority, and the point is that
the correction stopped happening.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from dyn import circuit, sim

FULL = circuit.correction()
PARTIAL = [("ifreg", ((3, 4), 1), [("x", (0,))])]


def memory_with(table, flips=()) -> circuit.Circuit:
    ops = circuit.prepare(0) + circuit.inject(3, flips) + circuit.syndrome(3)
    ops += circuit.measure_ancillas(3) + table
    ops += [("measure", (qubit,), qubit) for qubit in range(3)]
    return ops


def clean(ops, shots: int = 300, seed: int = 6) -> float:
    return sim.sample(ops, shots, seed=seed).get("000", 0) / shots


def checks(check: Callable[[bool, str], None]) -> None:
    check(len(FULL) == 3 and len(PARTIAL) == 1, "the full table has three rows, the partial one")

    check(clean(memory_with(FULL, (0,))) == 1.0, "the full table repairs a flip at 0")
    check(clean(memory_with(PARTIAL, (0,))) == 1.0, "so does the partial one, for that error")

    check(clean(memory_with(FULL, (1,))) == 1.0, "the full table repairs a flip at 1")
    check(clean(memory_with(PARTIAL, (1,))) == 0.0, "the partial one leaves it")

    check(clean(memory_with(FULL, (2,))) == 1.0, "and at 2")
    check(clean(memory_with(PARTIAL, (2,))) == 0.0, "the partial one leaves it too")

    check(clean(memory_with(PARTIAL)) == 1.0, "with no error the partial table is harmless")

    counts = sim.sample(memory_with(PARTIAL, (1,)), 300, seed=6)
    check(counts.get("010", 0) > 250, "the leftover error is visible in the codeword")

    # The logical bit is the wrong metric: a single flip is a majority.
    total = sum(counts.values())
    logical_wrong = sum(
        count for key, count in counts.items()
        if (sum(int(character) for character in key) * 2 > 3)
    ) / total
    check(logical_wrong == 0.0, "and the logical bit is still right, which is why the defect hides")

    check(clean(memory_with(FULL, (1, 2))) == 0.0, "two errors defeat both tables")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
