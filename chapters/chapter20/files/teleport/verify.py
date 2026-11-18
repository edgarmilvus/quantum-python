"""From counts to a Bloch vector, with the readout and the Pauli frame handled.

Three arithmetic steps stand between a histogram and the chapter's number. The first is
a marginal over the receiving qubit, because the two outcome bits are random and their
only job is the correction. The second is the readout matrix, inverted from the calibration
circuits. The third is the Pauli frame, which is what the postselect version applies in
software instead of on the device.

The correction signs are the whole subtlety: a Pauli frame changes the observable, and a
Z on the receiving qubit flips the sign of <X> and <Y> but not of <Z>.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np

from .circuit import BASES
from .state import Prepared, distance, fidelity

# Which frame bits flip the measured bit in each tomography basis.
FRAME = {
    "X": (1, 0),  # the Z correction flips X
    "Y": (1, 1),  # both flips
    "Z": (0, 1),  # the X correction flips Z
}


def bit_of(key: str, qubit: int) -> int:
    """Qiskit prints q2 q1 q0; qubit 0 is the rightmost character."""
    return int(key[len(key) - 1 - qubit])


def marginal(counts: Dict[str, int], qubit: int = 2) -> Tuple[float, float]:
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no marginal")
    width = len(next(iter(counts)))
    if not 0 <= qubit < width:
        raise ValueError(f"qubit {qubit} is outside a {width}-bit key")
    ones = sum(count for key, count in counts.items() if bit_of(key, qubit) == 1)
    return (1.0 - ones / total, ones / total)


def readout_matrix(p_one_given_zero: float, p_zero_given_one: float) -> np.ndarray:
    a, b = p_one_given_zero, p_zero_given_one
    return np.array([[1 - a, b], [a, 1 - b]])


def corrected_marginal(counts: Dict[str, int], a: float, b: float, qubit: int = 2) -> Tuple[float, float]:
    """Invert the 2 by 2 readout matrix and renormalise."""
    p = np.array(marginal(counts, qubit), dtype=float)
    fixed = np.linalg.inv(readout_matrix(a, b)) @ p
    fixed = np.clip(fixed, 0, None)
    return (float(fixed[0] / fixed.sum()), float(fixed[1] / fixed.sum()))


def postselect(counts: Dict[str, int], basis: str, correct: bool = True) -> Dict[str, int]:
    """Apply the Pauli frame to the receiving bit, shot by shot."""
    if basis not in BASES:
        raise ValueError(f"a basis is one of {BASES}, got {basis!r}")
    flips_x, flips_z = FRAME[basis]
    out: Dict[str, int] = {"0": 0, "1": 0}
    for key, count in counts.items():
        bit = bit_of(key, 2)
        m0, m1 = bit_of(key, 0), bit_of(key, 1)
        if correct:
            bit ^= (flips_x * m0) ^ (flips_z * m1)
        out[str(bit)] += count
    return out


def expectation(counts: Dict[str, int], a: float, b: float) -> float:
    """The expectation of the measured Pauli, with the corrected 2 by 2 marginal."""
    qubit = 0 if len(next(iter(counts))) == 1 else 2
    p0, p1 = corrected_marginal(counts, a, b, qubit)
    return p0 - p1


def bloch(
    counts_by_basis: Dict[str, Dict[str, int]],
    a: float,
    b: float,
    postselected: bool = False,
    correct: bool = True,
) -> Tuple[float, float, float]:
    """The three expectation values, in the order (X, Y, Z)."""
    if set(counts_by_basis) != set(BASES):
        raise ValueError(f"tomography needs the three bases, got {sorted(counts_by_basis)}")
    values = []
    for basis in BASES:
        counts = postselect(counts_by_basis[basis], basis, correct) if postselected else counts_by_basis[basis]
        values.append(expectation(counts, a, b))
    return tuple(values)  # type: ignore[return-value]


@dataclass(frozen=True)
class Calibration:
    """The two directed rates of the receiving qubit."""

    p_one_given_zero: float
    p_zero_given_one: float

    @classmethod
    def from_counts(cls, circuits: List[Dict], qubit: int = 2) -> "Calibration":
        """Accept the record's entries (counts under "counts") or bare histograms."""
        if len(circuits) < qubit + 2:
            raise ValueError(f"a calibration needs {qubit + 2} circuits, got {len(circuits)}")
        histograms = [entry["counts"] if "counts" in entry else entry for entry in circuits]
        p01 = marginal(histograms[0], qubit)[1]
        p10 = marginal(histograms[qubit + 1], qubit)[0]
        return cls(p01, p10)

    def report(self) -> str:
        return f"readout 0->1 {self.p_one_given_zero:.4f}, 1->0 {self.p_zero_given_one:.4f}"


@dataclass(frozen=True)
class Report:
    prepared: Prepared
    measured: Tuple[float, float, float]
    fidelity: float
    distance: float
    kind: str

    @property
    def verdict(self) -> str:
        if self.fidelity >= 0.90:
            return "the state arrived"
        if self.fidelity >= 2 / 3:
            return "degraded, above the classical guess"
        return "not teleported"

    def report(self) -> str:
        x, y, z = self.measured
        return (
            f"{self.kind:12s} bloch ({x:+.4f}, {y:+.4f}, {z:+.4f})  "
            f"F {self.fidelity:.4f}  {self.verdict}"
        )


def report(prepared: Prepared, measured: Tuple[float, float, float], kind: str) -> Report:
    return Report(prepared, measured, fidelity(prepared, measured), distance(prepared, measured), kind)


def run(record: dict, kind: str = "dynamic") -> Report:
    """Read one recorded run and score its tomography."""
    prepared = Prepared(record["prepared"]["theta"], record["prepared"]["phi"])
    if kind not in record:
        raise KeyError(f"the record has no {kind!r} tomography")
    calibration = Calibration.from_counts(record["calibration"])
    counts = record[kind]["counts"]
    measured = bloch(counts, calibration.p_one_given_zero, calibration.p_zero_given_one,
                     postselected=(kind == "postselect"), correct=(kind != "uncorrected"))
    return report(prepared, measured, kind)
