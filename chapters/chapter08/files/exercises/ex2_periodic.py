"""Exercise 2 (extend): the transform of a periodic state.

A state that is uniform over every fourth basis state transforms to a state with support
on four indices. The exercise checks that, because periodicity is the property phase
estimation exploits.

Run: python3 chapters/chapter08/files/exercises/ex2_periodic.py
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

import numpy as np

import qft


def periodic_state(n: int, period: int) -> np.ndarray:
    """Uniform over indices that are multiples of `period`."""
    if period < 1 or (1 << n) % period:
        raise ValueError(f"the period must divide {1 << n}, got {period}")
    size = 1 << n
    state = np.zeros(size, dtype=np.complex128)
    indices = list(range(0, size, period))
    for index in indices:
        state[index] = 1.0 / np.sqrt(len(indices))
    return state


def support(distribution: Dict[int, float], threshold: float = 1e-9) -> List[int]:
    return [k for k, p in distribution.items() if p > threshold]


def transform(state: np.ndarray) -> Dict[int, float]:
    probabilities = np.abs(qft.dft(int(np.log2(state.size))) @ state) ** 2
    return {k: float(p) for k, p in enumerate(probabilities)}


def checks(check: Callable[[bool, str], None]) -> None:
    n = 4
    period_two = transform(periodic_state(n, 2))
    peaks = support(period_two)
    check(peaks == [0, 8], "period 2 gives peaks at 0 and half the register")
    check(abs(period_two[0] - 0.5) < 1e-9, "each peak holds half the probability")

    period_four = transform(periodic_state(n, 4))
    check(support(period_four) == [0, 4, 8, 12], "period 4 gives four peaks")
    check(all(abs(period_four[k] - 0.25) < 1e-9 for k in (0, 4, 8, 12)), "each holding a quarter")

    uniform = transform(periodic_state(n, 1))
    check(support(uniform) == [0], "a flat state transforms to a single peak at zero")
    check(abs(uniform[0] - 1.0) < 1e-9, "holding all the probability")

    delta = transform(periodic_state(n, 16))
    check(len(support(delta)) == 16, "a single index transforms to a flat state")
    check(all(abs(delta[k] - 1 / 16) < 1e-9 for k in range(16)), "every index holds one sixteenth")

    try:
        periodic_state(4, 3)
    except ValueError:
        check(True, "a period that does not divide the size is refused")
    else:
        check(False, "a period that does not divide the size is refused")

    check(abs(sum(period_four.values()) - 1.0) < 1e-9, "the transformed distribution sums to one")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
