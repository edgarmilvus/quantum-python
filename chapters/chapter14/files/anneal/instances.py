"""The three instances the chapter works on, defined once.

A chapter that builds its test data inside a demo and again inside a harness will
eventually build two different tests. These functions are the single source: the
demos import them, the harness imports them, and the numbers in the prose are
whatever they return.
"""

from __future__ import annotations

import itertools
from typing import Dict, List, Tuple

import numpy as np

Coupling = Dict[Tuple[int, int], float]


def maxcut_square() -> List[Tuple[int, int, float]]:
    """The chapter 13 instance: a square plus one diagonal, unit weights."""
    return [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0), (0, 2, 1.0)]


def spin_glass(n: int = 12, seed: int = 2026) -> Coupling:
    """All pairs coupled, each sign drawn once, so the instance is reproducible."""
    if n < 3:
        raise ValueError(f"a spin glass needs at least three variables, got {n}")
    rng = np.random.default_rng(seed)
    return {
        (i, j): float(rng.choice([-1.0, 1.0]))
        for i, j in itertools.combinations(range(n), 2)
    }


def frustrated_ring(n: int = 6) -> Coupling:
    """A ring with one anti-ferromagnetic bond per pair, so no assignment satisfies all.

    Odd rings frustrate with every bond anti-ferromagnetic; even rings need one
    sign flipped, which this function does at the last bond.
    """
    if n < 3:
        raise ValueError(f"a ring has at least three vertices, got {n}")
    coupling: Coupling = {(i, (i + 1) % n): -1.0 for i in range(n)}
    coupling[(n - 1, 0)] = 1.0
    return coupling
