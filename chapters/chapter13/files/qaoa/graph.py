"""A small weighted graph, its cuts, and the brute-force answer.

MaxCut asks for a split of the vertices into two sides that maximizes the weight
of the edges crossing it. The graph here is small enough that every split can be
enumerated, which is what makes the quantum answer checkable: the optimum is a
number this file computes exactly, not an estimate.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

Edge = Tuple[int, int, float]


@dataclass(frozen=True)
class Graph:
    """Vertices 0..n-1 and weighted edges between them."""

    n: int
    edges: Tuple[Edge, ...]

    def __post_init__(self) -> None:
        if self.n < 2:
            raise ValueError(f"a graph has at least two vertices, got {self.n}")
        if not self.edges:
            raise ValueError("a graph needs at least one edge")
        seen = set()
        for i, j, weight in self.edges:
            if not (0 <= i < self.n and 0 <= j < self.n):
                raise ValueError(f"edge {(i, j)} is outside 0..{self.n - 1}")
            if i == j:
                raise ValueError(f"edge {(i, j)} is a self-loop")
            if weight <= 0:
                raise ValueError(f"weight {weight} on {(i, j)} is not positive")
            key = (min(i, j), max(i, j))
            if key in seen:
                raise ValueError(f"edge {key} appears twice")
            seen.add(key)

    @property
    def m(self) -> int:
        return len(self.edges)

    def neighbours(self, vertex: int) -> List[int]:
        if not 0 <= vertex < self.n:
            raise ValueError(f"vertex {vertex} is outside 0..{self.n - 1}")
        out = []
        for i, j, _ in self.edges:
            if i == vertex:
                out.append(j)
            elif j == vertex:
                out.append(i)
        return out

    def cut(self, bits: int) -> float:
        """The weight of the edges whose endpoints sit on different sides."""
        if not 0 <= bits < 2 ** self.n:
            raise ValueError(f"{bits} is not a bitmask over {self.n} vertices")
        total = 0.0
        for i, j, weight in self.edges:
            if ((bits >> i) & 1) != ((bits >> j) & 1):
                total += weight
        return total

    def assignment(self, bits: int) -> Tuple[int, ...]:
        return tuple((bits >> vertex) & 1 for vertex in range(self.n))

    def max_cut(self) -> Tuple[float, int]:
        """The optimum and one bitmask that reaches it."""
        best_value, best_bits = -1.0, 0
        for bits in range(2 ** self.n):
            value = self.cut(bits)
            if value > best_value:
                best_value, best_bits = value, bits
        return best_value, best_bits

    def all_cuts(self) -> Dict[int, float]:
        return {bits: self.cut(bits) for bits in range(2 ** self.n)}

    def spectrum(self) -> Dict[float, int]:
        """How many assignments reach each cut value, which is the null model."""
        out: Dict[float, int] = {}
        for value in self.all_cuts().values():
            out[value] = out.get(value, 0) + 1
        return dict(sorted(out.items()))

    def uniform_mean(self) -> float:
        """The average cut over all 2^n assignments: what guessing achieves."""
        return sum(self.all_cuts().values()) / 2 ** self.n

    def degree(self, vertex: int) -> int:
        return len(self.neighbours(vertex))

    def report(self) -> str:
        lines = [f"graph: {self.n} vertices, {self.m} edges"]
        for i, j, weight in self.edges:
            lines.append(f"  {i} -- {j}   weight {weight:g}")
        return "\n".join(lines)


def square_with_diagonal() -> Graph:
    """The chapter's instance: a square plus one diagonal, all weights one."""
    return Graph(n=4, edges=((0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0), (0, 2, 1.0)))


def ring(n: int) -> Graph:
    """A cycle, whose max cut is n for even n and n - 1 for odd n."""
    if n < 3:
        raise ValueError(f"a ring has at least three vertices, got {n}")
    return Graph(n=n, edges=tuple((i, (i + 1) % n, 1.0) for i in range(n)))


def weighted_square() -> Graph:
    """The same square with one heavy edge, which moves the optimum."""
    return Graph(n=4, edges=((0, 1, 1.0), (1, 2, 3.0), (2, 3, 1.0), (3, 0, 1.0)))


def complete(n: int, weight: float = 1.0) -> Graph:
    """Every pair connected, whose max cut is floor(n^2 / 4) for unit weights."""
    if n < 2:
        raise ValueError(f"a complete graph has at least two vertices, got {n}")
    edges = tuple((i, j, weight) for i, j in itertools.combinations(range(n), 2))
    return Graph(n=n, edges=edges)
