"""Chains, embeddings, and the vote that repairs a broken one.

A quantum annealer does not have a complete graph. Its qubits are wired in a
sparse pattern, so a logical variable that must couple to five others becomes a
*chain* of physical qubits held together by strong couplings. If one link of the
chain disagrees at readout, the chain is broken, and the majority vote that
repairs it is a decision with an error rate the chapter measures.

The graph here is Chimera C(2,2): four cells of eight qubits, each cell complete
bipartite between its four horizontal and four vertical qubits, with horizontal
qubits chained to the cell on the right and vertical ones to the cell below.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

Physical = Tuple[int, int, int]
Coupling = Dict[Tuple[int, int], float]


@dataclass(frozen=True)
class Chimera:
    """A grid of cells, eight qubits each, wired the D-Wave way."""

    rows: int
    cols: int

    def __post_init__(self) -> None:
        if self.rows < 1 or self.cols < 1:
            raise ValueError(f"a Chimera is at least 1x1, got {self.rows}x{self.cols}")

    @property
    def qubits(self) -> List[Physical]:
        return [(row, column, k) for row in range(self.rows) for column in range(self.cols) for k in range(8)]

    def neighbours(self, qubit: Physical) -> List[Physical]:
        row, column, k = qubit
        if not (0 <= row < self.rows and 0 <= column < self.cols and 0 <= k < 8):
            raise ValueError(f"{qubit} is not a qubit of this graph")
        out: List[Physical] = []
        if k < 4:
            out += [(row, column, other) for other in range(4, 8)]
            if column + 1 < self.cols:
                out.append((row, column + 1, k))
        else:
            out += [(row, column, other) for other in range(4)]
            if row + 1 < self.rows:
                out.append((row + 1, column, k))
        return out

    def edges(self) -> List[Tuple[Physical, Physical]]:
        seen: Set[Tuple[Physical, Physical]] = set()
        for qubit in self.qubits:
            for other in self.neighbours(qubit):
                key = tuple(sorted([qubit, other]))
                seen.add(key)
        return sorted(seen)

    def has_edge(self, a: Physical, b: Physical) -> bool:
        return b in self.neighbours(a)


Embedding = Dict[int, List[Physical]]


def validate(embedding: Embedding, graph: Chimera, couplings: Iterable[Tuple[int, int]]) -> None:
    """Every chain must be connected, and every coupling must touch two chains."""
    if not embedding:
        raise ValueError("an embedding maps at least one variable")
    used: Dict[Physical, int] = {}
    for variable, chain in embedding.items():
        if not chain:
            raise ValueError(f"variable {variable} has an empty chain")
        for position in range(len(chain) - 1):
            if not graph.has_edge(chain[position], chain[position + 1]):
                raise ValueError(f"chain for {variable} is not connected at {chain[position]}")
        for qubit in chain:
            if qubit in used:
                raise ValueError(f"{qubit} is in the chains of {used[qubit]} and {variable}")
            used[qubit] = variable
    for i, j in couplings:
        if i not in embedding or j not in embedding:
            raise ValueError(f"coupling {(i, j)} names a variable with no chain")
        if not any(graph.has_edge(a, b) for a in embedding[i] for b in embedding[j]):
            raise ValueError(f"coupling {(i, j)} has no physical edge between the chains")


def physical_problem(
    linear: Dict[int, float],
    coupling: Coupling,
    embedding: Embedding,
    chain_strength: float,
    graph: Optional[Chimera] = None,
) -> Tuple[Dict[Physical, float], Dict[Tuple[Physical, Physical], float]]:
    """Spread each logical variable over its chain and pin the chain together."""
    if chain_strength <= 0:
        raise ValueError(f"a chain strength is positive, got {chain_strength}")
    physical_linear: Dict[Physical, float] = {}
    for variable, chain in embedding.items():
        share = linear.get(variable, 0.0) / len(chain)
        for qubit in chain:
            physical_linear[qubit] = physical_linear.get(qubit, 0.0) + share
    physical_coupling: Dict[Tuple[Physical, Physical], float] = {}
    for variable, chain in embedding.items():
        for left, right in zip(chain, chain[1:]):
            key = tuple(sorted([left, right]))
            physical_coupling[key] = physical_coupling.get(key, 0.0) - chain_strength
    for (i, j), strength in coupling.items():
        edge = _find_edge(graph, embedding[i], embedding[j])
        if edge is None:
            raise ValueError(f"no physical edge joins {i} and {j}")
        key = tuple(sorted(edge))
        physical_coupling[key] = physical_coupling.get(key, 0.0) + strength
    return physical_linear, physical_coupling


def _find_edge(
    graph: Optional[Chimera], left: Sequence[Physical], right: Sequence[Physical]
) -> Optional[Tuple[Physical, Physical]]:
    if graph is None:
        raise ValueError("a physical problem needs the graph its chains were embedded on")
    for a, b in itertools.product(left, right):
        if graph.has_edge(a, b):
            return a, b
    return None


def majority(spins: Dict[Physical, int]) -> int:
    """The vote a chain casts: +1, -1, or a tie resolved toward -1."""
    total = sum(spins.values())
    if not spins:
        raise ValueError("an empty chain has no vote")
    return 1 if total > 0 else -1


def unembed(
    sample: Dict[Physical, int], embedding: Embedding
) -> Tuple[Dict[int, int], List[int]]:
    """Read a physical sample back into logical spins, naming the broken chains."""
    logical: Dict[int, int] = {}
    broken: List[int] = []
    for variable, chain in embedding.items():
        values = {qubit: sample[qubit] for qubit in chain if qubit in sample}
        if len(values) != len(chain):
            raise ValueError(f"the sample is missing part of the chain for {variable}")
        if len(set(values.values())) > 1:
            broken.append(variable)
        logical[variable] = majority(values)
    return logical, sorted(broken)


def chain_break_fraction(sample: Dict[Physical, int], embedding: Embedding) -> float:
    """The share of chains that did not agree with themselves."""
    if not embedding:
        raise ValueError("an embedding maps at least one variable")
    broken = 0
    for chain in embedding.values():
        values = {sample[qubit] for qubit in chain if qubit in sample}
        if len(values) > 1:
            broken += 1
    return broken / len(embedding)


def five_variable_instance() -> Tuple[Dict[int, float], Coupling, Embedding]:
    """A five-variable problem and an embedding of it on Chimera C(2,2).

    The logical graph is a four-cycle with a tail: 0-1, 1-2, 2-3, 3-0 and 3-4.
    Four of the variables need a chain of two physical qubits; the fifth is a
    single qubit, which is what a well-placed variable looks like.
    """
    linear: Dict[int, float] = {}
    coupling: Coupling = {(0, 1): 1.0, (1, 2): 1.0, (2, 3): 1.0, (0, 3): 1.0, (3, 4): 1.0}
    embedding: Embedding = {
        0: [(0, 0, 0), (0, 1, 0)],
        1: [(0, 1, 4), (1, 1, 4)],
        2: [(1, 0, 0), (1, 1, 0)],
        3: [(0, 0, 4), (1, 0, 4)],
        4: [(0, 0, 1)],
    }
    return linear, coupling, embedding


def embed_report(embedding: Embedding) -> str:
    lines = [f"{'variable':10s}{'chain':8s}{'physical qubits'}"]
    for variable, chain in sorted(embedding.items()):
        lines.append(f"{variable:<10d}{len(chain):<8d}{' '.join(str(qubit) for qubit in chain)}")
    return "\n".join(lines)
