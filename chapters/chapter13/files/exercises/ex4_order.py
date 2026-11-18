"""Exercise 4 (break): the mixer before the phase separator.

Run: python3 chapters/chapter13/files/exercises/ex4_order.py

A diagonal gate applied last cannot change a measurement in the computational
basis, so a circuit that ends with the separator returns the state the mixer
produced: a product state, whose expected cut is exactly the uniform mean for
every pair of angles. The defect is loud in one sense (the landscape is flat) and
quiet in another (the number it returns, 2.5, is a perfectly plausible cut).
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, List

import numpy as np

from qaoa import graph as g, qaoa, state as st


def state_mixer_first(graph: g.Graph, beta: float, gamma: float) -> st.State:
    """The defect: H, mixer, then separator, which leaves the separator last."""
    vector = st.zero(graph.n)
    for wire in range(graph.n):
        vector = st.h(vector, wire)
    for wire in range(graph.n):
        vector = st.rx(vector, wire, 2 * beta)
    for i, j, weight in graph.edges:
        vector = st.rzz(vector, i, j, -gamma * weight)
    return vector


def landscape(graph: g.Graph, state: Callable[[g.Graph, float, float], st.State], steps: int = 24) -> List[float]:
    values = []
    for beta in np.linspace(0.0, np.pi / 2, steps):
        for gamma in np.linspace(0.0, np.pi, steps):
            values.append(qaoa.expected_cut(graph, state(graph, beta, gamma)))
    return values


def checks(check: Callable[[bool, str], None]) -> None:
    instance = g.square_with_diagonal()
    broken = landscape(instance, state_mixer_first)
    values = np.array(broken)

    check(len(values) == 576, "the defect is measured on a 24 by 24 grid")
    check(abs(values.max() - 2.5) < 1e-9, "the highest expected cut it reaches is exactly 2.5")
    check(abs(values.min() - 2.5) < 1e-9, "the lowest is 2.5 as well")
    check(float(values.std()) < 1e-9, "so the landscape has no structure at all")
    check(abs(values.mean() - instance.uniform_mean()) < 1e-12, "and it equals the uniform guess")

    ratio = qaoa.approximation_ratio(float(values.max()), 4.0)
    check(abs(ratio - 0.625) < 1e-9, "which is 0.625 of the optimum")
    check(ratio < 0.8093, "below the 0.8093 the correct circuit reaches")

    good = landscape(instance, lambda graph, b, ga: qaoa.state_for(graph, [b], [ga]))
    good_values = np.array(good)
    check(good_values.std() > 0.4, "the correct circuit has a landscape with real structure")
    check(abs(good_values.max() - 3.2295) < 1e-3, "and its maximum is 3.2295 on the same grid")

    swapped = landscape(instance, lambda graph, b, ga: qaoa.state_for(graph, [ga], [b]))
    swapped_values = np.array(swapped)
    check(abs(swapped_values.max() - good_values.max()) < 1e-3, "swapping beta and gamma reaches the same maximum")
    check(abs(swapped_values.max() - 3.2371) / 3.2371 < 0.01,
          "so that bug costs a quarter of a percent: a reader cannot see it in the number")

    check(abs(qaoa.expected_cut(instance, state_mixer_first(instance, 0.0, 0.0)) - 2.5) < 1e-9,
          "with both angles zero the defect is right, because there is nothing to order")
    check(abs(qaoa.expected_cut(instance, state_mixer_first(instance, 0.3, 1.0)) - 2.5) < 1e-9,
          "and it stays right for a nontrivial pair of angles")

    check(len(instance.edges) == 5, "the instance has five edges, which the diagonal gate spans")
    check(abs(qaoa.expected_cut(instance, qaoa.state_for(instance, [0.3109], [0.5713])) - 3.2371) < 1e-3,
          "the correct circuit's optimum is still 3.2371")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
