"""A one-qubit state vector, written by hand.

The point of this file is that nothing here is quantum: it is a numpy array of
complex numbers with three rules attached. Every rule is checked, and every
check raises with the value that failed.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np

DEFAULT_TOL = 1e-12


class StateError(ValueError):
    """A state that cannot be used, with the reason in the message."""


class UnnormalizedState(StateError):
    """Amplitudes whose squared magnitudes do not sum to one."""


class StateVector:
    """Two complex amplitudes, and the operations that are legal on them.

    The state is immutable: every operation returns a new StateVector, so a
    caller cannot mutate a state that another function is reading.
    """

    __slots__ = ("_amplitudes",)

    def __init__(self, amplitudes: Iterable[complex]) -> None:
        values = np.asarray(list(amplitudes), dtype=np.complex128)
        if values.ndim != 1:
            raise StateError(f"amplitudes must be one-dimensional, got shape {values.shape}")
        if values.size != 2:
            raise StateError(f"a one-qubit state has 2 amplitudes, got {values.size}")
        if not np.all(np.isfinite(values)):
            raise StateError(f"amplitudes contain a non-finite value: {values}")
        self._amplitudes = values

    # -- construction ----------------------------------------------------
    @classmethod
    def from_amplitudes(cls, values: Iterable[complex], tol: float = DEFAULT_TOL) -> "StateVector":
        """Build a state, refusing one that is not normalized."""
        state = cls(values)
        norm = state.norm
        if abs(norm - 1.0) > tol:
            raise UnnormalizedState(
                f"amplitudes have squared norm {norm:.15f}, expected 1.0 within {tol:g}; "
                f"call .normalized() if the values are meant to be rescaled"
            )
        return state

    @classmethod
    def zero(cls) -> "StateVector":
        """The basis state |0>, as the array [1, 0]."""
        return cls([1.0, 0.0])

    @classmethod
    def one(cls) -> "StateVector":
        """The basis state |1>, as the array [0, 1]."""
        return cls([0.0, 1.0])

    # -- properties ------------------------------------------------------
    @property
    def amplitudes(self) -> np.ndarray:
        """A copy: mutating what you get back cannot corrupt the state."""
        return self._amplitudes.copy()

    @property
    def norm(self) -> float:
        """The squared norm, sum of |a_i|^2. It must be 1.0."""
        return float(np.sum(np.abs(self._amplitudes) ** 2))

    def probabilities(self) -> np.ndarray:
        """The measurement distribution, p_i = |a_i|^2."""
        return np.abs(self._amplitudes) ** 2

    def labels(self) -> list[str]:
        return ["|0>", "|1>"]

    # -- operations ------------------------------------------------------
    def normalized(self) -> "StateVector":
        """Rescale to norm one, or refuse if that is impossible."""
        norm = self.norm
        if norm <= 0.0:
            raise UnnormalizedState("cannot normalize the zero vector: it has no direction")
        return StateVector(self._amplitudes / np.sqrt(norm))

    def inner(self, other: "StateVector") -> complex:
        """<self|other>: the conjugate of self, dotted with other."""
        return complex(np.vdot(self._amplitudes, other._amplitudes))

    def with_phase(self, phase: complex) -> "StateVector":
        """Multiply every amplitude by the same unit-modulus number."""
        if abs(abs(phase) - 1.0) > DEFAULT_TOL:
            raise StateError(f"a phase must have modulus 1, got |{abs(phase):.6f}|")
        return StateVector(self._amplitudes * phase)

    def chance(self, index: int) -> float:
        """The probability of one outcome, with an index check."""
        if index not in (0, 1):
            raise StateError(f"one qubit has outcomes 0 and 1, got {index}")
        return float(self.probabilities()[index])

    # -- dunder ----------------------------------------------------------
    def __len__(self) -> int:
        return int(self._amplitudes.size)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, StateVector):
            return NotImplemented
        return bool(np.allclose(self._amplitudes, other._amplitudes, atol=DEFAULT_TOL))

    def __hash__(self) -> int:
        return hash(tuple(np.round(self._amplitudes, 12)))

    def __repr__(self) -> str:
        a, b = self._amplitudes
        return f"StateVector([{a.real:+.6f}{a.imag:+.6f}j, {b.real:+.6f}{b.imag:+.6f}j])"


def hadamard(state: StateVector) -> StateVector:
    """H on a single qubit: (a + b) / sqrt(2), (a - b) / sqrt(2)."""
    a, b = state.amplitudes
    root = np.sqrt(2.0)
    return StateVector([(a + b) / root, (a - b) / root])


def z_gate(state: StateVector) -> StateVector:
    """Z on a single qubit: leaves |0> alone, flips the sign of |1>."""
    a, b = state.amplitudes
    return StateVector([a, -b])


def x_gate(state: StateVector) -> StateVector:
    """X on a single qubit: swaps the two amplitudes."""
    a, b = state.amplitudes
    return StateVector([b, a])
