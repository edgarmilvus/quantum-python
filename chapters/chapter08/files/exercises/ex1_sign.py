"""Exercise 1 (repair): the inverse transform with the wrong sign.

Applying the forward DFT where the inverse belongs mirrors the answer: a phase of 1/8 at
three bits comes back as 7/8. The circuit, the depth and the distribution are all
plausible, and the number is wrong.

Run: python3 chapters/chapter08/files/exercises/ex1_sign.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict

import numpy as np

import phase
import qft


def pea_with(phi: float, n: int, inverse: np.ndarray) -> Dict[int, float]:
    total = n + 1
    state = phase.prepare(n)
    for wire in range(n):
        state = qft.embed_one(qft.H2, wire, total) @ state
    for wire in range(n):
        state = phase.controlled_power(phi, power=n - 1 - wire, control=wire, target=n, total=total) @ state
    embedded = np.kron(inverse, np.eye(2, dtype=np.complex128))
    state = embedded @ state
    probabilities = np.abs(state) ** 2
    return {k: float(probabilities[2 * k] + probabilities[2 * k + 1]) for k in range(1 << n)}


def checks(check: Callable[[bool, str], None]) -> None:
    n = 3
    right = pea_with(0.125, n, qft.dft(n, sign=-1))
    wrong = pea_with(0.125, n, qft.dft(n, sign=1))

    best_right = max(right, key=right.get)
    best_wrong = max(wrong, key=wrong.get)
    check(best_right == 1, "the repair returns k=1 for a phase of one eighth")
    check(best_wrong == 7, "the defect returns k=7, the mirror image")
    check(abs(right[1] - 1.0) < 1e-9, "the repair is certain")
    check(abs(wrong[7] - 1.0) < 1e-9, "the defect is certain too")

    check(best_right + best_wrong == (1 << n), "the two indices sum to the register size")
    check(np.allclose(qft.dft(n, -1), qft.dft(n, 1).conj().T), "the two transforms are adjoints")

    mirrored = pea_with(0.375, n, qft.dft(n, sign=1))
    check(max(mirrored, key=mirrored.get) == 5, "a phase of three eighths mirrors to five eighths")

    identity = pea_with(0.0, n, qft.dft(n, sign=1))
    check(max(identity, key=identity.get) == 0, "a zero phase is its own mirror")

    check(sum(right.values()) == sum(right.values()), "the distributions are sums of probabilities")
    check(abs(sum(right.values()) - 1.0) < 1e-9, "the repair's distribution sums to one")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
