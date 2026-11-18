"""Exercise 1 (repair): a loader that returns amplitudes which are not normalized.

The dashboard downstream divides by the norm it believes is one. Nothing crashes;
every probability is silently wrong by the same 1%.

Run: python3 chapters/chapter01/files/exercises/run_exercises.py
"""

from __future__ import annotations

import pathlib as _pathlib
import sys as _sys

# Allow `python3 ex3_shots.py` from this directory: the exercise imports
# modules that live one level up.
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from state import StateError, StateVector


class LoadError(ValueError):
    """The raw amplitudes cannot become a usable state."""


def load_amplitudes(raw: Dict[str, List[float]]) -> StateVector:
    """Turn {"real": [...], "imag": [...]} into a normalized state.

    Refuses a vector with no direction, and refuses mismatched lengths, because
    a length mismatch is a loader bug, not a state to be repaired.
    """
    real = list(raw.get("real", []))
    imag = list(raw.get("imag", []))
    if len(real) != len(imag):
        raise LoadError(f"real has {len(real)} values, imag has {len(imag)}")
    if len(real) != 2:
        raise LoadError(f"a one-qubit state needs 2 amplitudes, got {len(real)}")
    raw_state = StateVector([complex(r, i) for r, i in zip(real, imag)])
    if raw_state.norm <= 0.0:
        raise LoadError("the zero vector has no direction and cannot be normalized")
    try:
        return raw_state.normalized()
    except StateError as exc:  # pragma: no cover - defensive
        raise LoadError(str(exc)) from exc


def checks(check: Callable[[bool, str], None]) -> None:
    good = load_amplitudes({"real": [1.0, 0.0], "imag": [0.0, 0.0]})
    check(abs(good.norm - 1.0) < 1e-12, "a normalized input is returned unchanged")
    check(good.amplitudes[0] == 1.0, "the |0> amplitude survives the loader")

    biased = load_amplitudes({"real": [1.0, 0.1], "imag": [0.0, 0.0]})
    check(abs(biased.norm - 1.0) < 1e-12, "a norm of 1.01 is repaired to 1.0")
    check(abs(biased.probabilities().sum() - 1.0) < 1e-12, "the repaired state has a proper distribution")
    check(abs(biased.chance(1) - 0.00990099) < 1e-8, "the repaired P(1) is 0.1^2/1.01, not 0.1^2")

    try:
        load_amplitudes({"real": [0.0, 0.0], "imag": [0.0, 0.0]})
    except LoadError:
        check(True, "the zero vector is refused")
    else:
        check(False, "the zero vector is refused")

    try:
        load_amplitudes({"real": [1.0], "imag": [0.0]})
    except LoadError:
        check(True, "one amplitude is refused")
    else:
        check(False, "one amplitude is refused")

    try:
        load_amplitudes({"real": [1.0, 0.0], "imag": [0.0]})
    except LoadError:
        check(True, "mismatched real/imag lengths are refused")
    else:
        check(False, "mismatched real/imag lengths are refused")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
