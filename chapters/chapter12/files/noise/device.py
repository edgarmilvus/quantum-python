"""What the device says about itself: readout flips, gate rates, survival.

Two artefacts feed this module, and both are files in runs/:

- `chapter12/0009-readout-4circuits-4096-ibm/result.json`, four prepared states measured on ibm_fez,
  which gives the readout error of the pair the Bell and CHSH runs used;
- `chapter12/0020-calibration-snapshot/circuit.json`, the provider's saved calibration of
  ibm_fez, exported once, which gives the error of every gate in the Grover
  circuit.

The first is measured by this book; the second is published by the provider and
is the only per-gate data the book has. Chapter 12 keeps them apart, because
mixing them is how a model becomes unfalsifiable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .states import labels

ROOT = Path(__file__).resolve().parents[4]
READOUT_RUN = ROOT / "runs/chapter12/0009-readout-4circuits-4096-ibm/result.json"
CALIBRATION_RUN = ROOT / "runs/chapter12/0020-calibration-snapshot/circuit.json"


def load_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


# -- readout -------------------------------------------------------------
@dataclass(frozen=True)
class Readout:
    """A measured confusion matrix: M[reported, prepared].

    The book keeps the full matrix rather than a single flip probability per
    wire. The 0009 run shows why: preparing |1> misreads at 3.3% and preparing
    |0> at 0.9%, so a symmetric model is wrong by a factor of three on one of
    the two columns.
    """

    table: np.ndarray
    source: str = ""

    def __post_init__(self) -> None:
        size = self.table.shape[0]
        if self.table.shape[1] != size or size < 2 or size & (size - 1):
            raise ValueError(f"a readout matrix is 2^n x 2^n, got {self.table.shape}")
        if not np.allclose(self.table.sum(axis=0), 1.0, atol=1e-9):
            raise ValueError("every column of a readout matrix sums to one")

    @property
    def wires(self) -> int:
        return int(round(np.log2(self.table.shape[0])))

    @classmethod
    def from_matrix(cls, matrix: np.ndarray, source: str = "") -> "Readout":
        return cls(table=np.array(matrix, dtype=float), source=source)

    @classmethod
    def independent(cls, flips: Sequence[float], source: str = "") -> "Readout":
        """The tensor product of per-wire flips, which assumes independence."""
        width = len(flips)
        size = 2 ** width
        matrix = np.zeros((size, size))
        for prepared in range(size):
            for reported in range(size):
                probability = 1.0
                for wire in range(width):
                    same = ((prepared >> wire) & 1) == ((reported >> wire) & 1)
                    probability *= (1 - flips[wire]) if same else flips[wire]
                matrix[reported, prepared] = probability
        return cls(table=matrix, source=source)

    def matrix(self) -> np.ndarray:
        return self.table.copy()

    def sample(self, probabilities: np.ndarray, shots: int, rng: np.random.Generator) -> np.ndarray:
        if len(probabilities) != self.table.shape[0]:
            raise ValueError(f"{len(probabilities)} outcomes do not fit {self.wires} wires")
        seen = self.table @ probabilities
        return rng.multinomial(shots, seen / seen.sum())

    def prob_correct(self, index: int) -> float:
        """M[index, index]: the chance a prepared index is reported as itself."""
        if not 0 <= index < self.table.shape[0]:
            raise ValueError(f"{index} is not an outcome of {self.wires} wires")
        return float(self.table[index, index])

    def to_counts(self, probabilities: np.ndarray, shots: int) -> Dict[str, int]:
        seen = self.table @ probabilities
        keys = labels(self.wires)
        counts: Dict[str, int] = {}
        for key, value in zip(keys, seen):
            count = int(round(float(value) * shots))
            if count:
                counts[key] = count
        difference = shots - sum(counts.values())
        if difference:
            top = max(counts, key=counts.get)
            counts[top] += difference
        return counts


def estimate_flips(record: dict) -> Tuple[float, ...]:
    """Symmetric per-wire flip probabilities, pooled over the prepared columns.

    Under independent and symmetric errors this estimate is exact; the 0009
    matrix falsifies symmetry, and `asymmetry` measures by how much.
    """
    if "preparations" not in record or "counts" not in record:
        raise ValueError("not a readout calibration record")

    def bit(key: str, wire: int, width: int = 2) -> int:
        return int(key[width - 1 - wire])

    prepared: Dict[str, Dict[str, int]] = {}
    for name, wires in record["preparations"].items():
        index = 0
        for wire in wires:
            index |= 1 << wire
        prepared[format(index, "02b")] = record["counts"][name]

    flips: List[float] = []
    for wire in (0, 1):
        wrong = total = 0
        for state, row in prepared.items():
            for reported, count in row.items():
                total += count
                if bit(reported, wire) != bit(state, wire):
                    wrong += count
        flips.append(wrong / total)
    return tuple(flips)


def asymmetry(record: dict) -> Tuple[float, float]:
    """P(report 1 | prepare 0) and P(report 0 | prepare 1), pooled over wires.

    A symmetric model sets both to the same number. The 0009 run returns about
    0.009 and 0.033, which is why the chapter inverts the measured matrix
    instead of a one-parameter model.
    """
    prepared: Dict[str, Dict[str, int]] = {}
    for name, wires in record["preparations"].items():
        index = 0
        for wire in wires:
            index |= 1 << wire
        prepared[format(index, "02b")] = record["counts"][name]

    zero_total = zero_flip = one_total = one_flip = 0
    for state, row in prepared.items():
        for reported, count in row.items():
            for wire in (0, 1):
                bit = int(state[1 - wire])
                if bit:
                    one_total += count
                    if int(reported[1 - wire]) == 0:
                        one_flip += count
                else:
                    zero_total += count
                    if int(reported[1 - wire]) == 1:
                        zero_flip += count
    return zero_flip / zero_total, one_flip / one_total


def readout_from_record(path: Optional[Path] = None, mode: str = "matrix") -> Readout:
    """The measured matrix, or the independent model, from the 0009 run."""
    record = load_json(path or READOUT_RUN)
    source = Path(path or READOUT_RUN).name
    if mode == "matrix":
        size = 4
        matrix = np.zeros((size, size))
        order = ["00", "01", "10", "11"]
        for name, wires in record["preparations"].items():
            index = 0
            for wire in wires:
                index |= 1 << wire
            prepared = format(index, "02b")
            row = record["counts"][name]
            total = sum(row.values())
            for reported, count in row.items():
                matrix[order.index(reported), order.index(prepared)] = count / total
        return Readout.from_matrix(matrix, source=source)
    if mode == "independent":
        return Readout.independent(estimate_flips(record), source=source)
    raise ValueError(f"unknown readout mode {mode!r}")


# -- gate rates ----------------------------------------------------------
@dataclass(frozen=True)
class Rates:
    """A per-gate error rate, looked up by gate name and wires.

    `table` holds either a float (one rate for every gate of that name) or a
    dict keyed by the wire tuple, which is what the calibration file provides.
    """

    table: Dict[str, object]
    source: str = ""

    def error(self, gate: str, wires: Sequence[int]) -> float:
        if gate not in self.table:
            raise KeyError(f"no rate for gate {gate!r}; known: {sorted(self.table)}")
        entry = self.table[gate]
        if isinstance(entry, dict):
            key = tuple(wires)
            if key in entry:
                return float(entry[key])
            if len(key) == 2 and (key[1], key[0]) in entry:
                return float(entry[(key[1], key[0])])
            raise KeyError(f"no rate for {gate} on {key}")
        return float(entry)

    def survival(self, ops: Iterable[Tuple[str, Sequence[int]]]) -> float:
        value = 1.0
        for gate, wires in ops:
            value *= 1 - self.error(gate, wires)
        return value


def rates_from_calibration(record: dict) -> Rates:
    """The error of each gate in the transpiled circuit, as the file recorded it."""
    table: Dict[str, Dict[Tuple[int, ...], float]] = {}
    for op in record["ops"]:
        table.setdefault(op["gate"], {})[tuple(op["qubits"])] = float(op["error"])
    return Rates(table=table, source=str(CALIBRATION_RUN.name))


def uniform_rates(single: float, two: float) -> Rates:
    """One number per gate kind, which is the model the chapter falsifies."""
    return Rates(table={"h": single, "x": single, "sx": single, "rz": 0.0,
                        "cx": two, "cz": two, "ecr": two}, source="uniform")


# -- survival ------------------------------------------------------------
@dataclass(frozen=True)
class Budget:
    """A product of (1 - error) split into the parts a report has to name."""

    gates: float
    readout: float
    one_qubit_gates: int = 0
    two_qubit_gates: int = 0

    @property
    def total(self) -> float:
        return self.gates * self.readout

    def report(self) -> str:
        return (
            f"{self.two_qubit_gates} two-qubit and {self.one_qubit_gates} one-qubit gates "
            f"survive at {self.gates:.4f}; readout at {self.readout:.4f}; "
            f"together {self.total:.4f}"
        )


def survival_from_ops(ops: Sequence[dict], readout: Optional[Readout] = None) -> Budget:
    """Multiply (1 - error) over a recorded op list, then by the readout."""
    gates = 1.0
    one = two = 0
    for op in ops:
        gates *= 1 - float(op["error"])
        if len(op["qubits"]) == 1:
            one += 1
        else:
            two += 1
    readout_factor = 1.0
    if readout is not None:
        # The peak is the probability of one basis state, so the readout factor
        # is that state's diagonal entry, not the product of every diagonal.
        peak = 1 if one + two == 0 else 0
        readout_factor = float(readout.table.mean(axis=1).max()) if readout.wires > 1 else readout.prob_correct(peak)
    return Budget(gates=gates, readout=readout_factor, one_qubit_gates=one, two_qubit_gates=two)


def calibration_budget(path: Optional[Path] = None, marked: int = 5) -> Tuple[Budget, dict]:
    """The chapter's headline prediction: the Grover peak before it was measured."""
    record = load_json(path or CALIBRATION_RUN)
    # The three measured qubits, in logical order, carry the calibration's own
    # readout errors; using them keeps the prediction internally consistent.
    entries = sorted(record["readout"], key=lambda entry: entry["wire"])
    readout = Readout.independent(
        [float(entry["error"]) for entry in entries],
        source="provider calibration snapshot",
    )
    budget = survival_from_ops(record["ops"])
    return Budget(
        gates=budget.gates,
        readout=readout.prob_correct(marked),
        one_qubit_gates=budget.one_qubit_gates,
        two_qubit_gates=budget.two_qubit_gates,
    ), record


def sigma_binomial(probability: float, shots: int) -> float:
    """The standard error of a frequency measured with `shots` shots."""
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    return float(np.sqrt(max(probability * (1 - probability), 0.0) / shots))
