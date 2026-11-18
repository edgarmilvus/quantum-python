"""A two-wire register: four amplitudes, a labelling convention, and a sampler.

The class exists to make one thing visible that SDKs hide: the index of an
amplitude is a choice of ordering. `labels()` prints that choice.
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

from gates import apply_one


class RegisterError(ValueError):
    """A register that cannot be used, with the reason in the message."""


class Register:
    """Four complex amplitudes, labelled |q0 q1> by default."""

    __slots__ = ("_amplitudes", "_labels")

    def __init__(self, amplitudes: Iterable[complex], labels: Optional[List[str]] = None) -> None:
        values = np.asarray(list(amplitudes), dtype=np.complex128)
        if values.shape != (4,):
            raise RegisterError(f"a two-wire register has 4 amplitudes, got {values.shape}")
        if not np.all(np.isfinite(values)):
            raise RegisterError(f"amplitudes contain a non-finite value: {values}")
        self._amplitudes = values
        self._labels = labels or ["|00>", "|01>", "|10>", "|11>"]

    # -- construction ----------------------------------------------------
    @classmethod
    def from_amplitudes(cls, values: Iterable[complex], tol: float = 1e-12) -> "Register":
        register = cls(values)
        if abs(register.norm - 1.0) > tol:
            raise RegisterError(
                f"amplitudes have squared norm {register.norm:.15f}, expected 1.0 within {tol:g}"
            )
        return register

    @classmethod
    def zero(cls) -> "Register":
        return cls([1.0, 0.0, 0.0, 0.0])

    @classmethod
    def tensor(cls, left: np.ndarray, right: np.ndarray) -> "Register":
        """The product of two one-wire states, left factor first."""
        a = np.asarray(left, dtype=np.complex128)
        b = np.asarray(right, dtype=np.complex128)
        if a.shape != (2,) or b.shape != (2,):
            raise RegisterError(f"tensor expects two 2-amplitude states, got {a.shape} and {b.shape}")
        return cls(np.kron(a, b))

    # -- properties ------------------------------------------------------
    @property
    def amplitudes(self) -> np.ndarray:
        return self._amplitudes.copy()

    @property
    def norm(self) -> float:
        return float(np.sum(np.abs(self._amplitudes) ** 2))

    def probabilities(self) -> np.ndarray:
        return np.abs(self._amplitudes) ** 2

    def labels(self) -> List[str]:
        return list(self._labels)

    def bitstring(self, index: int) -> str:
        """The label of one index, with a bounds check."""
        if not 0 <= index < 4:
            raise RegisterError(f"a two-wire register has indices 0..3, got {index}")
        return self._labels[index]

    # -- operations ------------------------------------------------------
    def apply(self, gate: np.ndarray, wire: int) -> "Register":
        return Register(apply_one(self._amplitudes, gate, wire))

    def probabilities_by_label(self) -> Dict[str, float]:
        return {label: float(p) for label, p in zip(self._labels, self.probabilities())}

    def sample(self, shots: int, seed: Optional[int] = None) -> Dict[str, int]:
        if shots <= 0:
            raise ValueError(f"shots must be positive, got {shots}")
        rng = np.random.default_rng(seed)
        cumulative = np.cumsum(self.probabilities())
        counts = {label: 0 for label in self._labels}
        for _ in range(shots):
            index = int(np.searchsorted(cumulative, rng.random(), side="right"))
            index = min(index, 3)
            counts[self._labels[index]] += 1
        return counts

    # -- structure -------------------------------------------------------
    def factors(self, tol: float = 1e-12) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Return (left, right) if the state is a product, else None.

        A product state satisfies a_ij = l_i * r_j for every pair, so the matrix
        of amplitudes has rank one. The check is the 2x2 determinant, which is
        exact for the states this book builds.
        """
        m = self._amplitudes.reshape(2, 2)
        determinant = m[0, 0] * m[1, 1] - m[0, 1] * m[1, 0]
        if abs(determinant) > tol:
            return None
        # Recover the factors from the largest row or column.
        if abs(m[0, 0]) >= abs(m[1, 0]) and abs(m[0, 0]) > tol:
            left = m[:, 0] / m[0, 0]
            right = m[0, :]
        elif abs(m[1, 0]) > tol:
            left = m[:, 0] / m[1, 0]
            right = m[1, :]
        elif abs(m[0, 1]) > tol:
            left = m[:, 1] / m[0, 1]
            right = m[0, :]
        else:
            return None
        left_norm = np.linalg.norm(left)
        right_norm = np.linalg.norm(right)
        return left / left_norm, right / right_norm

    def __len__(self) -> int:
        return 4

    def __repr__(self) -> str:
        return "Register(" + ", ".join(f"{a:+.4f}" for a in self._amplitudes) + ")"
