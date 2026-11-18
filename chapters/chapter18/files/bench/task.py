"""The benchmark's task: a three-qubit GHZ state and the distance from ideal.

One circuit, one ideal distribution, one number. The circuit is H, CX, CX, which
should produce 000 and 111 at one half each; the number is the total variation
distance between what a backend returned and that ideal, which is half the L1
distance and is in [0, 1].

The choice of task is the benchmark's first decision. GHZ is small enough to run on
every backend in the book, entangled enough that a broken two-qubit gate shows, and
symmetric enough that its ideal distribution has two entries, which makes the
distance computable by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Sequence, Tuple

Ideal = Dict[str, float]


def ghz_ops(qubits: int = 3) -> Sequence[Tuple[str, Tuple[int, ...]]]:
    """H on the first qubit, then a CX chain: the standard GHZ preparation."""
    if qubits < 2:
        raise ValueError(f"a GHZ state has at least two qubits, got {qubits}")
    ops: list = [("h", (0,))]
    for qubit in range(qubits - 1):
        ops.append(("cx", (qubit, qubit + 1)))
    return ops


def ideal_distribution(qubits: int = 3) -> Ideal:
    """The all-zero and all-one strings, one half each."""
    if qubits < 2:
        raise ValueError(f"a GHZ state has at least two qubits, got {qubits}")
    return {"0" * qubits: 0.5, "1" * qubits: 0.5}


def normalise(counts: Dict[str, int]) -> Dict[str, float]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no distribution")
    return {str(key): value / total for key, value in counts.items()}


def total_variation(counts: Dict[str, int], ideal: Ideal) -> float:
    """Half the L1 distance between the observed and the ideal distribution."""
    observed = normalise(counts)
    keys = set(observed) | set(ideal)
    return 0.5 * sum(abs(observed.get(key, 0.0) - ideal.get(key, 0.0)) for key in keys)


def hellinger(counts: Dict[str, int], ideal: Ideal) -> float:
    """A distance that punishes small probabilities less than the L1 does."""
    observed = normalise(counts)
    keys = set(observed) | set(ideal)
    total = sum(
        (observed.get(key, 0.0) ** 0.5 - ideal.get(key, 0.0) ** 0.5) ** 2 for key in keys
    )
    return float((total / 2) ** 0.5)


def signal(counts: Dict[str, int]) -> float:
    """The share of shots on the two outcomes the circuit was built to produce."""
    observed = normalise(counts)
    width = len(next(iter(observed)))
    return observed.get("0" * width, 0.0) + observed.get("1" * width, 0.0)


def noise_floor(shots: int, ideal: Ideal, seed: int = 0) -> float:
    """The TVD an exact sampler shows at this shot count, which is the baseline.

    A backend cannot beat this number; it can only come close to it. A reported TVD
    below the floor is not a better machine, it is a source that returned
    probabilities instead of samples.
    """
    import numpy as np

    if shots < 1:
        raise ValueError(f"shots must be positive, got {shots}")
    keys = sorted(set(ideal) | {format(index, "03b") for index in range(8)})
    probabilities = [ideal.get(key, 0.0) for key in keys]
    rng = np.random.default_rng(seed)
    draws = rng.multinomial(shots, probabilities)
    counts = {key: int(count) for key, count in zip(keys, draws) if count}
    return total_variation(counts, ideal)


@dataclass(frozen=True)
class Row:
    """One benchmark entry: who ran the task, how well, how long, and for how much."""

    source: str
    provider: str
    kind: str
    tvd: float
    shots: int
    wall_seconds: float
    cost_usd: float
    notes: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.tvd <= 1:
            raise ValueError(f"a distance is in [0, 1], got {self.tvd}")
        if self.shots < 1:
            raise ValueError(f"shots must be positive, got {self.shots}")
        if self.wall_seconds < 0 or self.cost_usd < 0:
            raise ValueError("time and cost are non-negative")

    def report(self) -> str:
        return (
            f"{self.source:26s}{self.kind:6s}{self.tvd:8.4f}{self.shots:7d}"
            f"{self.wall_seconds:9.2f}{self.cost_usd:9.4f}   {self.notes}"
        )


def table(rows: Iterable[Row]) -> str:
    lines = [f"{'source':26s}{'kind':6s}{'tvd':>8s}{'shots':>7s}{'wall s':>9s}{'usd':>9s}   note"]
    for row in rows:
        lines.append(row.report())
    return "\n".join(lines)


def improvements(rows: Sequence[Row]) -> Dict[str, float]:
    """Ratios between the worst and the best row, which is what a reader compares."""
    if len(rows) < 2:
        raise ValueError("a comparison needs at least two rows")
    worst = max(rows, key=lambda row: row.tvd)
    best = min(rows, key=lambda row: row.tvd)
    return {
        "worst": worst.tvd,
        "best": best.tvd,
        "ratio": worst.tvd / best.tvd if best.tvd > 0 else float("inf"),
        "spread": worst.tvd - best.tvd,
    }
