"""The QAOA state, its cost, its gradient, and the circuit a device runs.

The circuit is the textbook one: Hadamards, then p layers of a phase separator
that depends on the graph and a mixer that does not. The only decision this file
makes is the sign convention for the separator, and it is the one that makes the
expected cut rise as gamma grows from zero.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import state as st
from .graph import Graph

Ops = List[Tuple[str, Tuple[int, ...], Optional[float]]]


def state_for(graph: Graph, betas: Sequence[float], gammas: Sequence[float]) -> st.State:
    """|psi(beta, gamma)> for p layers, wire 0 the least significant bit."""
    if len(betas) != len(gammas):
        raise ValueError(f"{len(betas)} betas and {len(gammas)} gammas do not pair")
    if not betas:
        raise ValueError("QAOA has at least one layer")
    vector = st.zero(graph.n)
    for wire in range(graph.n):
        vector = st.h(vector, wire)
    for beta, gamma in zip(betas, gammas):
        for i, j, weight in graph.edges:
            # e^{-i gamma C} with C = w(1 - ZZ)/2 is RZZ(-gamma w), up to a phase
            # that no measurement can see.
            vector = st.rzz(vector, i, j, -gamma * weight)
        for wire in range(graph.n):
            # e^{-i beta X} is RX(2 beta).
            vector = st.rx(vector, wire, 2 * beta)
    return vector


def circuit_ops(graph: Graph, betas: Sequence[float], gammas: Sequence[float]) -> Ops:
    """The same circuit as a gate list, for a device or a drawing."""
    if len(betas) != len(gammas) or not betas:
        raise ValueError("one beta and one gamma per layer, at least one layer")
    ops: Ops = [("h", (wire,), None) for wire in range(graph.n)]
    for beta, gamma in zip(betas, gammas):
        for i, j, weight in graph.edges:
            ops.append(("rzz", (i, j), -gamma * weight))
        for wire in range(graph.n):
            ops.append(("rx", (wire,), 2 * beta))
    return ops


def zz(vector: st.State, i: int, j: int) -> float:
    """<Z_i Z_j>: the correlation the cut is built from."""
    probability = st.probabilities(vector)
    total = 0.0
    for index, weight in enumerate(probability):
        parity = ((index >> i) & 1) ^ ((index >> j) & 1)
        total += weight * (1 if parity == 0 else -1)
    return float(total)


def expected_cut(graph: Graph, vector: st.State) -> float:
    """sum_edges w (1 - <ZZ>) / 2, which is the quantity QAOA minimizes."""
    if vector.shape[0] != 2 ** graph.n:
        raise ValueError(f"{vector.shape[0]} amplitudes do not fit {graph.n} vertices")
    total = 0.0
    for i, j, weight in graph.edges:
        total += weight * (1 - zz(vector, i, j)) / 2
    return float(total)


def cut_histogram(graph: Graph, vector: st.State) -> Dict[int, float]:
    """The probability of each bitmask, with its cut value alongside."""
    return {bits: float(p) for bits, p in enumerate(st.probabilities(vector))}


def distribution_over_cuts(graph: Graph, vector: st.State) -> Dict[float, float]:
    """How much probability sits on each cut value, which is what a histogram shows."""
    out: Dict[float, float] = {}
    for bits, probability in cut_histogram(graph, vector).items():
        value = graph.cut(bits)
        out[value] = out.get(value, 0.0) + probability
    return dict(sorted(out.items()))


def expected_cut_from_counts(graph: Graph, counts: Dict[int, int]) -> float:
    """The estimator a device returns: the mean cut over the shots taken."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no mean cut")
    return sum(graph.cut(bits) * count for bits, count in counts.items()) / total


def cut_sigma(graph: Graph, counts: Dict[int, int]) -> float:
    """The standard error of that mean, from the observed spread."""
    total = sum(counts.values())
    if total <= 1:
        raise ValueError(f"{total} shots have no spread")
    values = np.array([graph.cut(bits) for bits, count in counts.items() for _ in range(count)])
    return float(values.std(ddof=1) / np.sqrt(total))


def approximation_ratio(mean: float, optimum: float) -> float:
    """How much of the optimum the state reaches, as a fraction."""
    if optimum <= 0:
        raise ValueError(f"an optimum is positive, got {optimum}")
    return float(mean / optimum)


def _build(
    graph: Graph,
    betas: Sequence[float],
    gammas: Sequence[float],
    mixer_shift: Optional[Tuple[int, int, float]] = None,
    edge_shift: Optional[Tuple[int, int, float]] = None,
) -> st.State:
    """The circuit with at most one gate's angle moved, which the shift rule needs.

    A parameter that appears in several gates is several parameters that happen
    to share a value. Shifting all of them at once is not the same as taking the
    derivative, so the shifts are applied one gate at a time and the results are
    summed.
    """
    vector = st.zero(graph.n)
    for wire in range(graph.n):
        vector = st.h(vector, wire)
    for layer, (beta, gamma) in enumerate(zip(betas, gammas)):
        for position, (i, j, weight) in enumerate(graph.edges):
            angle = -gamma * weight
            if edge_shift is not None and edge_shift[0] == layer and edge_shift[1] == position:
                angle += edge_shift[2]
            vector = st.rzz(vector, i, j, angle)
        for wire in range(graph.n):
            angle = 2 * beta
            if mixer_shift is not None and mixer_shift[0] == layer and mixer_shift[1] == wire:
                angle += mixer_shift[2]
            vector = st.rx(vector, wire, angle)
    return vector


def gradient(
    graph: Graph, betas: Sequence[float], gammas: Sequence[float]
) -> Tuple[List[float], List[float]]:
    """The parameter-shift gradient: one circuit pair per gate angle.

    For a gate e^{-i theta G / 2} with G squared one, the derivative is
    [f(theta + pi/2) - f(theta - pi/2)] / 2. The mixer's gate is RX(2 beta), so
    its shift in the gate's angle is pi, which is pi/2 in beta, and each wire is
    shifted separately. The separator's edge gate is RZZ(-gamma w), whose angle
    is -gamma w, so one edge shifts by pi/2 and the chain rule multiplies by -w.

    The cost is 2 evaluations per mixer gate plus 2 per separator edge, which is
    the number the shot-budget section divides by.
    """
    if len(betas) != len(gammas) or not betas:
        raise ValueError("one beta and one gamma per layer")
    d_betas: List[float] = []
    d_gammas: List[float] = []
    for layer in range(len(betas)):
        total_beta = 0.0
        for wire in range(graph.n):
            plus = expected_cut(graph, _build(graph, betas, gammas, mixer_shift=(layer, wire, +np.pi / 2)))
            minus = expected_cut(graph, _build(graph, betas, gammas, mixer_shift=(layer, wire, -np.pi / 2)))
            # theta = 2 beta, so d/dbeta = 2 * d/dtheta = plus - minus.
            total_beta += plus - minus
        d_betas.append(float(total_beta))

        total_gamma = 0.0
        for position, (_, _, weight) in enumerate(graph.edges):
            plus = expected_cut(graph, _build(graph, betas, gammas, edge_shift=(layer, position, +np.pi / 2)))
            minus = expected_cut(graph, _build(graph, betas, gammas, edge_shift=(layer, position, -np.pi / 2)))
            total_gamma += -weight * (plus - minus) / 2
        d_gammas.append(float(total_gamma))
    return d_betas, d_gammas


def counts_to_bits(graph: Graph, counts: Dict[str, int]) -> Dict[int, int]:
    """Turn Qiskit's bit strings into the integer keys the rest of the chapter uses."""
    out: Dict[int, int] = {}
    for key, value in counts.items():
        if len(key) != graph.n:
            raise ValueError(f"{key!r} is not a {graph.n}-bit outcome")
        out[int(key, 2)] = out.get(int(key, 2), 0) + value
    return out
