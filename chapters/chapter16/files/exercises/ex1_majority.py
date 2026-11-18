"""Exercise 1 (repair): a decoder that reads one qubit and calls it a vote.

Run: python3 chapters/chapter16/files/exercises/ex1_majority.py

Taking the first bit is the simplest decoder and the most plausible-looking. It is
right whenever the first qubit is right, so it passes every test that flips the
last qubit, and its logical error is the physical error of one qubit instead of the
binomial tail of three.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Sequence

import numpy as np

from ecc import code, sim


def decode_first(bits: Sequence[int]) -> int:
    """The defect: the first qubit is the answer."""
    if not bits:
        raise ValueError("an empty codeword has no answer")
    return int(bits[0])


def decode_majority(bits: Sequence[int]) -> int:
    return code.Repetition(len(bits)).decode(bits)


def error_rate(decoder, distance: int, p: float, trials: int = 20000, seed: int = 2) -> float:
    rng = np.random.default_rng(seed)
    wrong = 0
    for _ in range(trials):
        flips = rng.random(distance) < p
        bits = [int(flip) for flip in flips]
        if decoder(bits) != 0:
            wrong += 1
    return wrong / trials


def checks(check: Callable[[bool, str], None]) -> None:
    three = code.Repetition(3)

    check(decode_first([0, 0, 0]) == 0, "the defect is right on a clean codeword")
    check(decode_first([0, 0, 1]) == 0, "and on a flip of the last qubit")
    check(decode_first([1, 0, 0]) == 1, "but wrong on a flip of the first")
    check(three.decode([1, 0, 0]) == 0, "where the majority is right")

    check(decode_first([1, 1, 0]) == 1, "two flips at the front fool it")
    check(three.decode([1, 1, 0]) == 1, "and fool the majority too, which is the limit")

    defect = error_rate(decode_first, 3, 0.1)
    correct = error_rate(decode_majority, 3, 0.1)
    check(abs(defect - 0.1) < 0.01, "the defect's rate is the physical rate of one qubit")
    check(abs(correct - 0.028) < 0.005, "the majority's rate is the binomial tail")
    check(defect > 3 * correct, "so the defect is more than three times worse")

    five = code.Repetition(5)
    check(decode_first([1, 0, 0, 0, 0]) == 1, "the defect ignores four qubits of evidence")
    check(five.decode([1, 0, 0, 0, 0]) == 0, "which the majority uses")
    check(abs(error_rate(decode_first, 5, 0.1) - 0.1) < 0.01, "and its rate does not improve with distance")
    check(error_rate(decode_majority, 5, 0.1) < error_rate(decode_majority, 3, 0.1), "while the majority's does")

    for bits in ([0, 1], [0, 1, 0, 1]):
        try:
            decode_majority(bits)
        except ValueError:
            check(True, f"an even codeword of {len(bits)} has no majority")
        else:
            check(False, f"an even codeword of {len(bits)} has no majority")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
