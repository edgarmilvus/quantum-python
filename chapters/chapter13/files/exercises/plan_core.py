"""Exercise 5, file 1 of 3: the pure part.

A graph and a set of angles in, a verdict out. No optimiser, no file, no print.
The core does not know whether the angles came from a simplex, from a device or
from a textbook, which is what lets it be tested on a fixed pair.
"""

from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

from qaoa import graph as g, qaoa, state as st


def summarise(graph: g.Graph, betas: Sequence[float], gammas: Sequence[float], optimum: float) -> Dict[str, float]:
    """The four numbers a QAOA run owes: mean, ratio, best assignment, its share."""
    if len(betas) != len(gammas) or not betas:
        raise ValueError(f"one beta and one gamma per layer, got {len(betas)} and {len(gammas)}")
    if optimum <= 0:
        raise ValueError(f"an optimum is positive, got {optimum}")
    vector = qaoa.state_for(graph, betas, gammas)
    probabilities = st.probabilities(vector)
    best_bits = int(np.argmax(probabilities))
    mean = qaoa.expected_cut(graph, vector)
    return {
        "mean": mean,
        "optimum": optimum,
        "ratio": qaoa.approximation_ratio(mean, optimum),
        "best": float(best_bits),
        "best probability": float(probabilities[best_bits]),
        "best cut": float(graph.cut(best_bits)),
        "uniform": float(graph.uniform_mean()),
        "layers": float(len(betas)),
    }


def verdict(summary: Dict[str, float]) -> str:
    """A word for whether the state beats guessing and how close it gets."""
    if summary["mean"] <= summary["uniform"]:
        return "no better than guessing"
    gap = summary["optimum"] - summary["mean"]
    if gap <= 0.01 * summary["optimum"]:
        return "at the optimum"
    if summary["ratio"] >= 0.95:
        return "close to the optimum"
    return "above guessing"


def share_of_optimum(graph: g.Graph, betas: Sequence[float], gammas: Sequence[float]) -> float:
    """How much probability lands on an assignment that reaches the maximum cut."""
    optimum, _ = graph.max_cut()
    vector = qaoa.state_for(graph, betas, gammas)
    probabilities = st.probabilities(vector)
    return float(sum(p for bits, p in enumerate(probabilities) if graph.cut(bits) == optimum))
