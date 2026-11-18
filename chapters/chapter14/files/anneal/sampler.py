"""The sampler contract, and two implementations of it.

A sampler takes an Ising problem and returns samples. That is the whole interface
D-Wave's stack is built on, and it is small enough to write twice: an exact
sampler for the instances that can be enumerated, and a simulated annealer for
the ones that cannot.

The annealing schedule is the part worth teaching. A temperature that falls too
fast freezes the system in whatever basin it started in; one that falls slowly
enough lets the state cross barriers while it still can. The chapter measures the
difference rather than asserting it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

Coupling = Dict[Tuple[int, int], float]


@dataclass
class Result:
    """What a sampler returns: samples, their energies, and how often each was seen."""

    samples: List[Dict[int, int]]
    energies: List[float]
    occurrences: List[int]
    variable_type: str = "SPIN"
    info: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.samples:
            raise ValueError("a result has at least one sample")
        if len(self.samples) != len(self.energies) or len(self.energies) != len(self.occurrences):
            raise ValueError("samples, energies and occurrences must align")

    @property
    def reads(self) -> int:
        return sum(self.occurrences)

    def best(self) -> Tuple[float, Dict[int, int]]:
        index = int(np.argmin(self.energies))
        return self.energies[index], self.samples[index]

    def unique(self) -> int:
        return len({tuple(sorted(sample.items())) for sample in self.samples})

    def report(self) -> str:
        value, sample = self.best()
        spins = "".join(str(sample[key]) for key in sorted(sample))
        return f"{self.reads} reads, best energy {value:.3f} at spins {spins}, {self.unique()} distinct"


def ising_energy(
    linear: Dict[int, float], coupling: Coupling, offset: float, spins: Dict[int, int]
) -> float:
    total = offset
    for i, bias in linear.items():
        total += bias * spins.get(i, 1)
    for (i, j), strength in coupling.items():
        total += strength * spins.get(i, 1) * spins.get(j, 1)
    return float(total)


def local_field(
    linear: Dict[int, float], coupling: Coupling, spins: Dict[int, int], target: int
) -> float:
    """The field on one spin: what flipping it would feel."""
    field = linear.get(target, 0.0)
    for (i, j), strength in coupling.items():
        if i == target:
            field += strength * spins.get(j, 1)
        elif j == target:
            field += strength * spins.get(i, 1)
    return float(field)


def flip_delta(
    linear: Dict[int, float], coupling: Coupling, spins: Dict[int, int], target: int
) -> float:
    """The energy change from flipping one spin: -2 s_i times its local field."""
    return float(-2 * spins.get(target, 1) * local_field(linear, coupling, spins, target))


@dataclass
class Exact:
    """Every spin assignment, for the instances small enough to list."""

    linear: Dict[int, float]
    coupling: Coupling
    offset: float = 0.0

    def sample(self, num_reads: int = 1, **_: object) -> Result:
        if num_reads < 1:
            raise ValueError(f"reads must be positive, got {num_reads}")
        variables = variables_of(self.linear, self.coupling)
        if len(variables) > 20:
            raise ValueError(f"exact sampling is for 20 variables, got {len(variables)}")
        best = (-math.inf, {})
        height = 0
        for bits in range(2 ** len(variables)):
            spins = {variable: (1 if (bits >> position) & 1 else -1) for position, variable in enumerate(variables)}
            value = -ising_energy(self.linear, self.coupling, self.offset, spins)
            if value > best[0]:
                best, height = (value, spins), 1
            elif value == best[0]:
                height += 1
        energy_value = -best[0]
        return Result(
            samples=[dict(best[1])],
            energies=[energy_value],
            occurrences=[num_reads],
            info={"ground states": float(height)},
        )


@dataclass
class Annealer:
    """Simulated annealing on the Ising energy, with a geometric schedule."""

    linear: Dict[int, float]
    coupling: Coupling
    offset: float = 0.0
    sweeps: int = 200
    hot: float = 4.0
    cold: float = 0.05
    seed: int = 7

    def __post_init__(self) -> None:
        if self.sweeps < 1:
            raise ValueError(f"sweeps must be positive, got {self.sweeps}")
        if self.hot <= 0 or self.cold <= 0:
            raise ValueError(f"temperatures are positive, got {self.hot} and {self.cold}")
        if self.cold > self.hot:
            raise ValueError(f"the schedule cools, so cold <= hot, got {self.hot} and {self.cold}")

    def schedule(self) -> np.ndarray:
        """The inverse temperature at each sweep, geometric from cold to hot."""
        betas = np.geomspace(1 / self.hot, 1 / self.cold, self.sweeps)
        return betas

    def run_once(self, rng: np.random.Generator) -> Tuple[float, Dict[int, int], float]:
        variables = variables_of(self.linear, self.coupling)
        spins = {variable: int(rng.choice([-1, 1])) for variable in variables}
        value = ising_energy(self.linear, self.coupling, self.offset, spins)
        accepted = 0
        proposed = 0
        for beta in self.schedule():
            for variable in variables:
                proposed += 1
                delta = flip_delta(self.linear, self.coupling, spins, variable)
                if delta <= 0 or rng.random() < math.exp(-beta * delta):
                    spins[variable] = -spins[variable]
                    value += delta
                    accepted += 1
        return float(value), spins, accepted / proposed

    def trace(self, every: int = 1) -> List[Tuple[int, float]]:
        """The energy after every `every` sweeps, for one run at a fixed seed.

        A trace is what a reader wants when a run fails: it shows the sweep at
        which the state stopped improving, which is the sweep at which the
        temperature became too low to leave the basin.
        """
        if every < 1:
            raise ValueError(f"every must be positive, got {every}")
        rng = np.random.default_rng(self.seed)
        variables = variables_of(self.linear, self.coupling)
        spins = {variable: int(rng.choice([-1, 1])) for variable in variables}
        value = ising_energy(self.linear, self.coupling, self.offset, spins)
        out: List[Tuple[int, float]] = [(0, float(value))]
        for index, beta in enumerate(self.schedule(), start=1):
            for variable in variables:
                delta = flip_delta(self.linear, self.coupling, spins, variable)
                if delta <= 0 or rng.random() < math.exp(-beta * delta):
                    spins[variable] = -spins[variable]
                    value += delta
            if index % every == 0:
                out.append((index, float(value)))
        return out

    def sample(self, num_reads: int = 10, **_: object) -> Result:
        if num_reads < 1:
            raise ValueError(f"reads must be positive, got {num_reads}")
        rng = np.random.default_rng(self.seed)
        samples: List[Dict[int, int]] = []
        energies: List[float] = []
        acceptance = 0.0
        for _ in range(num_reads):
            value, spins, rate = self.run_once(rng)
            samples.append(spins)
            energies.append(value)
            acceptance += rate / num_reads
        grouped: Dict[Tuple[Tuple[int, int], ...], List[int]] = {}
        for index, sample in enumerate(samples):
            key = tuple(sorted(sample.items()))
            grouped.setdefault(key, []).append(index)
        unique_samples = [samples[indices[0]] for indices in grouped.values()]
        unique_energies = [energies[indices[0]] for indices in grouped.values()]
        occurrences = [len(indices) for indices in grouped.values()]
        return Result(
            samples=unique_samples,
            energies=unique_energies,
            occurrences=occurrences,
            info={"acceptance": float(acceptance), "sweeps": float(self.sweeps)},
        )


def variables_of(linear: Dict[int, float], coupling: Coupling) -> List[int]:
    found = set(linear)
    for i, j in coupling:
        found.add(i)
        found.add(j)
    return sorted(found)


def reads_for(p_success: float, target: float = 0.95) -> int:
    """Reads needed for at least `target` chance of one success."""
    if not 0 < p_success <= 1:
        raise ValueError(f"a per-read probability is in (0, 1], got {p_success}")
    if not 0 < target < 1:
        raise ValueError(f"a target is in (0, 1), got {target}")
    if p_success == 1:
        return 1
    return int(math.ceil(math.log(1 - target) / math.log(1 - p_success)))


def success_rate(result: Result, optimum: float, tolerance: float = 0.0) -> float:
    """The share of reads that reached the optimum, within a tolerance."""
    if result.reads < 1:
        raise ValueError("an empty result has no rate")
    hits = sum(
        count for energy, count in zip(result.energies, result.occurrences) if energy <= optimum + tolerance
    )
    return hits / result.reads
