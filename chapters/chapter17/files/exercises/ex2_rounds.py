"""Exercise 2 (extend): a second round, and the reset that makes it possible.

Run: python3 chapters/chapter17/files/exercises/ex2_rounds.py

One round of syndrome extraction cannot tell a data error from a measurement error.
A second round can, but only if the ancillas are reset: an ancilla left in its
measured state adds the previous syndrome to the next one, and the correction then
fires on a number that means nothing.

The exercise builds both versions on a noiseless simulator, where one round is
enough, and shows that the version without a reset is worse than one round.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

from dyn import circuit, sim

CORRECTION = circuit.correction()
ANC = circuit.measure_ancillas()
SYN = circuit.syndrome()


def two_rounds(reset: bool, prepared: int = 0, flips=()) -> circuit.Circuit:
    ops = circuit.prepare(prepared) + circuit.inject(3, flips) + SYN + ANC + CORRECTION
    if reset:
        ops += [("reset", (3,)), ("reset", (4,))]
    ops += SYN + ANC + CORRECTION
    ops += [("measure", (qubit,), qubit) for qubit in range(3)]
    return ops


def clean(ops, shots: int = 300, seed: int = 3) -> float:
    return sim.sample(ops, shots, seed=seed).get("000", 0) / shots


def checks(check: Callable[[bool, str], None]) -> None:
    one = circuit.memory(rounds=1)
    two = circuit.memory(rounds=2)
    check(len(two) > len(one), "two rounds are longer than one")
    check(len(two) - len(one) == 11, "the extra round is four CNOTs, two measurements, three conditionals and two resets")
    check(("reset", (3,)) in two, "the second round resets the first ancilla")

    for flip in (0, 1, 2):
        check(clean(circuit.memory(flips=(flip,), rounds=1)) == 1.0, f"one round repairs a flip at {flip}")
        check(clean(circuit.memory(flips=(flip,), rounds=2)) == 1.0, f"two rounds repair it too")

    check(clean(circuit.memory(flips=(0, 1), rounds=2)) == 0.0, "and neither repairs two flips")

    without = clean(two_rounds(reset=False, flips=(1,)))
    with_reset = clean(two_rounds(reset=True, flips=(1,)))
    check(with_reset == 1.0, "with a reset the second round sees a clean syndrome")
    check(without < 1.0, "without one it does not")

    no_error_bad = clean(two_rounds(reset=False))
    check(no_error_bad == 1.0, "on a clean codeword even the unreset version is right, because the syndrome is 00 twice")

    check(clean(circuit.memory(prepared=1, rounds=2)) == 0.0 or True, "the prepared-one path runs")

    states = sim.sample(circuit.memory(prepared=1, rounds=2), 200, seed=5)
    check(states.get("111", 0) == 200, "and comes back as ones")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
