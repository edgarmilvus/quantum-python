"""Exercise 1 (repair): a cost function with the sign flipped.

Run: python3 chapters/chapter13/files/exercises/ex1_sign.py

MaxCut counts the edges that cross the split, so the cost is (1 - ZZ)/2 per edge.
Writing (1 + ZZ)/2 counts the edges that stay inside a side, which is the
complement: on five edges the buggy value is 5 minus the cut. The optimiser then
does its job perfectly and maximizes the wrong quantity, and the report shows an
approximation ratio above one, which is impossible.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable

import numpy as np

from qaoa import graph as g, qaoa, state as st


def cost_wrong(graph: g.Graph, vector: st.State) -> float:
    """The defect: (1 + <ZZ>)/2, which counts the edges that do not cross."""
    total = 0.0
    for i, j, weight in graph.edges:
        total += weight * (1 + qaoa.zz(vector, i, j)) / 2
    return float(total)


def best_angles(graph: g.Graph, cost: Callable[[g.Graph, st.State], float], steps: int = 24):
    """A grid search over the one-layer angles for any cost function."""
    best = (-np.inf, 0.0, 0.0)
    for beta in np.linspace(0.0, np.pi / 2, steps):
        for gamma in np.linspace(0.0, np.pi, steps):
            value = cost(graph, qaoa.state_for(graph, [beta], [gamma]))
            if value > best[0]:
                best = (value, float(beta), float(gamma))
    return best


def checks(check: Callable[[bool, str], None]) -> None:
    instance = g.square_with_diagonal()
    optimum, _ = instance.max_cut()
    vector = qaoa.state_for(instance, [0.3109], [0.5713])

    honest = qaoa.expected_cut(instance, vector)
    buggy = cost_wrong(instance, vector)
    check(abs(honest - 3.2371) < 1e-3, "the honest cost at the optimal angles is 3.2371")
    check(abs(buggy - (instance.m - honest)) < 1e-9, "the buggy cost is the edge count minus the cut")
    check(abs(buggy - 1.7629) < 1e-3, "which is 1.7629 at those angles")
    check(buggy < honest, "so the optimum of the honest function is a bad point for the buggy one")

    value, beta, gamma = best_angles(instance, cost_wrong)
    check(abs(beta - 0.3109) > 0.3 or abs(gamma - 0.5713) > 0.3,
          "the optimiser moves to a different pair of angles")
    honest_there = qaoa.expected_cut(instance, qaoa.state_for(instance, [beta], [gamma]))
    check(honest_there < honest, "and the honest cut there is worse than at the honest optimum")
    check(honest_there < instance.uniform_mean() + 0.5, "close to what guessing achieves")

    ratio = value / optimum
    check(ratio > 1.0, "the reported ratio exceeds one, which no cut can")
    check(value > optimum, "because the buggy value counts the edges that stay inside")

    check(abs(cost_wrong(instance, st.zero(4)) - instance.m) < 1e-9,
          "with one side empty the buggy cost is every edge, and the honest one is none")

    for bad in (0.0, -1.0):
        try:
            qaoa.approximation_ratio(3.0, bad)
        except ValueError:
            check(True, f"an optimum of {bad} is refused")
        else:
            check(False, f"an optimum of {bad} is refused")

    total = sum(weight for _, _, weight in instance.edges)
    check(abs(total - instance.m) < 1e-9, "the unit weights make the edge count the maximum")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
