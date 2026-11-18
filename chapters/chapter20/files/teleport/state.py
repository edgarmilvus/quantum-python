"""The state to teleport, and the fidelity that says it arrived.

A single qubit prepared with two angles has a Bloch vector, and the book's verification
compares the vector measured on the receiving qubit with the vector the sender prepared.
The fidelity of two single-qubit states is a dot product, which is why this chapter can
state its result as one number with an error bar.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Prepared:
    """|psi> = cos(theta/2)|0> + e^{i phi} sin(theta/2)|1>."""

    theta: float
    phi: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.theta <= math.pi:
            raise ValueError(f"theta is in [0, pi], got {self.theta}")
        if not 0.0 <= self.phi < 2 * math.pi:
            raise ValueError(f"phi is in [0, 2pi), got {self.phi}")

    def bloch(self) -> Tuple[float, float, float]:
        return (
            math.sin(self.theta) * math.cos(self.phi),
            math.sin(self.theta) * math.sin(self.phi),
            math.cos(self.theta),
        )

    def report(self) -> str:
        x, y, z = self.bloch()
        return f"theta {self.theta:.4f}, phi {self.phi:.4f} -> bloch ({x:.4f}, {y:.4f}, {z:.4f})"


def fidelity(prepared: Prepared, measured: Tuple[float, float, float]) -> float:
    """F = (1 + r . r_ideal) / 2, for a measured Bloch vector r."""
    x, y, z = prepared.bloch()
    mx, my, mz = measured
    return (1.0 + x * mx + y * my + z * mz) / 2.0


def distance(prepared: Prepared, measured: Tuple[float, float, float]) -> float:
    """The Euclidean distance between the ideal and the measured Bloch vector."""
    x, y, z = prepared.bloch()
    mx, my, mz = measured
    return math.sqrt((x - mx) ** 2 + (y - my) ** 2 + (z - mz) ** 2)
