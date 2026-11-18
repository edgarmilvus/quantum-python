"""Exercise 2 (extend): a gate on the second wire only, with a wire map.

A controlled experiment needs X on wire 1 and nothing on wire 0. The naive kron
order puts it on the wrong wire, and the symptom is a mirrored histogram.

Run: python3 chapters/chapter02/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import numpy as np

from gates import H, X, Z, apply_one, embed
from register import Register

GateList = Sequence[Tuple[np.ndarray, int]]


def apply_to(state: Register, gate: np.ndarray, wire: int, wire_map: Dict[int, int]) -> Register:
    """Apply `gate` to a logical wire, using `wire_map` to find its tensor slot.

    wire_map maps logical wire -> position in the tensor product. It exists so a
    caller can keep its own numbering and let the adapter translate.
    """
    if wire not in wire_map:
        raise ValueError(f"wire {wire} is not in the map {sorted(wire_map)}")
    slot = wire_map[wire]
    return Register(apply_one(state.amplitudes, gate, slot, wires=2))


def run(state: Register, gates: GateList, wire_map: Dict[int, int]) -> Register:
    out = state
    for gate, wire in gates:
        out = apply_to(out, gate, wire, wire_map)
    return out


def checks(check: Callable[[bool, str], None]) -> None:
    identity = {0: 0, 1: 1}
    swapped = {0: 1, 1: 0}
    zero = Register.zero()

    on_second = run(zero, [(X, 1)], identity)
    check(np.allclose(on_second.probabilities(), [0, 1, 0, 0]), "X on wire 1 lands at index 1")
    check(on_second.bitstring(1) == "|01>", "the label says the second wire moved")

    mirrored = run(zero, [(X, 1)], swapped)
    check(np.allclose(mirrored.probabilities(), [0, 0, 1, 0]), "the same call with a swapped map lands at index 2")

    both = run(zero, [(X, 0), (X, 1)], identity)
    check(np.allclose(both.probabilities(), [0, 0, 0, 1]), "X on both wires is |11>")

    split = run(zero, [(H, 1)], identity)
    check(abs(split.probabilities()[0] - 0.5) < 1e-9, "H on wire 1 puts half the probability at index 0")
    check(abs(split.probabilities()[1] - 0.5) < 1e-9, "and half at index 1")
    check(abs(split.probabilities()[2]) < 1e-12 and abs(split.probabilities()[3]) < 1e-12,
          "H on wire 1 never touches indices 2 and 3")

    after_z = run(split, [(Z, 1)], identity)
    check(np.allclose(after_z.probabilities(), split.probabilities()), "Z on wire 1 leaves the probabilities alone")
    check(not np.allclose(after_z.amplitudes, split.amplitudes), "Z on wire 1 changes the amplitudes")

    try:
        apply_to(zero, X, 2, identity)
    except ValueError:
        check(True, "wire 2 is refused when the map has two entries")
    else:
        check(False, "wire 2 is refused when the map has two entries")

    check(np.allclose(run(zero, [(X, 0), (X, 0)], identity).amplitudes, zero.amplitudes), "X twice cancels")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
