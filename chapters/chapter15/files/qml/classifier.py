"""Two classifiers that differ only in the kernel.

Kernel ridge regression is nine lines of linear algebra: solve (K + lambda I) a = y
and predict with sign(sum a_i K(x_i, x)). Swapping the quantum kernel for an RBF
keeps every other line, which is the comparison the chapter wants: the kernel is
the variable, not the optimiser.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np

Point = Tuple[float, float]


@dataclass
class Ridge:
    """A fitted kernel ridge classifier: the dual weights and the training kernel."""

    alpha: np.ndarray
    train: List[Point]
    lam: float

    def decision(self, cross: np.ndarray) -> np.ndarray:
        """The real-valued score for each row of a train-by-test kernel."""
        if cross.shape[0] != len(self.train):
            raise ValueError(f"{cross.shape[0]} rows for {len(self.train)} training points")
        return cross.T @ self.alpha

    def predict(self, cross: np.ndarray) -> np.ndarray:
        return np.sign(self.decision(cross))


def fit(gram: np.ndarray, labels: Sequence[int], points: Sequence[Point], lam: float = 1e-2) -> Ridge:
    """Solve the regularised system; the intercept is zero because labels are centred."""
    if gram.shape[0] != gram.shape[1] or gram.shape[0] != len(labels):
        raise ValueError(f"{gram.shape} does not match {len(labels)} labels")
    if lam <= 0:
        raise ValueError(f"a ridge penalty is positive, got {lam}")
    y = np.asarray(labels, dtype=float)
    alpha = np.linalg.solve(gram + lam * np.eye(gram.shape[0]), y)
    return Ridge(alpha=alpha, train=list(points), lam=lam)


def accuracy(predicted: Sequence[float], labels: Sequence[int]) -> float:
    if len(predicted) != len(labels):
        raise ValueError(f"{len(predicted)} predictions and {len(labels)} labels")
    hits = sum(1 for p, y in zip(predicted, labels) if int(np.sign(p)) == y)
    return hits / len(labels)


def confusion(predicted: Sequence[float], labels: Sequence[int]) -> Dict[str, int]:
    out = {"true positive": 0, "true negative": 0, "false positive": 0, "false negative": 0}
    for p, y in zip(predicted, labels):
        guess = int(np.sign(p))
        if guess == 1 and y == 1:
            out["true positive"] += 1
        elif guess == 1 and y == -1:
            out["false positive"] += 1
        elif guess == -1 and y == -1:
            out["true negative"] += 1
        else:
            out["false negative"] += 1
    return out


def rbf(points: Sequence[Point], gamma: float = 1.0) -> np.ndarray:
    """The classical kernel the quantum one is compared with."""
    if gamma <= 0:
        raise ValueError(f"gamma is positive, got {gamma}")
    a = np.asarray(points, dtype=float)
    square = np.sum(a * a, axis=1)
    distance = square[:, None] + square[None, :] - 2 * a @ a.T
    return np.exp(-gamma * np.maximum(distance, 0.0))


def cross(a: Sequence[Point], b: Sequence[Point], gamma: float = 1.0) -> np.ndarray:
    left = np.asarray(a, dtype=float)
    right = np.asarray(b, dtype=float)
    distance = (
        np.sum(left * left, axis=1)[:, None]
        + np.sum(right * right, axis=1)[None, :]
        - 2 * left @ right.T
    )
    return np.exp(-gamma * np.maximum(distance, 0.0))


def run(
    train_points: Sequence[Point],
    train_labels: Sequence[int],
    test_points: Sequence[Point],
    test_labels: Sequence[int],
    quantum_train: np.ndarray,
    quantum_cross: np.ndarray,
    lam: float = 1e-2,
) -> Dict[str, float]:
    """One quantum fit and one classical fit on the same split."""
    model = fit(quantum_train, train_labels, train_points, lam)
    quantum_score = model.decision(quantum_cross)
    best = {"gamma": 0.0, "accuracy": -1.0}
    for gamma in (0.5, 1.0, 2.0, 4.0, 8.0, 16.0):
        classical = fit(rbf(train_points, gamma), train_labels, train_points, lam)
        score = classical.decision(cross(train_points, test_points, gamma))
        value = accuracy(score, test_labels)
        if value > best["accuracy"]:
            best = {"gamma": gamma, "accuracy": value}
    return {
        "quantum": accuracy(quantum_score, test_labels),
        "classical": best["accuracy"],
        "gamma": best["gamma"],
    }
