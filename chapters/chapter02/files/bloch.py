"""The Bloch vector as three numbers you can measure.

For one qubit, <X>, <Y> and <Z> are the coordinates of a point inside a sphere of
radius one. This module computes them from a state, and estimates them from
counts, which is the only thing a device will give you.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np

from gates import H, S, X, Y, Z, apply_one

PAULI = {"x": X, "y": Y, "z": Z}


def _as_one_qubit(state: np.ndarray) -> np.ndarray:
    vector = np.asarray(state, dtype=np.complex128)
    if vector.shape != (2,):
        raise ValueError(f"a Bloch vector is defined for one qubit, got {vector.shape}")
    return vector


def expectation(state: np.ndarray, axis: str) -> float:
    """<psi|P|psi> for P in {X, Y, Z}."""
    if axis not in PAULI:
        raise ValueError(f"axis must be one of x, y, z, got {axis!r}")
    vector = _as_one_qubit(state)
    value = np.vdot(vector, PAULI[axis] @ vector)
    if abs(value.imag) > 1e-9:
        raise ValueError(f"an expectation of a Hermitian operator must be real, got {value}")
    return float(value.real)


def bloch_vector(state: np.ndarray) -> np.ndarray:
    vector = _as_one_qubit(state)
    return np.array([expectation(vector, "x"), expectation(vector, "y"), expectation(vector, "z")])


def purity(state: np.ndarray) -> float:
    """The length of the Bloch vector: 1 for a pure state, 0 at the centre."""
    return float(np.linalg.norm(bloch_vector(state)))


def angle_deg(state: np.ndarray) -> float:
    """The azimuth of the Bloch vector, in degrees, measured from +x toward +y."""
    x, y, _ = bloch_vector(state)
    if abs(x) < 1e-12 and abs(y) < 1e-12:
        raise ValueError("the vector has no azimuth: x and y are both zero")
    return math.degrees(math.atan2(y, x))


def ry_angle_deg(state: np.ndarray) -> float:
    """The polar angle of a state built by Ry(theta) on |0>, in degrees.

    Ry rotates in the x-z plane, so the angle is atan2(x, z), doubled: theta is
    the rotation, and the Bloch vector moves by theta, not by 2*theta.
    """
    x, _, z = bloch_vector(state)
    return math.degrees(math.atan2(x, z))


def measurement_basis(axis: str) -> np.ndarray:
    """The gate to apply before a Z measurement, to measure `axis` instead."""
    if axis == "z":
        return np.eye(2, dtype=np.complex128)
    if axis == "x":
        return H
    if axis == "y":
        # S-dagger then H maps Y onto Z.
        return H @ np.array([[1, 0], [0, -1j]], dtype=np.complex128)
    raise ValueError(f"axis must be one of x, y, z, got {axis!r}")


def estimate_from_counts(counts: Dict[str, int], axis: str) -> float:
    """The expectation of `axis` from counts taken after the basis rotation."""
    if axis not in PAULI:
        raise ValueError(f"axis must be one of x, y, z, got {axis!r}")
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("no shots: an expectation needs counts")
    return (counts.get("0", 0) - counts.get("1", 0)) / total


def estimate_vector(counts_by_axis: Dict[str, Dict[str, int]]) -> np.ndarray:
    """A Bloch vector from three measured axes."""
    missing = {"x", "y", "z"} - set(counts_by_axis)
    if missing:
        raise ValueError(f"missing axes: {sorted(missing)}")
    return np.array([estimate_from_counts(counts_by_axis[axis], axis) for axis in ("x", "y", "z")])


def angle_error_deg(estimated: np.ndarray, truth: np.ndarray) -> float:
    """The angle between two Bloch vectors, in degrees."""
    a = np.asarray(estimated, dtype=float)
    b = np.asarray(truth, dtype=float)
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        raise ValueError("an angle needs two non-zero vectors")
    cosine = float(np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0))
    return math.degrees(math.acos(cosine))
