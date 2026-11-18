"""Chapter 1 harness: every claim in the prose, as an assertion.

Run: python3 chapters/chapter01/files/run_ex1.py
Prints "NN/NN checks passed" and exits non-zero on the first failure.
"""

from __future__ import annotations

import math
import sys

import numpy as np

from sampling import estimated_probability, sample_counts, sample_index, standard_error
from sdks import IMPLEMENTATIONS, compare
from state import (
    DEFAULT_TOL,
    StateError,
    StateVector,
    UnnormalizedState,
    hadamard,
    x_gate,
    z_gate,
)

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the object ---------------------------------------------------------
section("state vector")
zero = StateVector.zero()
one = StateVector.one()
check(len(zero) == 2, "a one-qubit state has two amplitudes")
check(np.allclose(zero.amplitudes, [1.0, 0.0]), "|0> is [1, 0]")
check(np.allclose(one.amplitudes, [0.0, 1.0]), "|1> is [0, 1]")
check(abs(zero.norm - 1.0) < DEFAULT_TOL, "|0> is normalized")
check(abs(one.norm - 1.0) < DEFAULT_TOL, "|1> is normalized")
check(np.allclose(zero.probabilities(), [1.0, 0.0]), "|0> measures 0 with certainty")
check(zero.labels() == ["|0>", "|1>"], "labels are the basis names")

for bad, why in [
    ([1.0], "one amplitude"),
    ([1.0, 0.0, 0.0], "three amplitudes"),
    ([np.nan, 0.0], "a NaN"),
    ([[1.0, 0.0]], "a nested list"),
]:
    try:
        StateVector(bad)
    except StateError:
        check(True, f"refused {why}")
    else:
        check(False, f"refused {why}")

# -- normalization ------------------------------------------------------
section("normalization")
raw = StateVector([1.0, 0.1])
check(abs(raw.norm - 1.01) < 1e-12, "an unnormalized state knows its own norm")
try:
    StateVector.from_amplitudes([1.0, 0.1])
except UnnormalizedState:
    check(True, "from_amplitudes refuses norm 1.01")
else:
    check(False, "from_amplitudes refuses norm 1.01")

repaired = raw.normalized()
check(abs(repaired.norm - 1.0) < DEFAULT_TOL, "normalized() restores norm one")
check(np.allclose(repaired.probabilities().sum(), 1.0), "probabilities sum to one after repair")
check(np.allclose(repaired.amplitudes, np.array([1.0, 0.1]) / math.sqrt(1.01)), "amplitudes scale by 1/sqrt(norm)")

try:
    StateVector([0.0, 0.0]).normalized()
except StateError:
    check(True, "the zero vector cannot be normalized")
else:
    check(False, "the zero vector cannot be normalized")

scaled = StateVector([2.0, 0.0]).normalized()
check(np.allclose(scaled.amplitudes, [1.0, 0.0]), "scaling does not change the physical state")

# -- measurement --------------------------------------------------------
section("measurement")
p = np.array([0.25, 0.75])
state = StateVector([np.sqrt(p[0]), np.sqrt(p[1])])
check(abs(state.chance(0) - 0.25) < 1e-12, "P(0) is |a_0|^2")
check(abs(state.chance(1) - 0.75) < 1e-12, "P(1) is |a_1|^2")
try:
    state.chance(2)
except StateError:
    check(True, "outcome 2 is refused on one qubit")
else:
    check(False, "outcome 2 is refused on one qubit")

counts = sample_counts(state, shots=10_000, seed=42)
check(sum(counts.values()) == 10_000, "counts add up to the shots")
check(abs(estimated_probability(counts, 1) - 0.75) < 0.02, "10k shots land within 2 points of 0.75")
check(counts["0"] + counts["1"] == 10_000, "only the two outcomes appear")

again = sample_counts(state, shots=10_000, seed=42)
check(counts == again, "the same seed gives the same counts")
other = sample_counts(state, shots=10_000, seed=43)
check(counts != other, "a different seed gives different counts")

for single_seed in range(20):
    draw = sample_index(state, np.random.default_rng(single_seed))
    check(draw in (0, 1), f"draw {single_seed} is an outcome")

try:
    sample_counts(state, shots=0)
except ValueError:
    check(True, "zero shots is refused")
else:
    check(False, "zero shots is refused")

deterministic = StateVector.zero()
check(sample_counts(deterministic, shots=100, seed=1) == {"0": 100, "1": 0}, "|0> always yields 0")

# -- error bars ---------------------------------------------------------
section("error bars")
se = standard_error(0.5, 100)
check(abs(se - 0.05) < 1e-12, "standard error of 0.5 at 100 shots is 0.05")
check(standard_error(0.5, 400) < standard_error(0.5, 100), "more shots shrink the error")
check(standard_error(0.0, 10) == 0.0, "a certain outcome has no binomial error")
try:
    standard_error(1.5, 10)
except ValueError:
    check(True, "p above one is refused")
else:
    check(False, "p above one is refused")

# -- phase --------------------------------------------------------------
section("phase")
superposed = hadamard(zero)
check(np.allclose(superposed.probabilities(), [0.5, 0.5]), "H|0> is an even split")
rotated = superposed.with_phase(1j)
check(np.allclose(rotated.probabilities(), superposed.probabilities()), "a global phase leaves p unchanged")
check(abs(rotated.inner(superposed) - (-1j)) < DEFAULT_TOL, "the inner product records the phase")
check(rotated != superposed, "the vectors differ even when p does not")
check(sample_counts(rotated, 500, seed=3) == sample_counts(superposed, 500, seed=3), "counts are unchanged by a global phase")

try:
    superposed.with_phase(2.0)
except StateError:
    check(True, "a phase of modulus 2 is refused")
else:
    check(False, "a phase of modulus 2 is refused")

# -- gates --------------------------------------------------------------
section("gates")
hh = hadamard(hadamard(zero))
check(np.allclose(hh.amplitudes, zero.amplitudes), "H twice is the identity on |0>")
hzh = hadamard(z_gate(hadamard(zero)))
check(np.allclose(hzh.amplitudes, one.amplitudes), "H Z H is X on |0>")
check(np.allclose(x_gate(zero).amplitudes, one.amplitudes), "X swaps the basis states")
check(np.allclose(z_gate(one).amplitudes, [0.0, -1.0]), "Z flips the sign of |1>")
check(np.allclose(z_gate(zero).amplitudes, zero.amplitudes), "Z leaves |0> alone")

check(np.allclose(hh.probabilities(), zero.probabilities()), "H H returns p to [1, 0]")
check(np.allclose(hzh.probabilities(), one.probabilities()), "H Z H returns p to [0, 1]")
check(sample_counts(hh, 200, seed=5) == {"0": 200, "1": 0}, "H H counts are all zero")
check(sample_counts(hzh, 200, seed=5) == {"0": 0, "1": 200}, "H Z H counts are all one")
check(hh == zero, "two states are equal when their amplitudes are equal")

# -- the SDKs -----------------------------------------------------------
section("four implementations")
amps = [np.sqrt(0.6), np.sqrt(0.4) * 1j]
rows = compare(amps)
check(len(rows) == 4, "four implementations ran")
for name, produced, distance in rows:
    check(distance < 1e-9, f"{name} reproduces the amplitudes")
    check(abs(np.sum(np.abs(produced) ** 2) - 1.0) < 1e-9, f"{name} holds a normalized state")
    check(np.allclose(np.abs(produced) ** 2, np.abs(np.array(amps)) ** 2, atol=1e-9), f"{name} agrees on p")

for name, fn in IMPLEMENTATIONS.items():
    produced = fn([1.0, 0.0])
    check(np.allclose(produced, [1.0, 0.0], atol=1e-9), f"{name} reproduces |0>")

# -- the wall -----------------------------------------------------------
section("the wall")
for n in (10, 20, 25, 30):
    bytes_needed = 2**n * 16
    check(bytes_needed == 16 * 2**n, f"{n} qubits need {bytes_needed} bytes at complex128")
check(2**30 * 16 == 16 * 1024**3, "30 qubits of amplitudes is exactly 16 GiB")
check(2**40 * 16 > 10**13, "40 qubits is beyond any single machine")

# -- report -------------------------------------------------------------
print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
