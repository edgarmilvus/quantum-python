"""Turn a measurement into a rate, and a rate into a prediction.

Two moves, and the chapter is built on the difference between them. The first is
a fit: one observed shortfall divided by the number of gates that caused it. The
second is a prediction: that rate raised to the number of gates in a circuit that
was never used to fit it.

A fit cannot fail. A prediction can, and chapter 12's argument is that the
prediction is where the model earns or loses its keep.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import numpy as np

from .device import sigma_binomial


def uniform_rate(measured: float, ideal: float = 1.0, gates: int = 1) -> float:
    """One error rate that explains a measured shortfall over `gates` gates."""
    if gates < 1:
        raise ValueError(f"gates must be at least 1, got {gates}")
    if not 0 < measured <= ideal:
        raise ValueError(f"measured={measured} is not in (0, {ideal}]")
    return 1 - (measured / ideal) ** (1 / gates)


def predict(rate: float, gates: int) -> float:
    """The survival of `gates` gates, each losing `rate`."""
    if not 0 <= rate < 1:
        raise ValueError(f"a rate is in [0, 1), got {rate}")
    if gates < 0:
        raise ValueError(f"gates must be non-negative, got {gates}")
    return (1 - rate) ** gates


def peak(ideal: float, survival: float) -> float:
    """The probability a circuit still reports its intended outcome."""
    if not 0 <= survival <= 1:
        raise ValueError(f"a survival is in [0, 1], got {survival}")
    return ideal * survival


@dataclass(frozen=True)
class Test:
    """A prediction, the measurement it is tested against, and the distance."""

    name: str
    predicted: float
    measured: float
    sigma: float

    @property
    def gap(self) -> float:
        return self.predicted - self.measured

    @property
    def z(self) -> float:
        return self.gap / self.sigma if self.sigma > 0 else float("inf")

    @property
    def verdict(self) -> str:
        if abs(self.z) < 2:
            return "consistent"
        if abs(self.z) < 3:
            return "marginal"
        return "falsified"

    def report(self) -> str:
        return (
            f"{self.name:12s} predicted {self.predicted:.4f}  measured {self.measured:.4f}  "
            f"gap {self.gap:+.4f}  z {self.z:+.1f}  {self.verdict}"
        )


def test(name: str, predicted: float, measured: float, shots: int) -> Test:
    """Compare a prediction with a frequency, using the binomial error."""
    return Test(name=name, predicted=predicted, measured=measured,
                sigma=sigma_binomial(measured, shots))


def fit_rate_from_two(shortfalls: Sequence[float], gates: Sequence[int]) -> float:
    """A rate that minimizes the squared log-error of two measurements.

    With `shortfalls` as survival fractions and `gates` as the count of lossy
    gates in each, the least-squares solution is closed form for one parameter.
    """
    if len(shortfalls) != len(gates) or not shortfalls:
        raise ValueError("a shortfall and a gate count for each measurement")
    logs = np.array([np.log(value) for value in shortfalls])
    counts = np.array(gates, dtype=float)
    rate = 1 - float(np.exp((counts @ logs) / (counts @ counts)))
    return rate


def residuals(points: Sequence[Test]) -> float:
    """The largest |z| in a set of tests, which is the model's worst miss."""
    if not points:
        raise ValueError("no tests to summarise")
    return max(abs(point.z) for point in points)


def table(tests: Sequence[Test]) -> str:
    lines = [f"{'test':12s}{'predicted':>10s}{'measured':>10s}{'gap':>9s}{'z':>7s}   verdict"]
    for point in tests:
        lines.append(
            f"{point.name:12s}{point.predicted:10.4f}{point.measured:10.4f}"
            f"{point.gap:+9.4f}{point.z:+7.1f}   {point.verdict}"
        )
    return "\n".join(lines)
