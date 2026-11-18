"""A dataset small enough to compute a kernel matrix by hand.

Twelve points in two dimensions, two classes, and a split that fits a screen. The
point of the size is the same as chapter 13's: every number in the chapter is
computed, not sampled, and a reader can check the accuracy by counting the rows.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

Point = Tuple[float, float]


@dataclass(frozen=True)
class Dataset:
    """Points, labels in {-1, +1}, and a name for the table."""

    points: Tuple[Point, ...]
    labels: Tuple[int, ...]
    name: str = ""

    def __post_init__(self) -> None:
        if len(self.points) != len(self.labels):
            raise ValueError(f"{len(self.points)} points and {len(self.labels)} labels")
        if len(self.points) < 4:
            raise ValueError(f"a dataset has at least four points, got {len(self.points)}")
        for point in self.points:
            if len(point) != 2:
                raise ValueError(f"a point is two numbers, got {point}")
        if set(self.labels) - {-1, 1}:
            raise ValueError(f"labels are -1 or +1, got {sorted(set(self.labels))}")

    @property
    def n(self) -> int:
        return len(self.points)

    def split(self, train: Sequence[int], test: Sequence[int]) -> Tuple["Dataset", "Dataset"]:
        if not train or not test:
            raise ValueError("a split needs a train and a test part")
        if len(set(train) & set(test)) > 0:
            raise ValueError("a point cannot be in both parts")
        if max(list(train) + list(test)) >= self.n:
            raise ValueError(f"an index is outside 0..{self.n - 1}")
        return (
            Dataset(tuple(self.points[i] for i in train), tuple(self.labels[i] for i in train), f"{self.name} train"),
            Dataset(tuple(self.points[i] for i in test), tuple(self.labels[i] for i in test), f"{self.name} test"),
        )

    def stratified(self, take: int) -> Tuple["Dataset", "Dataset"]:
        """Take `take` points from each class for training, the rest for testing."""
        if take < 1:
            raise ValueError(f"take must be positive, got {take}")
        positives = [i for i, label in enumerate(self.labels) if label == 1]
        negatives = [i for i, label in enumerate(self.labels) if label == -1]
        if take >= min(len(positives), len(negatives)):
            raise ValueError(f"take={take} leaves no test point in a class")
        train = positives[:take] + negatives[:take]
        test = positives[take:] + negatives[take:]
        return self.split(train, test)

    def split_indices(self, take: int) -> Tuple[List[int], List[int]]:
        """The indices `stratified(take)` would use, so a kernel matrix can be indexed."""
        positives = [i for i, label in enumerate(self.labels) if label == 1]
        negatives = [i for i, label in enumerate(self.labels) if label == -1]
        if take < 1 or take >= min(len(positives), len(negatives)):
            raise ValueError(f"take={take} leaves no test point in a class")
        return positives[:take] + negatives[:take], positives[take:] + negatives[take:]

    def counts(self) -> Tuple[int, int]:
        return self.labels.count(1), self.labels.count(-1)


def xor() -> Dataset:
    """The four corners of a square, labelled by parity: no line separates them."""
    points = ((0.1, 0.1), (0.1, 0.9), (0.9, 0.1), (0.9, 0.9))
    labels = (1, -1, -1, 1)
    return Dataset(points=points, labels=labels, name="xor")


def circles() -> Dataset:
    """Inner and outer ring: a circle separates them, a line does not."""
    inner = [(0.5 + 0.12 * math.cos(2 * math.pi * k / 4), 0.5 + 0.12 * math.sin(2 * math.pi * k / 4)) for k in range(4)]
    outer = [(0.5 + 0.34 * math.cos(2 * math.pi * k / 4 + 0.4), 0.5 + 0.34 * math.sin(2 * math.pi * k / 4 + 0.4)) for k in range(4)]
    points = tuple(inner + outer)
    labels = (1,) * 4 + (-1,) * 4
    return Dataset(points=points, labels=labels, name="circles")


def circles12(per_ring: int = 6) -> Dataset:
    """A ring inside a ring, which a line cannot separate and a circle can."""
    if per_ring < 2:
        raise ValueError(f"a ring needs at least two points, got {per_ring}")
    inner = [
        (0.5 + 0.10 * math.cos(2 * math.pi * k / per_ring), 0.5 + 0.10 * math.sin(2 * math.pi * k / per_ring))
        for k in range(per_ring)
    ]
    outer = [
        (0.5 + 0.32 * math.cos(2 * math.pi * k / per_ring + 0.4), 0.5 + 0.32 * math.sin(2 * math.pi * k / per_ring + 0.4))
        for k in range(per_ring)
    ]
    return Dataset(points=tuple(inner + outer), labels=(1,) * per_ring + (-1,) * per_ring, name="circles")


def spiral(per_class: int = 6, turns: float = 1.5) -> Dataset:
    """Two interleaved arms: a line fails, a circle fails, a sharp kernel wins."""
    if per_class < 3:
        raise ValueError(f"a spiral needs at least three points per class, got {per_class}")
    points = []
    for k in range(per_class):
        angle = turns * 2 * math.pi * k / (per_class - 1)
        radius = 0.08 + 0.30 * k / (per_class - 1)
        points.append((0.5 + radius * math.cos(angle), 0.5 + radius * math.sin(angle)))
        points.append((0.5 - radius * math.cos(angle), 0.5 - radius * math.sin(angle)))
    labels = tuple(1 if i % 2 == 0 else -1 for i in range(len(points)))
    return Dataset(points=tuple(points), labels=labels, name="spiral")


def blobs() -> Dataset:
    """Two clusters a line does separate, which is the control for the kernel."""
    left = ((0.25, 0.3), (0.3, 0.45), (0.2, 0.55), (0.35, 0.25), (0.28, 0.38), (0.22, 0.48))
    right = ((0.75, 0.6), (0.8, 0.7), (0.7, 0.8), (0.78, 0.55), (0.72, 0.68), (0.82, 0.62))
    points = tuple(left + right)
    labels = (1,) * 6 + (-1,) * 6
    return Dataset(points=points, labels=labels, name="blobs")


def as_matrix(dataset: Dataset) -> List[List[float]]:
    return [[x, y] for x, y in dataset.points]


def report(dataset: Dataset) -> str:
    lines = [f"{dataset.name}: {dataset.n} points, {dataset.counts()[0]} positive, {dataset.counts()[1]} negative"]
    for (x, y), label in zip(dataset.points, dataset.labels):
        lines.append(f"  ({x:.3f}, {y:.3f})  {label:+d}")
    return "\n".join(lines)
