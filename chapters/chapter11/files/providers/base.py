"""The four operations every provider must support, and the objects they exchange.

A circuit is a list of operations on numbered wires, not a Qiskit object: the adapter is
the only place that knows a vendor's types. That is what makes the replay backend a
drop-in replacement for a real one.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

Op = Tuple[str, Tuple[int, ...], Optional[float]]


@dataclass(frozen=True)
class Circuit:
    """A circuit in the book's own words: ops, wires, and nothing else."""

    wires: int
    ops: Tuple[Op, ...] = ()

    def __post_init__(self) -> None:
        if self.wires < 1:
            raise ValueError(f"a circuit has at least one wire, got {self.wires}")
        for name, wires, theta in self.ops:
            for wire in wires:
                if not 0 <= wire < self.wires:
                    raise ValueError(f"wire {wire} is outside {self.wires}")

    def add(self, name: str, *wires: int, theta: Optional[float] = None) -> "Circuit":
        return Circuit(self.wires, self.ops + ((name, tuple(wires), theta),))

    def depth(self) -> int:
        free_at = [0] * self.wires
        for _, wires, _ in self.ops:
            layer = max(free_at[w] for w in wires) + 1
            for w in wires:
                free_at[w] = layer
        return max(free_at) if self.ops else 0

    def labels(self) -> List[str]:
        check = 1
        while check < self.wires:
            check *= 2
        width = self.wires
        return [format(index, f"0{width}b") for index in range(1 << self.wires)]


@dataclass(frozen=True)
class Profile:
    """What a provider says about a backend before anything runs."""

    provider: str
    backend: str
    qubits: int
    basis: Tuple[str, ...]
    two_qubit: Tuple[str, ...] = ()
    queue: int = 0
    retires_on: str = ""


@dataclass(frozen=True)
class Job:
    provider: str
    backend: str
    id: str
    shots: int
    depth: int
    replay: bool = False


@dataclass(frozen=True)
class Result:
    job: Job
    counts: Dict[str, int]

    @property
    def shots(self) -> int:
        return sum(self.counts.values())

    def frequency(self, label: str) -> float:
        if self.shots <= 0:
            raise ValueError("an empty result has no frequencies")
        return self.counts.get(label, 0) / self.shots


class BackendError(RuntimeError):
    """A provider refused, timed out, or returned something unusable."""


class Backend(ABC):
    """Submit, poll, fetch, cancel. Four operations, every provider."""

    name: str
    provider: str

    @abstractmethod
    def profile(self) -> Profile: ...

    @abstractmethod
    def submit(self, circuit: Circuit, shots: int) -> Job: ...

    @abstractmethod
    def status(self, job: Job) -> str: ...

    @abstractmethod
    def result(self, job: Job) -> Result: ...

    def cancel(self, job: Job) -> None:
        raise BackendError(f"{self.provider} does not support cancellation")

    # -- shared plumbing -------------------------------------------------
    def check_shots(self, shots: int) -> int:
        if shots <= 0:
            raise BackendError(f"shots must be positive, got {shots}")
        if shots > 100_000:
            raise BackendError(f"{shots} shots is beyond the book's limit of 100000")
        return shots


def counts_from_bits(bits: Sequence[int], shots: int) -> Dict[str, int]:
    """A histogram from a list of bitstrings."""
    if shots != len(bits):
        raise ValueError(f"{len(bits)} outcomes do not make {shots} shots")
    counts: Dict[str, int] = {}
    for value in bits:
        key = format(value, "02b") if value < 4 else str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts
