"""A statevector and the four gates QAOA needs.

Four qubits is 16 complex amplitudes and ten qubits is 1024, so a plain numpy
array is the right container: the chapter never simulates a circuit large enough
to need a sparse representation, and a dense vector makes the amplitude table
readable when a reader wants to see why an angle is optimal.

The convention is wire 0 as the least significant bit, the same as every
recorded run in this book.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

State = np.ndarray


def zero(n: int) -> State:
    """|0...0>, as 2^n amplitudes."""
    if n < 1:
        raise ValueError(f"a register has at least one wire, got {n}")
    state = np.zeros(2 ** n, dtype=complex)
    state[0] = 1.0
    return state


def _check(state: State, wire: int) -> int:
    n = int(round(np.log2(state.shape[0])))
    if 2 ** n != state.shape[0]:
        raise ValueError(f"{state.shape[0]} amplitudes is not a power of two")
    if not 0 <= wire < n:
        raise ValueError(f"wire {wire} is outside 0..{n - 1}")
    return n


def h(state: State, wire: int) -> State:
    _check(state, wire)
    out = state.copy()
    step = 1 << wire
    for base in range(0, state.shape[0], step << 1):
        for offset in range(step):
            a, b = base + offset, base + offset + step
            out[a], out[b] = (state[a] + state[b]) / np.sqrt(2), (state[a] - state[b]) / np.sqrt(2)
    return out


def rx(state: State, wire: int, theta: float) -> State:
    _check(state, wire)
    out = state.copy()
    step = 1 << wire
    cos, sin = np.cos(theta / 2), np.sin(theta / 2)
    for base in range(0, state.shape[0], step << 1):
        for offset in range(step):
            a, b = base + offset, base + offset + step
            out[a] = cos * state[a] - 1j * sin * state[b]
            out[b] = cos * state[b] - 1j * sin * state[a]
    return out


def rz(state: State, wire: int, theta: float) -> State:
    _check(state, wire)
    out = state.copy()
    step = 1 << wire
    for base in range(0, state.shape[0], step << 1):
        for offset in range(step):
            a, b = base + offset, base + offset + step
            out[a] = np.exp(-1j * theta / 2) * state[a]
            out[b] = np.exp(1j * theta / 2) * state[b]
    return out


def rzz(state: State, i: int, j: int, theta: float) -> State:
    """e^{-i theta Z_i Z_j / 2}, applied as a phase on the four parity classes."""
    _check(state, i)
    _check(state, j)
    if i == j:
        raise ValueError(f"RZZ needs two wires, got {i} twice")
    out = state.copy()
    for index in range(state.shape[0]):
        parity = ((index >> i) & 1) ^ ((index >> j) & 1)
        out[index] = np.exp(-0.5j * theta * (1 if parity == 0 else -1)) * state[index]
    return out


def probabilities(state: State) -> np.ndarray:
    values = np.abs(state) ** 2
    return values / values.sum()


def sample(state: State, shots: int, rng: np.random.Generator) -> Dict[int, int]:
    """Counts keyed by integer bitmask, bit i = wire i."""
    if shots <= 0:
        raise ValueError(f"shots must be positive, got {shots}")
    draws = rng.multinomial(shots, probabilities(state))
    return {index: int(count) for index, count in enumerate(draws) if count}


def labels(n: int) -> List[str]:
    return [format(index, f"0{n}b") for index in range(2 ** n)]


def bitstring(state: State, index: int) -> str:
    n = int(round(np.log2(state.shape[0])))
    if not 0 <= index < state.shape[0]:
        raise ValueError(f"{index} is not an outcome of {n} wires")
    return format(index, f"0{n}b")


def norm(state: State) -> float:
    return float(np.sqrt(np.sum(np.abs(state) ** 2)))
