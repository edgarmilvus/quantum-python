"""Order finding as phase estimation on a permutation, and the classical post-processing.

Shor's algorithm has two halves. The quantum half finds the order r of a modulo N. The
classical half turns r into a factor with two gcds, and fails often enough that a real
implementation retries. This file is both halves, with the permutation written out.
"""

from __future__ import annotations

import cmath
import math
from fractions import Fraction
from typing import Dict, List, Optional, Tuple

import numpy as np



H2 = np.array([[1, 1], [1, -1]], dtype=np.complex128) / np.sqrt(2.0)
I2 = np.eye(2, dtype=np.complex128)


def dft(n: int, sign: int = -1) -> np.ndarray:
    """Chapter 8's transform, repeated here so this chapter stands alone."""
    if n < 1:
        raise ValueError(f"a transform needs at least one qubit, got {n}")
    size = 1 << n
    root = cmath.exp(sign * 2j * math.pi / size)
    return np.array(
        [[root ** (row * column) for column in range(size)] for row in range(size)]
    ) / math.sqrt(size)


def embed_one(gate: np.ndarray, wire: int, n: int) -> np.ndarray:
    factors = [I2] * n
    factors[wire] = gate
    matrix = factors[0]
    for factor in factors[1:]:
        matrix = np.kron(matrix, factor)
    return matrix


# -- the classical half -------------------------------------------------
def order_of(a: int, n: int, limit: int = 10_000) -> Optional[int]:
    """The smallest r with a^r = 1 (mod n), or None within the limit."""
    if n < 2:
        raise ValueError(f"modulus must be at least two, got {n}")
    if a % n in (0,):
        raise ValueError(f"{a} is a multiple of {n}")
    value = 1
    for r in range(1, limit + 1):
        value = (value * a) % n
        if value == 1:
            return r
    return None


def continued_fraction(k: int, n_bits: int, max_denominator: int) -> Fraction:
    """The best rational with a small denominator for k / 2^n_bits."""
    if n_bits < 1:
        raise ValueError(f"at least one bit, got {n_bits}")
    if not 0 <= k < (1 << n_bits):
        raise ValueError(f"k must be in [0, {1 << n_bits}), got {k}")
    value = Fraction(k, 1 << n_bits)
    limit = value.limit_denominator(max_denominator)
    return limit


def factors_from_order(a: int, n: int, r: int) -> Optional[Tuple[int, int]]:
    """Two gcds, with the three ways they fail."""
    if r % 2:
        return None
    half = pow(a, r // 2, n)
    if half == 1 or half == n - 1:
        return None
    left = math.gcd(half - 1, n)
    right = math.gcd(half + 1, n)
    if left in (1, n) or right in (1, n):
        return None
    return left, right


def shor(N: int, a: int) -> Dict[str, object]:
    """The classical pipeline for one choice of a."""
    if math.gcd(a, N) != 1:
        factor = math.gcd(a, N)
        return {"n": N, "a": a, "r": None, "factors": (factor, N // factor), "path": "gcd directly"}
    r = order_of(a, N)
    if r is None:
        return {"n": N, "a": a, "r": None, "factors": None, "path": "order not found"}
    factors = factors_from_order(a, N, r)
    if factors is None:
        return {"n": N, "a": a, "r": r, "factors": None, "path": "retry with another a"}
    return {"n": N, "a": a, "r": r, "factors": factors, "path": "gcd"}


def best_effort(N: int, candidates: List[int]) -> Dict[str, object]:
    """Try values of a until one factors N, and report how many were needed."""
    for position, a in enumerate(candidates, start=1):
        result = shor(N, a)
        if result["factors"]:
            result["attempts"] = position
            return result
    return {"n": N, "attempts": len(candidates), "factors": None, "path": "no candidate worked"}


# -- the quantum half ---------------------------------------------------
def multiplier_matrix(a: int, n: int, bits: int) -> np.ndarray:
    """The permutation |x> -> |a x mod n>, with the states at or above n left alone."""
    if bits < 1:
        raise ValueError(f"at least one bit, got {bits}")
    size = 1 << bits
    if n > size:
        raise ValueError(f"{n} does not fit in {bits} bits")
    if math.gcd(a, n) != 1:
        raise ValueError(f"{a} and {n} are not coprime")
    matrix = np.zeros((size, size), dtype=np.complex128)
    for x in range(size):
        target = (a * x) % n if x < n else x
        matrix[target, x] = 1.0
    return matrix


def power_matrix(matrix: np.ndarray, exponent: int) -> np.ndarray:
    if exponent < 0:
        raise ValueError(f"an exponent is non-negative, got {exponent}")
    if exponent == 0:
        return np.eye(matrix.shape[0], dtype=np.complex128)
    result = np.eye(matrix.shape[0], dtype=np.complex128)
    base = matrix
    while exponent:
        if exponent & 1:
            result = base @ result
        base = base @ base
        exponent >>= 1
    return result


def controlled_matrix(matrix: np.ndarray, control: int, total: int) -> np.ndarray:
    """Apply `matrix` on the low bits when the control bit is one."""
    size = matrix.shape[0]
    full = np.zeros((size * 2, size * 2), dtype=np.complex128)
    full[:size, :size] = np.eye(size)
    full[size:, size:] = matrix
    # The control is the most significant bit of the ancilla-plus-target index.
    if control == 0:
        return full
    raise ValueError("this helper only handles the top control bit")


def _hadamard_on_axis(values: np.ndarray, ancillas: int, wire: int) -> np.ndarray:
    """Apply H to one ancilla bit of a (ancilla, target) array, in place of a kron."""
    block = values.shape[1]
    shape = [2] * ancillas + [block]
    arr = values.reshape(shape)
    axis = ancillas - 1 - wire
    moved = np.moveaxis(arr, axis, 0)
    first, second = moved[0].copy(), moved[1].copy()
    moved[0] = (first + second) / np.sqrt(2.0)
    moved[1] = (first - second) / np.sqrt(2.0)
    return np.moveaxis(moved, 0, axis).reshape(-1, block)


def order_finding(a: int, n: int, bits: int, ancillas: int) -> Dict[int, float]:
    """Phase estimation on the multiplier, returning the distribution over k.

    The state is held as an (ancilla value, target value) array: the ancillas are the
    rows and the target the columns, which is what the >= n rule of the permutation
    expects.
    """
    if ancillas < 1:
        raise ValueError(f"at least one ancilla, got {ancillas}")
    target = multiplier_matrix(a, n, bits)
    block = 1 << bits
    state = np.zeros((1 << ancillas, block), dtype=np.complex128)
    state[0, 1] = 1.0  # ancillas at zero, target at one

    for wire in range(ancillas):
        state = _hadamard_on_axis(state, ancillas, wire)

    for wire in range(ancillas):
        power = ancillas - 1 - wire
        step = power_matrix(target, 2 ** power)
        mask = 1 << (ancillas - 1 - wire)
        selected = np.array([value for value in range(1 << ancillas) if value & mask])
        # One matrix product for every selected row, not one per row.
        state[selected] = (step @ state[selected].T).T

    # Inverse transform along the ancilla axis, one matrix product instead of a kron.
    transformed = dft(ancillas, sign=-1) @ state
    probabilities = np.abs(transformed) ** 2
    return {k: float(probabilities[k].sum()) for k in range(1 << ancillas)}


def recover_order(k: int, ancillas: int, n: int) -> int:
    """Turn a measured phase into a candidate order, using continued fractions."""
    fraction = continued_fraction(k, ancillas, max_denominator=n)
    return fraction.denominator


def attempt(a: int, n: int, k: int, ancillas: int) -> Dict[str, object]:
    """One measured k, through continued fractions and two gcds."""
    r = recover_order(k, ancillas, n)
    if r in (1,):
        return {"k": k, "r": r, "factors": None, "path": "r is one"}
    factors = factors_from_order(a, n, r)
    return {"k": k, "r": r, "factors": factors, "path": "gcd" if factors else "retry"}


MAX_BITS = 20


def quantum_success(a: int, n: int, bits: int, ancillas: int) -> Dict[str, float]:
    """The probability that a single run yields the factors.

    The state has 2^(bits + ancillas) amplitudes, so the simulation refuses anything past
    twenty qubits rather than allocating it.
    """
    if bits + ancillas > MAX_BITS:
        raise ValueError(
            f"{bits + ancillas} qubits is beyond the {MAX_BITS}-qubit simulation limit; "
            f"use circuit_resources for the count"
        )
    values = order_finding(a, n, bits, ancillas)
    good = 0.0
    for k, probability in values.items():
        if attempt(a, n, k, ancillas)["factors"]:
            good += probability
    return {"probability": good, "outcomes": float(len([p for p in values.values() if p > 1e-12]))}


def circuit_resources(n: int) -> Dict[str, int]:
    """The textbook resource count for this n, not for a real key."""
    bits = max(1, math.ceil(math.log2(n + 1)))
    ancillas = 2 * bits
    return {
        "n": n,
        "bits": bits,
        "ancillas": ancillas,
        "qubits": bits + ancillas,
        "multiplications": ancillas * (ancillas + 1) // 2,
    }
