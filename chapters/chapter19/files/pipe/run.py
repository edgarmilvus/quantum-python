"""The execution stage: read a record, correct the readout, and report.

A recorded run is the pipeline's output, and the pipeline's second half is the part
that turns it into a claim: a per-qubit readout model from the calibration circuits, a
corrected histogram, and a verdict that says whether the peak is the answer the task
asked for.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from .spec import Task

ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Readout:
    """One 2x2 matrix per qubit, from the two directed rates the calibration measured."""

    p_one_given_zero: Tuple[float, ...]
    p_zero_given_one: Tuple[float, ...]

    def matrix(self) -> np.ndarray:
        n = len(self.p_one_given_zero)
        out = np.array([[1.0]])
        for a, b in zip(self.p_one_given_zero, self.p_zero_given_one):
            out = np.kron(out, np.array([[1 - a, b], [a, 1 - b]]))
        return out

    def report(self) -> str:
        pairs = ", ".join(
            f"q{index} {a:.3f}/{b:.3f}" for index, (a, b) in enumerate(zip(self.p_one_given_zero, self.p_zero_given_one))
        )
        return f"readout 0->1/1->0: {pairs}"


def readout(record: dict) -> Readout:
    """Build the model from the calibration circuits in a recorded run."""
    if "calibration" not in record:
        raise ValueError("the record has no calibration circuits")
    zero = record["calibration"][0]["counts"]
    total_zero = sum(zero.values())
    if total_zero <= 0:
        raise ValueError("the all-zero calibration is empty")
    n = len(record["secret"])
    p01 = [
        sum(count for key, count in zero.items() if int(key[::-1][qubit]) == 1) / total_zero
        for qubit in range(n)
    ]
    p10 = []
    for entry in record["calibration"][1:]:
        qubit = int(entry["prepared"]) - 1
        total = sum(entry["counts"].values())
        p10.append(sum(count for key, count in entry["counts"].items() if int(key[::-1][qubit]) == 0) / total)
    return Readout(tuple(p01), tuple(p10))


def correct(counts: Dict[str, int], model: Readout) -> Dict[str, float]:
    """Invert the readout matrix and renormalise, which is chapter 12's arithmetic."""
    n = len(model.p_one_given_zero)
    keys = [format(index, f"0{n}b") for index in range(2 ** n)]
    raw = np.array([counts.get(key, 0) for key in keys], dtype=float)
    total = raw.sum()
    if total <= 0:
        raise ValueError("an empty histogram has nothing to correct")
    corrected = np.linalg.inv(model.matrix()) @ (raw / total)
    corrected = np.clip(corrected, 0, None)
    return dict(zip(keys, (float(value) for value in corrected / corrected.sum())))


def top(distribution: Dict[str, float]) -> Tuple[str, float]:
    key = max(distribution, key=distribution.get)
    return key, distribution[key]


@dataclass(frozen=True)
class Report:
    task: str
    secret: str
    shots: int
    seconds: float
    usd: float
    raw_top: str
    raw_share: float
    corrected_top: str
    corrected_share: float

    @property
    def ok(self) -> bool:
        return self.corrected_top == self.secret

    def report(self) -> str:
        verdict = "the secret was recovered" if self.ok else "the secret was not recovered"
        return (
            f"{self.task}: {self.shots} shots in {self.seconds:.1f} s for {self.usd:.2f} USD\n"
            f"  raw       {self.raw_top} at {self.raw_share:.4f}\n"
            f"  corrected {self.corrected_top} at {self.corrected_share:.4f}\n"
            f"  {verdict}"
        )


def run(record: dict, task: Task, seconds: float = 4.0, usd: float = 0.0) -> Report:
    """The pipeline's second half: calibration, correction, and a verdict."""
    if record.get("secret") != task.secret:
        raise ValueError(f"the record's secret {record.get('secret')} is not the task's {task.secret}")
    counts = record["counts"]
    model = readout(record)
    corrected = correct(counts, model)
    raw_key, raw_share = top({key: value / sum(counts.values()) for key, value in counts.items()})
    corrected_key, corrected_share = top(corrected)
    return Report(
        task=task.name,
        secret=task.secret,
        shots=int(record["shots"]),
        seconds=seconds,
        usd=usd,
        raw_top=raw_key,
        raw_share=raw_share,
        corrected_top=corrected_key,
        corrected_share=corrected_share,
    )


def load(case: str) -> dict:
    path = ROOT / "runs" / case / "result.json"
    if not path.exists():
        raise FileNotFoundError(f"no recorded run at {path}")
    return json.loads(path.read_text())
