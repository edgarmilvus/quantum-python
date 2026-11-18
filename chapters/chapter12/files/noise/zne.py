"""Zero-noise extrapolation: fold a circuit, measure at three scales, extrapolate.

Folding replaces a circuit U by U (U-dagger U)^k, which triples and quintuples
the gate count without changing the ideal answer. If the noise grows linearly
with the gate count, the measured value at scale 0 is the noiseless one.

Two things the chapter insists on: the extrapolation carries a weight vector,
so its error bar is computable, and it is only licensed where the noise model is
scale-invariant. A readout error is not: it is the same at every scale, so it
survives the extrapolation as a constant offset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np

Op = Tuple[str, Tuple[int, ...], Optional[float]]


def inverse_op(op: Op) -> Op:
    """The inverse of one operation, for the fold."""
    gate, wires, theta = op
    if gate in ("h", "x", "y", "z", "cx", "cnot", "cz"):
        return (gate, tuple(wires), None)
    if gate in ("rx", "ry", "rz"):
        if theta is None:
            raise ValueError(f"{gate} needs an angle to invert")
        return (gate, tuple(wires), -theta)
    raise ValueError(f"no inverse for {gate!r}; folding needs a gate with one")


def fold(ops: Sequence[Op], scale: int) -> List[Op]:
    """U, U U-dagger U, U (U-dagger U)^2, ... for scale 1, 3, 5."""
    if scale < 1 or scale % 2 == 0:
        raise ValueError(f"a fold scale is odd and at least 1, got {scale}")
    base = [tuple((gate, tuple(wires), theta)) for gate, wires, theta in ops]
    out = list(base)
    for _ in range((scale - 1) // 2):
        out = out + [inverse_op(op) for op in reversed(base)] + base
    return out


@dataclass(frozen=True)
class Point:
    """One measured value at one noise scale, with its standard error."""

    scale: int
    value: float
    sigma: float = 0.0

    def __post_init__(self) -> None:
        if self.scale < 1:
            raise ValueError(f"a scale is at least 1, got {self.scale}")
        if not np.isfinite(self.value):
            raise ValueError(f"a value is finite, got {self.value}")


@dataclass(frozen=True)
class Fit:
    """An extrapolated value at scale 0, its error, and the weights that made it."""

    value: float
    sigma: float
    weights: Tuple[float, ...]
    method: str

    def report(self) -> str:
        return f"{self.method}: {self.value:.4f} +/- {self.sigma:.4f}"


def _design(xs: Sequence[float]) -> np.ndarray:
    return np.array([[1.0, x] for x in xs])


def linear(points: Sequence[Point]) -> Fit:
    """Least-squares line, evaluated at scale 0."""
    if len(points) < 2:
        raise ValueError(f"a line needs two points, got {len(points)}")
    xs = [point.scale for point in points]
    ys = [point.value for point in points]
    design = _design(xs)
    coefficients, *_ = np.linalg.lstsq(design, np.array(ys), rcond=None)
    weights = np.linalg.lstsq(design, np.eye(len(points)), rcond=None)[0][0]
    # Equal sigma per point: the intercept's variance is sigma^2 sum(w^2).
    sigma = float(np.sqrt(sum(point.sigma ** 2 * weight ** 2 for point, weight in zip(points, weights))))
    return Fit(
        value=float(coefficients[0]),
        sigma=sigma,
        weights=tuple(float(weight) for weight in weights),
        method="linear",
    )


def exponential(points: Sequence[Point]) -> Fit:
    """Fit ln(value) against scale, which is the shape multiplicative noise has."""
    if len(points) < 2:
        raise ValueError(f"an exponential needs two points, got {len(points)}")
    for point in points:
        if point.value <= 0:
            raise ValueError(f"a log needs a positive value, got {point.value} at scale {point.scale}")
    xs = [point.scale for point in points]
    ys = [float(np.log(point.value)) for point in points]
    design = _design(xs)
    coefficients, *_ = np.linalg.lstsq(design, np.array(ys), rcond=None)
    weights = np.linalg.lstsq(design, np.eye(len(points)), rcond=None)[0][0]
    sigma_log = float(
        np.sqrt(sum((point.sigma / point.value) ** 2 * weight ** 2 for point, weight in zip(points, weights)))
    )
    value = float(np.exp(coefficients[0]))
    return Fit(
        value=value,
        sigma=abs(value * sigma_log),
        weights=tuple(float(weight) for weight in weights),
        method="exponential",
    )


def budget(points: Sequence[Point], shots: int) -> dict:
    """What the extrapolation costs in shots, and what it buys in scale."""
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    total = sum(shots for _ in points)
    return {
        "points": len(points),
        "shots": total,
        "max scale": max(point.scale for point in points),
        "relative cost": total / shots,
    }
