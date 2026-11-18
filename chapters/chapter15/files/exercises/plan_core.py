"""Exercise 5, file 1 of 3: the pure part.

Two kernel matrices, two label lists and a penalty in; a report out. No circuit, no
file, no print: the core cannot tell whether the matrices came from a statevector
or from ibm_fez.
"""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

from qml import classifier


def summarise(
    k_train: np.ndarray,
    train_labels: Sequence[int],
    k_cross: np.ndarray,
    test_labels: Sequence[int],
    lam: float = 0.1,
) -> Dict[str, float]:
    """Fit on one kernel, score on the other, and report what the fit saw."""
    if k_train.shape[0] != k_train.shape[1]:
        raise ValueError(f"a training kernel is square, got {k_train.shape}")
    if k_train.shape[0] != len(train_labels):
        raise ValueError(f"{k_train.shape[0]} rows for {len(train_labels)} labels")
    if k_cross.shape[0] != k_train.shape[0]:
        raise ValueError(f"{k_cross.shape[0]} cross rows for {k_train.shape[0]} training points")
    if k_cross.shape[1] != len(test_labels):
        raise ValueError(f"{k_cross.shape[1]} cross columns for {len(test_labels)} test labels")
    if lam <= 0:
        raise ValueError(f"a penalty is positive, got {lam}")

    model = classifier.fit(k_train, train_labels, [(0.0, 0.0)] * len(train_labels), lam)
    train_accuracy = classifier.accuracy(model.decision(k_train), train_labels)
    test_accuracy = classifier.accuracy(model.decision(k_cross), test_labels)
    off_diagonal = float(k_train[~np.eye(len(train_labels), dtype=bool)].mean())
    return {
        "train accuracy": train_accuracy,
        "test accuracy": test_accuracy,
        "off diagonal": off_diagonal,
        "condition": float(np.linalg.cond(k_train)),
        "penalty": lam,
    }


def verdict(summary: Dict[str, float], baseline: float = 0.667) -> str:
    """Whether the kernel beat the classical number, and by how much."""
    gap = summary["test accuracy"] - baseline
    if gap > 0.15:
        return "well above the baseline"
    if gap > 0:
        return "above the baseline"
    if gap > -0.1:
        return "level with the baseline"
    return "below the baseline"
