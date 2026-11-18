"""The repetition code: encode, measure syndromes, decode.

Three qubits hold one logical bit by majority. The code protects against bit flips
and against nothing else, which is the lesson the chapter measures: an error
correction code trades physical qubits for a logical error rate along the axis it
checks, and along the other axis it is transparent.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


@dataclass(frozen=True)
class Repetition:
    """A distance-d repetition code: d data qubits, d-1 parity checks."""

    distance: int

    def __post_init__(self) -> None:
        if self.distance < 3 or self.distance % 2 == 0:
            raise ValueError(f"a repetition code has an odd distance of at least three, got {self.distance}")

    @property
    def n(self) -> int:
        return self.distance

    @property
    def correctable(self) -> int:
        return (self.distance - 1) // 2

    def encode(self, bit: int) -> List[int]:
        if bit not in (0, 1):
            raise ValueError(f"a logical bit is 0 or 1, got {bit}")
        return [bit] * self.distance

    def checks(self) -> List[Tuple[int, int]]:
        """The parity checks: neighbouring pairs, which is all a repetition code needs."""
        return [(i, i + 1) for i in range(self.distance - 1)]

    def syndromes(self, bits: Sequence[int]) -> Tuple[int, ...]:
        if len(bits) != self.distance:
            raise ValueError(f"{len(bits)} bits for distance {self.distance}")
        return tuple((bits[i] + bits[i + 1]) % 2 for i, _ in enumerate(self.checks()))

    def decode(self, bits: Sequence[int]) -> int:
        """Majority vote; a tie is impossible for an odd distance."""
        if len(bits) != self.distance:
            raise ValueError(f"{len(bits)} bits for distance {self.distance}")
        ones = sum(bits)
        if ones * 2 == self.distance:
            raise ValueError("a tie cannot be decoded")
        return 1 if ones * 2 > self.distance else 0

    def flips(self, bits: Sequence[int], prepared: int) -> int:
        """How many data qubits differ from the encoded state."""
        return sum(1 for value in bits if value != prepared)

    def corrects(self, flips: int) -> bool:
        return flips <= self.correctable

    def report(self) -> str:
        return (
            f"repetition d={self.distance}: {self.n} data qubits, {self.distance - 1} parity checks, "
            f"corrects up to {self.correctable} flip{'s' if self.correctable != 1 else ''}"
        )


def logical_error_ideal(distance: int, p: float) -> float:
    """The exact logical error rate when every qubit flips independently with p.

    The decoder fails when more than half the qubits flip, which is the binomial
    tail. No simulation is needed, and the chapter uses the formula as the null
    hypothesis the device is compared with.
    """
    if not 0 <= p <= 1:
        raise ValueError(f"a probability is in [0, 1], got {p}")
    if distance < 3 or distance % 2 == 0:
        raise ValueError(f"a repetition code has an odd distance of at least three, got {distance}")
    tail = 0.0
    for k in range((distance + 1) // 2, distance + 1):
        tail += _binomial(distance, k) * p ** k * (1 - p) ** (distance - k)
    return float(tail)


def _binomial(n: int, k: int) -> int:
    return len(list(itertools.combinations(range(n), k))) if 0 <= k <= n else 0


def physical_from_counts(counts: Dict[str, int], prepared: int) -> float:
    """The per-qubit flip rate implied by a histogram of measured codewords."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no rate")
    flips = 0
    for key, count in counts.items():
        bits = [int(character) for character in key[::-1]]
        flips += sum(1 for value in bits if value != prepared) * count
    return flips / (total * len(next(iter(counts))))


def logical_from_counts(counts: Dict[str, int], code: Repetition, prepared: int) -> float:
    """The share of shots whose majority vote is wrong."""
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no rate")
    wrong = 0
    for key, count in counts.items():
        bits = [int(character) for character in key[::-1]]
        if len(bits) != code.distance:
            raise ValueError(f"{key!r} is not a {code.distance}-bit codeword")
        if code.decode(bits) != prepared:
            wrong += count
    return wrong / total


def wilson(errors: float, trials: float, z: float = 1.96) -> Tuple[float, float]:
    """A Wilson interval, because a rate near zero breaks the textbook one."""
    if trials <= 0:
        raise ValueError(f"trials must be positive, got {trials}")
    p = errors / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    half = z * (p * (1 - p) / trials + z * z / (4 * trials * trials)) ** 0.5 / denominator
    return max(0.0, centre - half), min(1.0, centre + half)
