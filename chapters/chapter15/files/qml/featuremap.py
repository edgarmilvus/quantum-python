"""The ZZ feature map, and the statevector it produces.

One data point becomes one circuit. The map is the one from Havlicek et al.: a
Hadamard layer, a phase per feature, a phase per pair of features, and a second
Hadamard layer. The kernel between two points is the squared overlap of their two
states, which a device measures by running one circuit backwards into the other
and counting the shots that come back to all zeros.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import numpy as np

Point = Tuple[float, float]
Op = Tuple[str, Tuple[int, ...], float]
State = np.ndarray


def zero(n: int) -> State:
    if n < 1:
        raise ValueError(f"a register has at least one wire, got {n}")
    state = np.zeros(2 ** n, dtype=complex)
    state[0] = 1.0
    return state


def apply(state: State, gate: str, wires: Sequence[int], theta: float = 0.0) -> State:
    """Apply one gate in place-free style, with wire 0 the least significant bit."""
    n = int(round(math.log2(state.shape[0])))
    if 2 ** n != state.shape[0]:
        raise ValueError(f"{state.shape[0]} amplitudes is not a power of two")
    out = state.copy()
    if gate == "h":
        wire, step = wires[0], 1 << wires[0]
        for base in range(0, out.shape[0], step << 1):
            for offset in range(step):
                a, b = base + offset, base + offset + step
                out[a], out[b] = (state[a] + state[b]) / math.sqrt(2), (state[a] - state[b]) / math.sqrt(2)
        return out
    if gate == "rz":
        wire, step = wires[0], 1 << wires[0]
        for base in range(0, out.shape[0], step << 1):
            for offset in range(step):
                a, b = base + offset, base + offset + step
                out[a] = np.exp(-0.5j * theta) * state[a]
                out[b] = np.exp(0.5j * theta) * state[b]
        return out
    if gate == "rzz":
        i, j = wires
        for index in range(out.shape[0]):
            parity = ((index >> i) & 1) ^ ((index >> j) & 1)
            out[index] = np.exp(-0.5j * theta * (1 if parity == 0 else -1)) * state[index]
        return out
    raise ValueError(f"unknown gate {gate!r}")


def ops_for(point: Point, n: int = 2, reps: int = 1) -> List[Op]:
    """The gate list for one point: one Hadamard layer, then `reps` phase layers.

    This is Qiskit's ZZFeatureMap, written out: H on every wire once, then a phase
    per feature and a phase per pair, repeated. More repetitions sharpen the kernel,
    which is the same trade QAOA's p makes in the other direction.
    """
    if len(point) != n:
        raise ValueError(f"{len(point)} features on {n} wires")
    if reps < 1:
        raise ValueError(f"reps must be at least 1, got {reps}")
    ops: List[Op] = [("h", (wire,), 0.0) for wire in range(n)]
    for _ in range(reps):
        for wire, value in enumerate(point):
            ops.append(("rz", (wire,), -2 * value))
        for i in range(n):
            for j in range(i + 1, n):
                phi = (math.pi - point[i]) * (math.pi - point[j])
                ops.append(("rzz", (i, j), -2 * phi))
    return ops


def inverse(ops: Sequence[Op]) -> List[Op]:
    """The adjoint, for the overlap circuit: reverse the order and negate angles."""
    out: List[Op] = []
    for gate, wires, theta in reversed(ops):
        out.append((gate, tuple(wires), -theta if gate != "h" else 0.0))
    return out


def state_for(point: Point, n: int = 2, reps: int = 1) -> State:
    state = zero(n)
    for gate, wires, theta in ops_for(point, n, reps):
        state = apply(state, gate, wires, theta)
    return state


def overlap_ops(a: Point, b: Point, n: int = 2, reps: int = 1) -> List[Op]:
    """U(b)-dagger U(a): all-zero probability is the squared overlap."""
    return ops_for(a, n, reps) + inverse(ops_for(b, n, reps))


def fidelity(state_a: State, state_b: State) -> float:
    if state_a.shape != state_b.shape:
        raise ValueError(f"{state_a.shape} and {state_b.shape} do not match")
    overlap = np.vdot(state_b, state_a)
    return float(abs(overlap) ** 2)


def norm(state: State) -> float:
    return float(np.sqrt(np.sum(np.abs(state) ** 2)))
