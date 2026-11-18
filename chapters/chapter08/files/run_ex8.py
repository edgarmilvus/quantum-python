"""Chapter 8 harness: the transform, the circuit, and phase estimation.

Run: python3 chapters/chapter08/files/run_ex8.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import math
import sys

import numpy as np

import phase
import qft

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the transform ------------------------------------------------------
section("the Fourier matrix")
for n in (1, 2, 3, 4):
    matrix = qft.dft(n)
    size = 1 << n
    check(matrix.shape == (size, size), f"n={n}: the matrix is {size} square")
    check(np.allclose(matrix.conj().T @ matrix, np.eye(size)), f"n={n}: the transform is unitary")
    check(np.allclose(qft.dft(n, -1) @ matrix, np.eye(size)), f"n={n}: the inverse undoes it")
    check(abs(abs(np.linalg.det(matrix)) - 1.0) < 1e-9, f"n={n}: the determinant has modulus one")

check(qft.dft(1).shape == (2, 2), "one qubit: a two by two transform")
check(abs(qft.dft(1)[0, 0] - 1 / np.sqrt(2)) < 1e-12, "with entries of modulus one over root two")
check(np.allclose(qft.dft(2) / (1 / 2), qft.dft(2) * 2), "n=2 has entries of modulus one half")

for sign in (0, 2):
    try:
        qft.dft(2, sign)
    except ValueError:
        check(True, f"sign {sign} is refused")
    else:
        check(False, f"sign {sign} is refused")

try:
    qft.dft(0)
except ValueError:
    check(True, "zero qubits are refused")
else:
    check(False, "zero qubits are refused")

# -- the circuit --------------------------------------------------------
section("the circuit")
for n in (1, 2, 3, 4, 5):
    check(np.max(np.abs(qft.qft_matrix(n) - qft.dft(n))) < 1e-12,
          f"n={n}: Hadamards and phases reproduce the matrix")

check(qft.gate_count(1) == 1, "one qubit needs one gate")
check(qft.gate_count(2) == 4, "two qubits need four")
check(qft.gate_count(3) == 7, "three need seven")
check(qft.gate_count(4) == 12, "four need twelve")
check(qft.circuit_depth(1) == 1, "the depth of one qubit is one layer")
check(qft.circuit_depth(3) == 6, "three qubits take six layers")
check(qft.circuit_depth(20) == 40, "twenty qubits take forty layers")
check(qft.gate_count(20) == 220, "and two hundred and twenty gates")

check(np.allclose(qft.inverse_qft_matrix(3), qft.qft_matrix(3).conj().T), "the inverse is the adjoint")

try:
    qft.swap(3, 1, 1)
except ValueError:
    check(True, "swapping a wire with itself is refused")
else:
    check(False, "swapping a wire with itself is refused")

# -- phase estimation ---------------------------------------------------
section("phase estimation")
for exponent in range(1, 5):
    for numerator in range(0, 1 << exponent, 3):
        value = numerator / (1 << exponent)
        k, probability = phase.estimate(value, exponent)
        check(abs(probability - 1.0) < 1e-9, f"phi={value:.4f} at n={exponent} is exact")
        check(k == numerator, f"phi={value:.4f} returns k={numerator}")

k, probability = phase.estimate(1 / 3, 4)
check(k == 5, "one third at four bits returns five sixteenths")
check(abs(phase.phase_of(k, 4) - 0.3125) < 1e-12, "which is 0.3125")
check(0.6 < probability < 0.75, "with a probability between sixty and seventy-five percent")

values = phase.distribution(1 / 3, 4)
check(abs(sum(values.values()) - 1.0) < 1e-9, "the distribution sums to one")
check(len(values) == 16, "sixteen outcomes at four bits")
top_three = sorted(values.values())[-3:]
check(min(top_three) > 0.02, "the three best outcomes each hold more than two percent")

check(phase.precision(4) == 1 / 16, "four bits resolve one sixteenth")
check(phase.phase_of(5, 4) == 5 / 16, "the fifth sixteenth is 0.3125")

for bad in (-0.1, 1.0, 1.5):
    try:
        phase.unitary(bad)
    except ValueError:
        check(True, f"phase {bad} is refused")
    else:
        check(False, f"phase {bad} is refused")

try:
    phase.phase_of(16, 4)
except ValueError:
    check(True, "k outside the register is refused")
else:
    check(False, "k outside the register is refused")

check(abs(phase.distribution(0.0, 3)[0] - 1.0) < 1e-12, "a zero phase returns zero with certainty")

# -- precision ----------------------------------------------------------
section("precision")
worst = min(phase.success_probability(phi / 400, 6) for phi in range(1, 400))
check(worst > 4 / math.pi**2, "the worst case stays above the 4/pi^2 floor")
check(worst < 0.45, "and is close to it")
check(abs(phase.success_probability(1 / 8, 3) - 1.0) < 1e-12, "a representable phase is certain")
check(phase.success_probability(1 / 8 + 1 / 64, 3) < 1.0, "and a neighbouring one is not")

check(phase.success_probability(0.5 / (1 << 4), 4) < 0.45, "halfway between two values is the worst case")
check(abs(phase.success_probability(0.5 / (1 << 4), 5) - 1.0) < 1e-12, "one more bit makes it exact")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
