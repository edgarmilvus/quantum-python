"""Exercise 1 (repair): a loader whose tensor product came out backwards.

The file builds |wire1> tensor |wire0> but the sampler labels the result |wire0
wire1>. Every outcome is mirrored: a state prepared as |10> is reported as |01>.

Run: python3 chapters/chapter02/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import numpy as np

from register import Register, RegisterError


def build(wire0: np.ndarray, wire1: np.ndarray) -> Register:
    """Build the register so that index = wire0 * 2 + wire1.

    The defect this repairs is the factor order: `np.kron(wire1, wire0)` gives a
    register whose labels are the mirror image of what the caller asked for.
    """
    a = np.asarray(wire0, dtype=np.complex128)
    b = np.asarray(wire1, dtype=np.complex128)
    if a.shape != (2,) or b.shape != (2,):
        raise RegisterError(f"each wire needs 2 amplitudes, got {a.shape} and {b.shape}")
    return Register(np.kron(a, b))


def index_of(state: Register) -> int:
    return int(np.argmax(np.abs(state.amplitudes)))


def checks(check: Callable[[bool, str], None]) -> None:
    zero = np.array([1.0, 0.0])
    one = np.array([0.0, 1.0])

    check(index_of(build(zero, zero)) == 0, "|0>|0> is index 0")
    check(index_of(build(zero, one)) == 1, "|0>|1> is index 1")
    check(index_of(build(one, zero)) == 2, "|1>|0> is index 2")
    check(index_of(build(one, one)) == 3, "|1>|1> is index 3")

    reversed_state = Register(np.kron(one, zero))
    check(index_of(reversed_state) == 2, "the wrong order would also give index 2 for |1>|0>")
    check(build(zero, one).bitstring(1) == "|01>", "the label matches the index")
    check(build(one, zero).bitstring(2) == "|10>", "the second wire is the low bit of the index")
    check(np.allclose(build(zero, one).probabilities(), [0, 1, 0, 0]), "the distribution has one peak")

    try:
        build(zero, np.array([1.0, 0.0, 0.0]))
    except RegisterError:
        check(True, "a three-amplitude wire is refused")
    else:
        check(False, "a three-amplitude wire is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
