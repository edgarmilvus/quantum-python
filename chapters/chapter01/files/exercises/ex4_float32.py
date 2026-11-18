"""Exercise 4 (break): the precision at which normalization stops holding.

The same pipeline runs float32 on a GPU and float64 on the CPU. A rotation that
is not its own inverse drifts, and float32 reaches a visible error after a few
thousand cycles while float64 does not within the same budget.

Run: python3 chapters/chapter01/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List, Optional

import numpy as np

DEFAULT_MAX_CYCLES = 20_000


def rotate(amplitudes: np.ndarray, angle: float, dtype) -> np.ndarray:
    """One real rotation by `angle`, in the requested precision."""
    cosine = dtype(np.cos(angle))
    sine = dtype(np.sin(angle))
    a, b = amplitudes
    return np.array([cosine * a - sine * b, sine * a + cosine * b], dtype=dtype)


def norm_trace(cycles: int, angle: float = 0.3, dtype=np.float32) -> List[float]:
    """The squared norm after each cycle, as float64 numbers for comparison."""
    vector = np.array([1.0, 0.0], dtype=dtype)
    trace = []
    for _ in range(cycles):
        vector = rotate(vector, angle, dtype)
        trace.append(float(np.sum(np.abs(vector) ** 2, dtype=np.float64)))
    return trace


def first_failure(
    tolerance: float = 1e-4,
    max_cycles: int = DEFAULT_MAX_CYCLES,
    angle: float = 0.3,
    dtype=np.float32,
) -> Optional[int]:
    """The first cycle whose norm is off by more than `tolerance`, or None."""
    if tolerance <= 0:
        raise ValueError(f"tolerance must be positive, got {tolerance}")
    vector = np.array([1.0, 0.0], dtype=dtype)
    for cycle in range(1, max_cycles + 1):
        vector = rotate(vector, angle, dtype)
        norm = float(np.sum(np.abs(vector) ** 2, dtype=np.float64))
        if abs(norm - 1.0) > tolerance:
            return cycle
    return None


def checks(check: Callable[[bool, str], None]) -> None:
    fails_at = first_failure(dtype=np.float32)
    check(fails_at is not None, "float32 breaks its norm inside 20k cycles")
    check(fails_at is not None and 1000 < fails_at < 5000, "float32 breaks between 1000 and 5000 cycles")

    check(first_failure(dtype=np.float64) is None, "float64 holds its norm for the same budget")

    trace = norm_trace(2000, dtype=np.float32)
    check(abs(trace[0] - 1.0) < 1e-6, "the first cycle is still accurate in float32")
    check(abs(trace[-1] - 1.0) > abs(trace[0] - 1.0), "the error grows with the cycle count")

    frozen = norm_trace(50, angle=0.0, dtype=np.float32)
    check(max(abs(n - 1.0) for n in frozen) < 1e-7, "a zero angle leaves the norm alone")

    loose = first_failure(tolerance=1e-3, dtype=np.float32)
    check(loose is None or (fails_at is not None and loose > fails_at), "a looser tolerance fails later")

    single = rotate(np.array([1.0, 0.0], dtype=np.float32), 0.3, np.float32)
    check(single.dtype == np.float32, "the rotation keeps the requested precision")
    check(abs(float(np.sum(np.abs(single) ** 2)) - 1.0) < 1e-6, "one rotation preserves the norm to float32 precision")

    try:
        first_failure(tolerance=0.0)
    except ValueError:
        check(True, "a non-positive tolerance is refused")
    else:
        check(False, "a non-positive tolerance is refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
