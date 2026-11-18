"""Exercise 4 (break): a code that checks the wrong axis.

Run: python3 chapters/chapter16/files/exercises/ex4_axis.py

The repetition code exists in two orientations. Checking Z parities protects the
bit and leaves the phase; checking X parities protects the phase and leaves the bit.
Pointing the second code at bit-flip noise does nothing at all: the syndromes are
blind to the error, and the logical error becomes the parity of the flips, which is
worse than a single bare qubit.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from ecc import code, sim


def odd_parity(distance: int, p: float) -> float:
    """What the wrong-axis code leaves behind: the parity of the flips."""
    if not 0 <= p <= 1:
        raise ValueError(f"a probability is in [0, 1], got {p}")
    return float((1 - (1 - 2 * p) ** distance) / 2)


def checks(check: Callable[[bool, str], None]) -> None:
    p = 0.1

    right = code.logical_error_ideal(3, p)
    wrong = odd_parity(3, p)
    bare = p

    check(abs(right - 0.028) < 1e-9, "the right axis gives 0.028 at p=0.1")
    check(abs(wrong - 0.244) < 1e-3, "the wrong axis leaves 0.244")
    check(wrong > bare, "which is worse than the bare qubit's 0.1")
    check(wrong > 8 * right, "and eight times worse than the right code")

    check(abs(sim.phase_flip_error(3, p) - wrong) < 1e-12, "the wrong axis is the phase formula")
    check(abs(odd_parity(5, p) - sim.phase_flip_error(5, p)) < 1e-12, "at every distance")

    check(odd_parity(7, p) > odd_parity(5, p) > odd_parity(3, p), "and it gets worse with distance")
    check(code.logical_error_ideal(7, p) < code.logical_error_ideal(5, p), "while the right one gets better")

    check(odd_parity(3, 0.5) == 0.5, "at p=0.5 both are a coin flip")
    check(odd_parity(3, 0.0) == 0.0, "at p=0 the wrong axis is silent, because there is nothing to see")

    for bad in (1.5, -0.1):
        try:
            odd_parity(3, bad)
        except ValueError:
            check(True, f"p={bad} is refused")
        else:
            check(False, f"p={bad} is refused")

    # The bit-flip code's bill: three qubits to turn 0.1 into 0.028.
    check(right < bare / 3, "the right axis buys a factor of three with three qubits")
    check(wrong > bare * 2, "the wrong axis costs a factor of two with the same three qubits")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
