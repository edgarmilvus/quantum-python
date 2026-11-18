"""Phase estimation: reading an eigenvalue into a register of bits.

The unitary has an eigenstate |1> with eigenvalue e^{2 pi i phi}. The circuit writes
phi into the phases of n ancillas and then transforms them with the inverse QFT, so the
measurement returns the binary expansion of phi to n bits.
"""

from __future__ import annotations

import cmath
import math
from typing import Dict, List, Tuple

import numpy as np

from qft import dft, embed_one, I2, controlled_phase

H2 = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)


def unitary(phi: float) -> np.ndarray:
    """The one-qubit unitary whose |1> eigenphase is phi."""
    if not 0.0 <= phi < 1.0:
        raise ValueError(f"a phase is in [0, 1), got {phi}")
    return np.diag([1.0, cmath.exp(2j * math.pi * phi)]).astype(np.complex128)


def controlled_power(phi: float, power: int, control: int, target: int, total: int) -> np.ndarray:
    """Controlled U^{2^power}: a phase on |1,1> of e^{2 pi i phi 2^power}."""
    if power < 0:
        raise ValueError(f"a power is non-negative, got {power}")
    angle = 2 * math.pi * phi * (2 ** power)
    return controlled_phase(angle % (2 * math.pi), control=control, target=target, n=total)


def prepare(n: int) -> np.ndarray:
    """Ancillas in |0..0>, target in |1>."""
    size = 1 << (n + 1)
    state = np.zeros(size, dtype=np.complex128)
    # Ancillas at zero, target at one: the index is 1 with the target as the last bit.
    state[1] = 1.0
    return state


def pea_state(phi: float, n: int) -> np.ndarray:
    """The state before measurement: ancillas transformed, target unchanged."""
    total = n + 1
    state = prepare(n)
    hadamards = np.eye(1, dtype=np.complex128)
    for wire in range(n):
        state = embed_one(H2, wire, total) @ state
    # Wire 0 is the most significant bit of the register, so it carries the largest
    # power of U: the bit ordering of the circuit and of the measured integer agree.
    for wire in range(n):
        power = n - 1 - wire
        state = controlled_power(phi, power=power, control=wire, target=n, total=total) @ state

    # Inverse QFT on the ancillas only: build it on n wires and embed it.
    inverse = dft(n, sign=-1)
    embedded = np.kron(inverse, I2)
    return embedded @ state


def distribution(phi: float, n: int) -> Dict[int, float]:
    """Probability of each measured k, with the target traced out."""
    state = pea_state(phi, n)
    probabilities = np.abs(state) ** 2
    out = {}
    for k in range(1 << n):
        out[k] = float(probabilities[2 * k] + probabilities[2 * k + 1])
    return out


def estimate(phi: float, n: int) -> Tuple[int, float]:
    """The most likely k and its probability."""
    values = distribution(phi, n)
    k = max(values, key=values.get)
    return k, values[k]


def phase_of(k: int, n: int) -> float:
    """The phase a measured k corresponds to."""
    if not 0 <= k < (1 << n):
        raise ValueError(f"k must be in [0, {1 << n}), got {k}")
    return k / (1 << n)


def success_probability(phi: float, n: int) -> float:
    """The probability that the measurement returns the nearest n-bit approximation."""
    k, probability = estimate(phi, n)
    return probability


def precision(n: int) -> float:
    """The spacing between representable phases."""
    return 1.0 / (1 << n)
