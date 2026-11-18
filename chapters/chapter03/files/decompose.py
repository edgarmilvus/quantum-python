"""Any one-qubit gate is three rotations, and the decomposition is testable.

The ZYZ form writes a unitary as Rz(alpha) Ry(theta) Rz(beta), times a global
phase that no measurement can see. The compiler uses it to replace an arbitrary
gate with gates the backend actually implements.
"""

from __future__ import annotations

import math
from typing import Tuple

import numpy as np

from circuit import rotation


def _check_unitary(matrix: np.ndarray, tol: float = 1e-9) -> np.ndarray:
    u = np.asarray(matrix, dtype=np.complex128)
    if u.shape != (2, 2):
        raise ValueError(f"a one-qubit gate is 2x2, got {u.shape}")
    if np.max(np.abs(u.conj().T @ u - np.eye(2))) > tol:
        raise ValueError("the matrix is not unitary; ZYZ does not apply")
    return u


def zyz(matrix: np.ndarray) -> Tuple[float, float, float, float]:
    """Return (alpha, theta, beta, phase) with U = e^{i phase} Rz(a) Ry(t) Rz(b)."""
    u = _check_unitary(matrix)
    determinant = np.linalg.det(u)
    phase = float(np.angle(determinant) / 2.0)
    v = u * np.exp(-1j * phase)  # now in SU(2), determinant 1
    # atan2 of the two magnitudes, not acos of one: acos is ill-conditioned near
    # theta = 0 and turns an exact zero into 3e-8, which then fails a 1e-12 test.
    theta = 2.0 * math.atan2(abs(v[1, 0]), abs(v[0, 0]))
    if theta == 0.0:
        alpha = -2.0 * float(np.angle(v[0, 0]))
        beta = 0.0
        return alpha, 0.0, beta, phase
    total = -2.0 * float(np.angle(v[0, 0]))   # alpha + beta
    difference = 2.0 * float(np.angle(v[1, 0]))  # alpha - beta
    alpha = (total + difference) / 2.0
    beta = (total - difference) / 2.0
    return alpha, theta, beta, phase


def rebuild(alpha: float, theta: float, beta: float, phase: float = 0.0) -> np.ndarray:
    return np.exp(1j * phase) * rotation("z", alpha) @ rotation("y", theta) @ rotation("z", beta)


def distance_up_to_phase(a: np.ndarray, b: np.ndarray) -> float:
    """The largest entrywise difference after removing the best global phase."""
    left = np.asarray(a, dtype=np.complex128)
    right = np.asarray(b, dtype=np.complex128)
    overlap = np.vdot(right, left)
    if abs(overlap) < 1e-15:
        return float(np.max(np.abs(left - right)))
    phase = overlap / abs(overlap)
    return float(np.max(np.abs(left - phase * right)))
