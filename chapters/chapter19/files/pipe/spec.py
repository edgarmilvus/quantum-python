"""What a pipeline is given: a task, a budget, and the checks that refuse it.

A task is a circuit with a name, a shot count, a provider and a ceiling on money. The
dataclass validates the four, and the validation is the pipeline's first gate: a task
that names no provider or asks for zero shots fails before anything is submitted, which
is cheaper than failing in a queue.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

SECRET = "1011"


@dataclass(frozen=True)
class Task:
    """One experiment, described in the terms a pipeline needs."""

    name: str
    qubits: int
    shots: int
    provider: str
    budget_usd: float = 5.0
    secret: str = SECRET

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("a task needs a name")
        if self.qubits < 2:
            raise ValueError(f"a task has at least two qubits, got {self.qubits}")
        if not 1 <= self.shots <= 100_000:
            raise ValueError(f"shots are between 1 and 100000, got {self.shots}")
        if self.provider not in KNOWN:
            raise ValueError(f"unknown provider {self.provider!r}; known: {sorted(KNOWN)}")
        if self.budget_usd < 0:
            raise ValueError(f"a budget is non-negative, got {self.budget_usd}")
        if len(self.secret) != self.qubits:
            raise ValueError(f"a {self.qubits}-qubit secret has {self.qubits} bits, got {len(self.secret)!r}")
        if set(self.secret) - {"0", "1"}:
            raise ValueError(f"a secret is a bit string, got {self.secret!r}")

    @property
    def circuits(self) -> int:
        """The task, the all-zero calibration, and one calibration per qubit."""
        return 1 + 1 + self.qubits

    def ideal(self) -> Dict[str, float]:
        """BV puts all the probability on the secret, so the ideal is a delta."""
        return {self.secret: 1.0}


# A price per task and per shot, in dollars, from chapter 11's table.
KNOWN: Dict[str, Tuple[float, float]] = {
    "local": (0.0, 0.0),
    "ibm": (0.0, 0.0),
    "qbraid": (0.0, 0.0),
    "ionq": (0.30, 0.08),
    "braket-iqm": (0.30, 0.0016),
}


def bv_ops(secret: str) -> List[Tuple[str, Tuple[int, ...]]]:
    """The gate list of a Bernstein-Vazirani circuit, for a drawing or a check."""
    if not secret or set(secret) - {"0", "1"}:
        raise ValueError(f"a secret is a bit string, got {secret!r}")
    n = len(secret)
    ops: list = [("x", (n,))] + [("h", (qubit,)) for qubit in range(n + 1)]
    for qubit, bit in enumerate(reversed(secret)):
        if bit == "1":
            ops.append(("cx", (qubit, n)))
    ops += [("h", (qubit,)) for qubit in range(n)]
    return ops
