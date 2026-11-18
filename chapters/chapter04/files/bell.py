"""A Bell pair, a measurement at an angle, and the CHSH combination.

Everything here is arithmetic on four probabilities. The physics is that a device
refuses to keep the classical bound, and that is measured, not asserted.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

import numpy as np

# The four settings, in degrees, in the x-z plane of each qubit.
# a = 0, a' = 90, b = 45, b' = 135 gives the maximal violation for |Phi+>,
# because then three cosines are +0.7071 and one is -0.7071 in the S combination.
SETTINGS = {
    "ab": (0.0, 45.0),
    "ab_prime": (0.0, 135.0),
    "a_prime_b": (90.0, 45.0),
    "a_prime_b_prime": (90.0, 135.0),
}

CLASSICAL_BOUND = 2.0
TSIRELSON_BOUND = 2.0 * math.sqrt(2.0)


H = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
I2 = np.eye(2, dtype=np.complex128)
CX = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=np.complex128
)


def ry(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -s], [s, c]], dtype=np.complex128)


def bell_state() -> np.ndarray:
    """|Phi+> = (|00> + |11>) / sqrt(2), as four amplitudes."""
    return CX @ np.kron(H, I2) @ np.array([1.0, 0, 0, 0], dtype=np.complex128)


def measurement_rotation(angle_deg: float) -> float:
    """The Ry angle that turns a measurement along `angle_deg` into a Z measurement.

    Ry(-theta) maps the axis at theta onto z, so applying Ry(theta) after the state
    and then measuring Z measures the axis at -theta. The chapter fixes the sign by
    checking that E(a, b) = cos(a - b) on a Bell pair.
    """
    return math.radians(-angle_deg)


def rotated_state(angle_a: float, angle_b: float) -> np.ndarray:
    """The Bell pair after both rotations, before measurement."""
    rotation = np.kron(ry(measurement_rotation(angle_a)), ry(measurement_rotation(angle_b)))
    return rotation @ bell_state()


def probabilities(angle_a: float, angle_b: float) -> np.ndarray:
    """The measurement distribution at two settings."""
    return np.abs(rotated_state(angle_a, angle_b)) ** 2


def expectation_from_probabilities(p: Sequence[float]) -> float:
    """E = P(same) - P(different) over the four outcomes, index = b0 * 2 + b1."""
    values = np.asarray(list(p), dtype=float)
    if values.shape != (4,):
        raise ValueError(f"a two-qubit distribution has 4 entries, got {values.shape}")
    if abs(values.sum() - 1.0) > 1e-9:
        raise ValueError(f"the distribution sums to {values.sum():.9f}, not 1")
    same = values[0] + values[3]
    different = values[1] + values[2]
    return float(same - different)


def expectation_from_counts(counts: Dict[str, int]) -> float:
    """The same number from a histogram whose keys are two-bit strings."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an expectation needs at least one shot")
    same = counts.get("00", 0) + counts.get("11", 0)
    different = counts.get("01", 0) + counts.get("10", 0)
    return (same - different) / total


def chsh(expectations: Dict[str, float]) -> float:
    """S = E(a,b) - E(a,b') + E(a',b) + E(a',b')."""
    missing = set(SETTINGS) - set(expectations)
    if missing:
        raise ValueError(f"missing settings: {sorted(missing)}")
    return (
        expectations["ab"]
        - expectations["ab_prime"]
        + expectations["a_prime_b"]
        + expectations["a_prime_b_prime"]
    )


def simulate() -> Dict[str, float]:
    """The four expectations on an ideal Bell pair."""
    out = {}
    for name, (angle_a, angle_b) in SETTINGS.items():
        out[name] = expectation_from_probabilities(probabilities(angle_a, angle_b))
    return out


def predicted_expectation(angle_a: float, angle_b: float) -> float:
    """What a perfect Bell pair predicts: cos of the difference, in radians."""
    return math.cos(math.radians(angle_a - angle_b))


def standard_error(expectation: float, shots: int) -> float:
    """The shot-noise error of one expectation, from its own magnitude."""
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    if not -1.0 <= expectation <= 1.0:
        raise ValueError(f"an expectation is in [-1, 1], got {expectation}")
    return math.sqrt(max(0.0, 1.0 - expectation**2) / shots)


def chsh_error(expectations: Dict[str, float], shots: int) -> float:
    """Quadrature sum of the four single-setting errors."""
    return math.sqrt(sum(standard_error(value, shots) ** 2 for value in expectations.values()))


def violation_sigma(expectations: Dict[str, float], shots: int) -> float:
    """How many standard errors S sits above the classical bound."""
    margin = chsh(expectations) - CLASSICAL_BOUND
    error = chsh_error(expectations, shots)
    if error == 0:
        raise ValueError("zero error: cannot express a margin in sigmas")
    return margin / error
