"""Finding the angles: a grid, a simplex, and the budget both of them spend.

QAOA's angles have no closed form. A p-layer circuit has 2p of them, the cost is
a smooth but non-convex function of them, and every evaluation on a device costs
a job. So the chapter uses two methods with different costs: a grid, which is
embarrassingly parallel and needs no gradient, and a simplex, which converges in
a few dozen evaluations but only from a good starting point.

The evaluation counts are not an afterthought. They are the number the shot
budget multiplies, and the chapter's last section divides the runtime by them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from . import qaoa
from .graph import Graph


@dataclass
class Point:
    """One set of angles with the cost it achieved, in circuit evaluations."""

    betas: List[float]
    gammas: List[float]
    cost: float
    evaluations: int = 0
    method: str = ""

    def angles(self) -> List[float]:
        return list(self.betas) + list(self.gammas)

    def report(self) -> str:
        b = ", ".join(f"{value:.4f}" for value in self.betas)
        g = ", ".join(f"{value:.4f}" for value in self.gammas)
        return f"{self.method}: cost {self.cost:.4f} at beta [{b}] gamma [{g}] in {self.evaluations} evaluations"


class Counter:
    """A callable that counts how many times it was asked for a cost."""

    def __init__(self, function: Callable[[Sequence[float]], float]) -> None:
        self.function = function
        self.calls = 0

    def __call__(self, angles: Sequence[float]) -> float:
        self.calls += 1
        return self.function(angles)


def cost_function(graph: Graph, p: int) -> Callable[[Sequence[float]], float]:
    """The exact expected cut as a function of the 2p angles."""

    def evaluate(angles: Sequence[float]) -> float:
        if len(angles) != 2 * p:
            raise ValueError(f"{len(angles)} angles for {p} layers")
        betas = list(angles[:p])
        gammas = list(angles[p:])
        return qaoa.expected_cut(graph, qaoa.state_for(graph, betas, gammas))

    return evaluate


def grid_search(
    graph: Graph,
    p: int,
    beta_steps: int = 12,
    gamma_steps: int = 12,
    beta_range: Tuple[float, float] = (0.0, np.pi / 2),
    gamma_range: Tuple[float, float] = (0.0, np.pi),
) -> Point:
    """Every point of a regular grid, for one layer only.

    A grid over 2p dimensions explodes, so this is a one-layer method and the
    chapter says so: for p layers the grid supplies a starting point for the
    simplex, not a search.
    """
    if p != 1:
        raise ValueError(f"a two-dimensional grid is for one layer, got {p}")
    if beta_steps < 2 or gamma_steps < 2:
        raise ValueError(f"a grid has at least two points per axis, got {beta_steps}x{gamma_steps}")
    evaluate = cost_function(graph, 1)
    best = Point(betas=[0.0], gammas=[0.0], cost=-np.inf, method="grid")
    evaluations = 0
    for beta in np.linspace(*beta_range, beta_steps):
        for gamma in np.linspace(*gamma_range, gamma_steps):
            value = evaluate([beta, gamma])
            evaluations += 1
            if value > best.cost:
                best = Point(betas=[float(beta)], gammas=[float(gamma)], cost=float(value))
    best.evaluations = evaluations
    return best


def landscape(
    graph: Graph,
    beta_steps: int = 24,
    gamma_steps: int = 24,
    beta_range: Tuple[float, float] = (0.0, np.pi / 2),
    gamma_range: Tuple[float, float] = (0.0, np.pi),
) -> np.ndarray:
    """The one-layer cost on a grid, as a 2D array indexed [beta, gamma]."""
    evaluate = cost_function(graph, 1)
    grid = np.zeros((beta_steps, gamma_steps))
    for i, beta in enumerate(np.linspace(*beta_range, beta_steps)):
        for j, gamma in enumerate(np.linspace(*gamma_range, gamma_steps)):
            grid[i, j] = evaluate([beta, gamma])
    return grid


def nelder_mead(
    function: Callable[[Sequence[float]], float],
    start: Sequence[float],
    step: float = 0.2,
    max_iterations: int = 400,
    tolerance: float = 1e-9,
) -> Tuple[np.ndarray, float]:
    """A plain Nelder-Mead simplex, maximising.

    The implementation is forty lines and has no dependencies, which is the right
    trade for a chapter that wants the reader to see the evaluation count. A
    production optimiser would use SciPy's, which adds restarts and a termination
    rule that is harder to fool.
    """
    x0 = np.array(start, dtype=float)
    if x0.ndim != 1 or x0.size == 0:
        raise ValueError(f"a start is a non-empty vector, got {x0}")
    if step <= 0 or max_iterations < 1:
        raise ValueError(f"step and iterations must be positive, got {step} and {max_iterations}")
    dimension = x0.size
    simplex = [x0]
    for index in range(dimension):
        vertex = x0.copy()
        vertex[index] += step
        simplex.append(vertex)
    values = [function(vertex) for vertex in simplex]

    for _ in range(max_iterations):
        order = np.argsort(values)[::-1]
        simplex = [simplex[i] for i in order]
        values = [values[i] for i in order]
        if abs(values[0] - values[-1]) < tolerance:
            break
        centroid = np.mean(simplex[:-1], axis=0)
        worst = simplex[-1]
        reflected = centroid + (centroid - worst)
        reflected_value = function(reflected)
        if reflected_value > values[0]:
            expanded = centroid + 2 * (centroid - worst)
            expanded_value = function(expanded)
            if expanded_value > reflected_value:
                simplex[-1], values[-1] = expanded, expanded_value
            else:
                simplex[-1], values[-1] = reflected, reflected_value
        elif reflected_value > values[-2]:
            simplex[-1], values[-1] = reflected, reflected_value
        else:
            contracted = centroid + 0.5 * (worst - centroid)
            contracted_value = function(contracted)
            if contracted_value > values[-1]:
                simplex[-1], values[-1] = contracted, contracted_value
            else:
                best = simplex[0]
                simplex = [best] + [best + 0.5 * (vertex - best) for vertex in simplex[1:]]
                values = [function(vertex) for vertex in simplex]
    best_index = int(np.argmax(values))
    return simplex[best_index], float(values[best_index])


def optimise(
    graph: Graph,
    p: int,
    beta_steps: int = 12,
    gamma_steps: int = 12,
    restarts: int = 1,
) -> Point:
    """Grid for the start, simplex for the finish, with every call counted."""
    evaluate = cost_function(graph, p)
    counter = Counter(evaluate)
    if p == 1:
        start = grid_search(graph, p, beta_steps, gamma_steps)
        seed = [start.betas[0], start.gammas[0]]
        grid_evaluations = start.evaluations
    else:
        seed = [0.2] * p + [0.4] * p
        grid_evaluations = 0
    best_angles, best_cost = nelder_mead(counter, seed, step=0.15)
    best = Point(
        betas=[float(value) for value in best_angles[:p]],
        gammas=[float(value) for value in best_angles[p:]],
        cost=float(best_cost),
        evaluations=counter.calls + grid_evaluations,
        method=f"grid+simplex p={p}",
    )
    for restart in range(1, restarts):
        offset = 0.3 * restart
        seed = [0.2 + offset] * p + [0.4 + offset] * p
        angles, cost = nelder_mead(counter, seed, step=0.15)
        if cost > best.cost:
            best = Point(
                betas=[float(value) for value in angles[:p]],
                gammas=[float(value) for value in angles[p:]],
                cost=float(cost),
                evaluations=counter.calls + grid_evaluations,
                method=f"grid+simplex p={p} restart {restart}",
            )
    return best


def shots_to_resolve(delta: float, sigma: float, confidence: float = 2.0) -> int:
    """Shots needed to tell two costs apart by `delta` at `confidence` sigmas.

    The mean of N shots has standard error sigma/sqrt(N), so resolving a gap of
    delta needs N = (confidence * sigma / delta)^2.
    """
    if delta <= 0:
        raise ValueError(f"a gap is positive, got {delta}")
    if sigma <= 0:
        raise ValueError(f"a spread is positive, got {sigma}")
    if confidence <= 0:
        raise ValueError(f"a confidence is positive, got {confidence}")
    return int(np.ceil((confidence * sigma / delta) ** 2))


def budget(p: int, edges: int, shots: int, steps: int) -> Dict[str, float]:
    """What an optimisation costs, in circuits and in shots.

    One gradient evaluation shifts one gate at a time: 2 per mixer wire and 2 per
    separator edge. A gradient step therefore needs that many circuits, and an
    optimisation of `steps` steps needs the product.
    """
    if p < 1 or edges < 1 or shots < 1 or steps < 1:
        raise ValueError(f"p, edges, shots and steps are positive, got {p}, {edges}, {shots}, {steps}")
    circuits_per_gradient = 2 * p + 2 * p * edges
    return {
        "circuits per gradient": circuits_per_gradient,
        "circuits for the run": circuits_per_gradient * steps,
        "shots for the run": circuits_per_gradient * steps * shots,
        "seconds at 10 ms a shot": circuits_per_gradient * steps * shots * 0.01,
    }
