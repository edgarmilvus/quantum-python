"""A trajectory simulator for circuits with measurement in the middle.

A statevector is enough, provided the simulator does what the device does: at a
mid-circuit measurement it samples the qubit, collapses the state to the branch it
drew, records the classical bit, and only then decides whether the conditional
gate fires. Each shot is one trajectory, and the answer is a histogram over shots.

That is the mechanism the chapter is about. A simulator that measured everything
at the end would produce the same histogram for a circuit with feed-forward and one
without, which is how a broken dynamic circuit passes a test suite.
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .circuit import Circuit, Op, qubits

State = np.ndarray


def zero(n: int) -> State:
    state = np.zeros(2 ** n, dtype=complex)
    state[0] = 1.0
    return state


def apply_gate(state: State, gate: str, wires: Sequence[int]) -> State:
    n = int(round(math.log2(state.shape[0])))
    out = state.copy()
    if gate == "x":
        wire = wires[0]
        for index in range(state.shape[0]):
            out[index ^ (1 << wire)] = state[index]
        return out
    if gate == "h":
        wire, step = wires[0], 1 << wires[0]
        for base in range(0, state.shape[0], step << 1):
            for offset in range(step):
                a, b = base + offset, base + offset + step
                out[a], out[b] = (state[a] + state[b]) / math.sqrt(2), (state[a] - state[b]) / math.sqrt(2)
        return out
    if gate == "cx":
        control, target = wires
        for index in range(state.shape[0]):
            if (index >> control) & 1:
                out[index ^ (1 << target)] = state[index]
        return out
    raise ValueError(f"unknown gate {gate!r} for this simulator")


def probability_of(state: State, wire: int, value: int) -> float:
    total = 0.0
    for index, amplitude in enumerate(state):
        if (index >> wire) & 1 == value:
            total += float(abs(amplitude) ** 2)
    return total


def collapse(state: State, wire: int, value: int) -> State:
    out = state.copy()
    mask = 1 << wire
    for index in range(out.shape[0]):
        if (index & mask) != (value << wire):
            out[index] = 0.0
    norm = np.sqrt(np.sum(np.abs(out) ** 2))
    if norm < 1e-12:
        raise ValueError(f"collapsing wire {wire} to {value} removed every branch")
    return out / norm


def run_shot(ops: Circuit, n: int, rng: np.random.Generator) -> Tuple[State, List[int]]:
    """One trajectory: the final state and the classical register."""
    state = zero(n)
    register = [0] * 32
    for op in ops:
        name = op[0]
        if name in ("x", "h", "cx"):
            state = apply_gate(state, name, op[1])
        elif name == "measure":
            wire, bit = int(op[1][0]), int(op[2])
            value = 0 if rng.random() < probability_of(state, wire, 0) else 1
            state = collapse(state, wire, value)
            register[bit] = value
        elif name == "reset":
            wire = int(op[1][0])
            value = 0 if rng.random() < probability_of(state, wire, 0) else 1
            state = collapse(state, wire, value)
            if value == 1:
                state = apply_gate(state, "x", (wire,))
            register[wire] = 0
        elif name == "if":
            bit, expected = int(op[1][0]), int(op[1][1])
            if register[bit] == expected:
                state = _run_ops(state, n, op[2], register, rng)
        elif name == "ifreg":
            (low, high), expected = op[1]
            if register[low] + 2 * register[high] == expected:
                state = _run_ops(state, n, op[2], register, rng)
        else:
            raise ValueError(f"unknown operation {name!r}")
    return state, register


def _run_ops(state: State, n: int, ops: Circuit, register: List[int], rng: np.random.Generator) -> State:
    for op in ops:
        name = op[0]
        if name in ("x", "h", "cx"):
            state = apply_gate(state, name, op[1])
        elif name == "measure":
            wire, bit = int(op[1][0]), int(op[2])
            value = 0 if rng.random() < probability_of(state, wire, 0) else 1
            state = collapse(state, wire, value)
            register[bit] = value
        elif name == "if":
            if register[int(op[1][0])] == int(op[1][1]):
                state = _run_ops(state, n, op[2], register, rng)
        elif name == "ifreg":
            (low, high), expected = op[1]
            if register[low] + 2 * register[high] == expected:
                state = _run_ops(state, n, op[2], register, rng)
    return state


def sample(ops: Circuit, shots: int, seed: int = 0, data_bits: int = 3) -> Dict[str, int]:
    """The histogram of the data qubits, which are the low classical bits."""
    if shots < 1:
        raise ValueError(f"shots must be positive, got {shots}")
    n = qubits(ops)
    rng = np.random.default_rng(seed)
    counts: Dict[str, int] = {}
    for _ in range(shots):
        _, register = run_shot(ops, n, rng)
        key = "".join(str(register[bit]) for bit in reversed(range(data_bits)))
        counts[key] = counts.get(key, 0) + 1
    return counts


def histogram(ops: Circuit, shots: int, bits: Sequence[int], seed: int = 0) -> Dict[str, int]:
    """The joint histogram of the named classical bits, most significant first."""
    if shots < 1:
        raise ValueError(f"shots must be positive, got {shots}")
    if not bits:
        raise ValueError("a histogram needs at least one bit")
    n = qubits(ops)
    rng = np.random.default_rng(seed)
    counts: Dict[str, int] = {}
    for _ in range(shots):
        _, register = run_shot(ops, n, rng)
        key = "".join(str(register[bit]) for bit in bits)
        counts[key] = counts.get(key, 0) + 1
    return counts


def syndrome_histogram(ops: Circuit, shots: int, seed: int = 0, checks: int = 2, first_clbit: int = 3) -> Dict[str, int]:
    """How often each syndrome pattern was measured, which diagnoses the ancillas."""
    n = qubits(ops)
    rng = np.random.default_rng(seed)
    counts: Dict[str, int] = {}
    for _ in range(shots):
        _, register = run_shot(ops, n, rng)
        key = "".join(str(register[bit]) for bit in reversed(range(first_clbit, first_clbit + checks)))
        counts[key] = counts.get(key, 0) + 1
    return counts
