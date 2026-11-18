"""A problem in two alphabets: bits for the solver, spins for the machine.

Annealing hardware speaks Ising: variables are spins in {-1, +1}, the objective is
a linear term plus a coupling per pair, and the machine minimizes it. Most
problems arrive as QUBO: variables are bits in {0, 1} and the objective is a
matrix. The two are the same function under x = (1 + s) / 2, and this file does
the substitution once, exactly, with the offset kept rather than dropped.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

Qubo = Dict[Tuple[int, int], float]
Ising = Tuple[Dict[int, float], Dict[Tuple[int, int], float], float]


def qubo_from_maxcut(edges: Sequence[Tuple[int, int, float]], n: int) -> Qubo:
    """MaxCut as a QUBO: minimize the negative of the cut.

    The cut of an assignment x is sum w (x_i + x_j - 2 x_i x_j), so the QUBO has
    -sum_j w_ij on the diagonal and 2 w_ij off it. The identity the harness
    asserts is energy(x) = -cut(x) for every assignment.
    """
    if n < 2:
        raise ValueError(f"a graph has at least two vertices, got {n}")
    qubo: Qubo = {}
    for i, j, weight in edges:
        if i == j:
            raise ValueError(f"a self-loop at {i} has no cut")
        if weight <= 0:
            raise ValueError(f"weight {weight} on {(i, j)} is not positive")
        key = (min(i, j), max(i, j))
        qubo[(i, i)] = qubo.get((i, i), 0.0) - weight
        qubo[(j, j)] = qubo.get((j, j), 0.0) - weight
        qubo[key] = qubo.get(key, 0.0) + 2 * weight
    return {key: value for key, value in qubo.items() if value != 0}


def energy(qubo: Qubo, assignment: Dict[int, int]) -> float:
    """The QUBO objective at one assignment of bits."""
    total = 0.0
    for (i, j), coefficient in qubo.items():
        if i == j:
            total += coefficient * assignment.get(i, 0)
        else:
            total += coefficient * assignment.get(i, 0) * assignment.get(j, 0)
    return float(total)


def to_ising(qubo: Qubo) -> Ising:
    """x = (1 + s) / 2, carried through with the offset kept."""
    linear: Dict[int, float] = {}
    coupling: Dict[Tuple[int, int], float] = {}
    offset = 0.0
    for (i, j), coefficient in qubo.items():
        if i == j:
            linear[i] = linear.get(i, 0.0) + coefficient / 2
            offset += coefficient / 2
        else:
            key = (min(i, j), max(i, j))
            coupling[key] = coupling.get(key, 0.0) + coefficient / 4
            linear[i] = linear.get(i, 0.0) + coefficient / 4
            linear[j] = linear.get(j, 0.0) + coefficient / 4
            offset += coefficient / 4
    return {k: v for k, v in linear.items() if v != 0}, {k: v for k, v in coupling.items() if v != 0}, offset


def ising_energy(linear: Dict[int, float], coupling: Dict[Tuple[int, int], float], offset: float, spins: Dict[int, int]) -> float:
    """sum h_i s_i + sum J_ij s_i s_j + offset."""
    total = offset
    for i, bias in linear.items():
        total += bias * spins.get(i, 1)
    for (i, j), strength in coupling.items():
        total += strength * spins.get(i, 1) * spins.get(j, 1)
    return float(total)


def to_qubo(
    linear: Dict[int, float],
    coupling: Dict[Tuple[int, int], float],
    offset: float = 0.0,
) -> Tuple[Qubo, float]:
    """The inverse substitution, so a machine's answer can be read as bits.

    Substituting s = 2x - 1 into sum h s + sum J s s + c gives a QUBO plus an
    additive constant. The constant is returned rather than dropped, because the
    round trip is the test: qubo_energy(x) + constant must equal ising_energy(s).
    """
    qubo: Qubo = {}
    for i, bias in linear.items():
        qubo[(i, i)] = qubo.get((i, i), 0.0) + 2 * bias
    for (i, j), strength in coupling.items():
        qubo[(i, j)] = qubo.get((i, j), 0.0) + 4 * strength
        qubo[(i, i)] = qubo.get((i, i), 0.0) - 2 * strength
        qubo[(j, j)] = qubo.get((j, j), 0.0) - 2 * strength
    constant = offset - sum(linear.values()) + sum(coupling.values())
    return {key: value for key, value in qubo.items() if value != 0}, float(constant)


def brute_force(qubo: Qubo, n: int) -> Tuple[float, Dict[int, int]]:
    """The exact minimum, for the instances small enough to enumerate."""
    if n < 1 or n > 20:
        raise ValueError(f"brute force is for 1 to 20 variables, got {n}")
    best_value, best = float("inf"), {}
    for bits in range(2 ** n):
        assignment = {i: (bits >> i) & 1 for i in range(n)}
        value = energy(qubo, assignment)
        if value < best_value:
            best_value, best = value, assignment
    return float(best_value), best


def all_energies(qubo: Qubo, n: int) -> Dict[int, float]:
    return {bits: energy(qubo, {i: (bits >> i) & 1 for i in range(n)}) for bits in range(2 ** n)}


def penalty_qubo(n: int, variables: Iterable[int], strength: float) -> Qubo:
    """A term that punishes the chosen variables being on together.

    Zero is allowed and is a no-op, which is how a caller measures the problem
    before the constraint is added.

    Summing over all pairs gives strength * (k choose 2) when k chosen variables
    are on, which a caller sizes above the largest gain the objective can offer.
    """
    if strength < 0:
        raise ValueError(f"a penalty is non-negative, got {strength}")
    chosen = list(variables)
    if len(chosen) < 2:
        raise ValueError(f"a pair penalty needs two variables, got {len(chosen)}")
    qubo: Qubo = {}
    for i, j in itertools.combinations(sorted(chosen), 2):
        qubo[(i, j)] = qubo.get((i, j), 0.0) + strength
    return qubo


def add(*qubos: Qubo) -> Qubo:
    """The sum of several objectives, which is how a constraint joins an energy."""
    total: Qubo = {}
    for qubo in qubos:
        for key, value in qubo.items():
            total[key] = total.get(key, 0.0) + value
    return {key: value for key, value in total.items() if value != 0}


def variables(qubo: Qubo) -> List[int]:
    found = set()
    for i, j in qubo:
        found.add(i)
        found.add(j)
    return sorted(found)


def report(qubo: Qubo) -> str:
    lines = [f"{'term':12s}{'coefficient':>14s}"]
    for (i, j), value in sorted(qubo.items()):
        name = f"x{i}" if i == j else f"x{i} x{j}"
        lines.append(f"{name:12s}{value:14.3f}")
    return "\n".join(lines)
