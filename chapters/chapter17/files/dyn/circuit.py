"""A dynamic circuit: measurement in the middle, and a gate that depends on it.

The chapter's circuit prepares a repetition codeword, extracts the two parities
with two ancillas, measures the ancillas into classical bits *during* the circuit,
and applies a Pauli correction conditioned on those bits. That is the difference
between chapter 16's vote after the fact and correction while the circuit runs.

The operations are a list, so the same circuit can be simulated by the chapter's
own trajectory code and built into a Qiskit object for a device.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple, Union

Op = Tuple
Circuit = List[Op]


def prepare(prepared: int, distance: int = 3) -> Circuit:
    if prepared not in (0, 1):
        raise ValueError(f"a prepared bit is 0 or 1, got {prepared}")
    if distance < 3:
        raise ValueError(f"a repetition code has distance at least three, got {distance}")
    return [("x", (qubit,)) for qubit in range(distance)] if prepared else []


def inject(distance: int, flips: Sequence[int]) -> Circuit:
    """A test error, so the simulator can be checked without a device."""
    if len(set(flips)) != len(flips):
        raise ValueError(f"a qubit cannot be flipped twice, got {flips}")
    for qubit in flips:
        if not 0 <= qubit < distance:
            raise ValueError(f"qubit {qubit} is outside 0..{distance - 1}")
    return [("x", (qubit,)) for qubit in flips]


def syndrome(distance: int = 3, first_ancilla: int = 3) -> Circuit:
    """The parity checks, written as CNOTs onto ancillas."""
    ops: Circuit = []
    for check, (left, right) in enumerate(zip(range(distance - 1), range(1, distance))):
        ancilla = first_ancilla + check
        ops.append(("cx", (left, ancilla)))
        ops.append(("cx", (right, ancilla)))
    return ops


def measure_ancillas(distance: int = 3, first_ancilla: int = 3, first_clbit: int = 3) -> Circuit:
    return [("measure", (first_ancilla + index,), first_clbit + index) for index in range(distance - 1)]


def correction(distance: int = 3, first_ancilla: int = 3, first_clbit: int = 3) -> Circuit:
    """The feed-forward: the syndrome value names one qubit to flip.

    The two clbits form a two-bit register, and the device compares the whole
    register with a constant. Nested conditionals are refused by the runtime —
    error 1524 — so the correction is three flat tests on the register value:

        value 1 (s0=1, s1=0) -> flip qubit 0
        value 3 (s0=1, s1=1) -> flip qubit 1
        value 2 (s0=0, s1=1) -> flip qubit 2
    """
    if distance != 3:
        raise ValueError(f"this correction table is written for d=3, got {distance}")
    left, right = first_clbit, first_clbit + 1
    return [
        ("ifreg", ((left, right), 1), [("x", (0,))]),
        ("ifreg", ((left, right), 3), [("x", (1,))]),
        ("ifreg", ((left, right), 2), [("x", (2,))]),
    ]


def memory(
    distance: int = 3,
    prepared: int = 0,
    correct: bool = True,
    flips: Sequence[int] = (),
    rounds: int = 1,
) -> Circuit:
    """Prepare, (inject an error), then `rounds` of extract, measure and correct."""
    if rounds < 1:
        raise ValueError(f"a memory has at least one round, got {rounds}")
    ops: Circuit = prepare(prepared, distance)
    ops += inject(distance, flips)
    for round_index in range(rounds):
        ops += syndrome(distance)
        ops += measure_ancillas(distance)
        if correct:
            ops += correction(distance)
        if round_index + 1 < rounds:
            ops += [("reset", (first,)) for first in range(distance, distance + distance - 1)]
    ops += [("measure", (qubit,), qubit) for qubit in range(distance)]
    return ops


def clbits(ops: Circuit) -> int:
    """The number of classical bits the circuit writes, which is the register size."""
    highest = -1
    for op in ops:
        if op[0] == "measure":
            highest = max(highest, int(op[2]))
    return highest + 1


def qubits(ops: Circuit) -> int:
    """The number of qubits the circuit touches, including ancillas."""
    highest = 0
    for op in ops:
        if op[0] in ("x", "h", "measure"):
            highest = max(highest, int(op[1][0]))
        elif op[0] == "cx":
            highest = max(highest, int(op[1][0]), int(op[1][1]))
        elif op[0] in ("if", "ifreg"):
            highest = max(highest, qubits(op[2]))
    return highest + 1
