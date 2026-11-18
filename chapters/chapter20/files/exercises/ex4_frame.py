"""Exercise 4 (break): a Pauli frame with the two bits swapped.

Run: python3 chapters/chapter20/files/exercises/ex4_frame.py

The correction is X for m1 and Z for m0. Swap them and every branch that needs one gets
the other. The result is not noise: it is a fidelity of 0.6875 on an exact simulation,
which clears the two-thirds line and would pass a report that only checks the verdict.
That is the trap: the threshold is not a test.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

import math
from typing import Callable, Dict, Tuple

from qiskit.quantum_info import Statevector

from teleport import Prepared, fidelity
from teleport.circuit import BASES, before_measurement


def exact_counts(prepared: Prepared) -> Dict[str, Dict[str, int]]:
    counts: Dict[str, Dict[str, int]] = {}
    for basis in BASES:
        circuit = before_measurement(prepared)
        if basis == "X":
            circuit.h(2)
        elif basis == "Y":
            circuit.sdg(2)
            circuit.h(2)
        probabilities = Statevector(circuit).probabilities_dict()
        counts[basis] = {key.replace(" ", ""): int(round(p * 1_000_000)) for key, p in probabilities.items()}
    return counts


def frame(counts: Dict[str, int], basis: str, swap: bool = False) -> Dict[str, int]:
    """Apply the frame; `swap` is the defect: X on m0 and Z on m1."""
    if basis not in BASES:
        raise ValueError(f"a basis is one of {BASES}, got {basis!r}")
    fx = {"X": 1, "Y": 1, "Z": 0}[basis]
    fz = {"X": 0, "Y": 1, "Z": 1}[basis]
    if swap:
        fx, fz = fz, fx
    out = {"0": 0, "1": 0}
    for key, count in counts.items():
        bit = int(key[0])
        m0, m1 = int(key[2]), int(key[1])
        out[str(bit ^ (fx * m0) ^ (fz * m1))] += count
    return out


def bloch(counts: Dict[str, Dict[str, int]], swap: bool = False) -> Tuple[float, float, float]:
    values = []
    for basis in BASES:
        fixed = frame(counts[basis], basis, swap)
        total = sum(fixed.values())
        values.append((fixed["0"] - fixed["1"]) / total)
    return tuple(values)


def checks(check: Callable[[bool, str], None]) -> None:
    prepared = Prepared(math.pi / 3, math.pi / 4)
    counts = exact_counts(prepared)

    correct = fidelity(prepared, bloch(counts, swap=False))
    swapped = fidelity(prepared, bloch(counts, swap=True))

    check(abs(correct - 1.0) < 1e-3, "the correct frame returns the state")
    check(abs(swapped - 0.6875) < 1e-3, "the swapped frame returns 0.6875")
    check(swapped > 2 / 3, "which is above the classical line")
    check(swapped < 0.75, "and well below the correct run")
    check(correct - swapped > 0.3, "the gap is more than thirty points")

    check(abs(bloch(counts)[0] - 0.6124) < 1e-3, "the correct X component is 0.6124")
    check(abs(bloch(counts)[2] - 0.5) < 1e-3, "the correct Z component is 0.5")
    check(abs(bloch(counts, swap=True)[0]) < 0.75, "the swapped X component is not the state's")

    check(frame(counts["Z"], "Z", swap=False)["1"] == frame(counts["Z"], "Z", swap=False)["1"],
          "the frame is deterministic")
    check(sum(frame(counts["X"], "X") .values()) == sum(counts["X"].values()), "the frame keeps every shot")

    for bad in ("W", ""):
        try:
            frame(counts["X"], bad)
        except ValueError:
            check(True, f"the basis {bad!r} is refused")
        else:
            check(False, f"the basis {bad!r} is refused")

    check(correct > swapped, "the correct frame is the better one")
    check(len(counts) == 3, "three bases are simulated")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
