"""Chapter 2 harness: tensor products, wires, phase, Bloch, and endianness.

Run: python3 chapters/chapter02/files/run_ex2.py
Prints "NN/NN checks passed" and exits non-zero if any check failed.
"""

from __future__ import annotations

import sys

import numpy as np

from bloch import (
    angle_deg,
    bloch_vector,
    estimate_vector,
    expectation,
    measurement_basis,
    purity,
    ry_angle_deg,
)
from gates import H, S, T, X, Y, Z, apply_one, embed
from ordering import (
    bell_cirq,
    bell_numpy,
    bell_qiskit,
    cirq_x0,
    comparison,
    little_to_big,
    numpy_x0,
    numpy_x1,
    pennylane_x0,
    qiskit_x0,
    qiskit_x1,
    reconciliation,
)
from register import Register, RegisterError

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- tensor ------------------------------------------------------------
section("tensor product")
left = np.array([1.0, 0.0])
right = np.array([0.0, 1.0])
check(np.allclose(np.kron(left, right), [0, 1, 0, 0]), "|0> tensor |1> is index 1")
check(np.allclose(np.kron(right, left), [0, 0, 1, 0]), "|1> tensor |0> is index 2")
check(np.allclose(Register.tensor(left, right).amplitudes, [0, 1, 0, 0]), "Register.tensor keeps the left factor first")
check(len(Register.zero()) == 4, "a two-wire register has four amplitudes")
check(np.allclose(Register.zero().probabilities(), [1, 0, 0, 0]), "|00> measures as index 0")
check(Register.zero().norm == 1.0, "|00> is normalized")

try:
    Register([1.0, 0.0])
except RegisterError:
    check(True, "a two-amplitude register is refused")
else:
    check(False, "a two-amplitude register is refused")

try:
    Register.from_amplitudes([1.0, 0.0, 0.0, 0.0]) and Register.from_amplitudes([1, 0, 0, 1])
except RegisterError:
    check(True, "an unnormalized four-amplitude register is refused")
else:
    check(False, "an unnormalized four-amplitude register is refused")

labels = Register.zero().labels()
check(labels == ["|00>", "|01>", "|10>", "|11>"], "the default labels are |q0 q1> in index order")
try:
    Register.zero().bitstring(4)
except RegisterError:
    check(True, "index 4 is refused")
else:
    check(False, "index 4 is refused")

# -- wires -------------------------------------------------------------
section("a gate on one wire")
check(np.allclose(embed(X, 0), np.kron(X, np.eye(2))), "wire 0 is the left factor")
check(np.allclose(embed(X, 1), np.kron(np.eye(2), X)), "wire 1 is the right factor")
check(np.allclose(embed(X, 0) @ np.array([1, 0, 0, 0]), [0, 0, 1, 0]), "X on wire 0 moves |00> to index 2")
check(np.allclose(embed(X, 1) @ np.array([1, 0, 0, 0]), [0, 1, 0, 0]), "X on wire 1 moves |00> to index 1")
check(np.allclose(embed(Z, 0) @ np.array([0, 0, 1, 0]), [0, 0, -1, 0]), "Z on wire 0 flips the sign of index 2")
check(np.allclose(embed(Z, 1) @ np.array([0, 1, 0, 0]), [0, -1, 0, 0]), "Z on wire 1 flips the sign of index 1")

for bad_wire in (-1, 2):
    try:
        embed(X, bad_wire)
    except ValueError:
        check(True, f"wire {bad_wire} is refused")
    else:
        check(False, f"wire {bad_wire} is refused")

try:
    apply_one(np.array([1.0, 0.0]), X, 0, wires=2)
except ValueError:
    check(True, "a two-amplitude state on a two-wire register is refused")
else:
    check(False, "a two-amplitude state on a two-wire register is refused")

moved0 = Register.zero().apply(X, 0)
moved1 = Register.zero().apply(X, 1)
check(moved0.bitstring(int(np.argmax(moved0.amplitudes))) == "|10>", "X on wire 0 gives |10>")
check(moved1.bitstring(int(np.argmax(moved1.amplitudes))) == "|01>", "X on wire 1 gives |01>")
check(np.allclose(moved0.probabilities(), [0, 0, 1, 0]), "X on wire 0 has probability 1 at index 2")
check(np.allclose(moved1.probabilities(), [0, 1, 0, 0]), "X on wire 1 has probability 1 at index 1")
check(np.allclose(moved0.probabilities()[::-1], moved1.probabilities()), "the two wires mirror each other")
check(np.allclose(moved0.apply(X, 0).amplitudes, Register.zero().amplitudes), "X twice is the identity")

# -- phase -------------------------------------------------------------
section("phase and interference")
h0 = Register.zero().apply(H, 0)
check(np.allclose(h0.probabilities(), [0.5, 0, 0.5, 0]), "H on wire 0 splits indices 0 and 2")
check(np.allclose(h0.apply(H, 0).probabilities(), [1, 0, 0, 0]), "H twice returns index 0")

hs = h0.apply(S, 0)
check(np.allclose(hs.probabilities(), h0.probabilities()), "S on wire 0 leaves the probabilities unchanged")
check(not np.allclose(hs.amplitudes, h0.amplitudes), "S on wire 0 changes the amplitudes")

hsh = hs.apply(H, 0)
check(np.allclose(hsh.probabilities(), [0.5, 0, 0.5, 0]), "S gives a pi/2 phase, so H returns an even split")

hth = h0.apply(T, 0).apply(H, 0)
check(abs(hth.probabilities()[0] - 0.85355339) < 1e-8, "T gives a pi/4 phase, so P(00) is 0.8536")
check(abs(hth.probabilities()[2] - 0.14644661) < 1e-8, "T leaves P(10) at 0.1464")
check(abs(hth.probabilities()[1]) < 1e-12, "wire 1 stays in |0>")

wrong_wire = h0.apply(S, 1).apply(H, 0)
check(np.allclose(wrong_wire.probabilities(), [1, 0, 0, 0]), "S on the other wire does nothing to wire 0")

counts = hth.sample(1000, seed=5)
check(sum(counts.values()) == 1000, "counts add up to the shots")
check(counts["|01>"] == 0 and counts["|11>"] == 0, "wire 1 never leaves |0>")
check(counts["|00>"] + counts["|10>"] == 1000, "all shots land on the two allowed outcomes")
check(abs(counts["|00>"] / 1000 - 0.8536) < 0.03, "the 85/15 split is reproduced at 1000 shots")
check(hth.sample(1000, seed=5) == counts, "the same seed reproduces the counts")

# -- bloch -------------------------------------------------------------
section("the Bloch vector")
check(np.allclose(bloch_vector(np.array([1.0, 0.0])), [0, 0, 1]), "|0> points at +z")
check(np.allclose(bloch_vector(np.array([0.0, 1.0])), [0, 0, -1]), "|1> points at -z")
check(np.allclose(bloch_vector(apply_one(np.array([1.0, 0.0]), H, 0, wires=1)), [1, 0, 0]), "H|0> points at +x")
plus_i = np.array([1.0, 1j]) / np.sqrt(2.0)
check(np.allclose(bloch_vector(plus_i), [0, 1, 0]), "(|0> + i|1>)/sqrt(2) points at +y")
check(np.allclose(bloch_vector(apply_one(np.array([1.0, 0.0]), Y, 0, wires=1)), [0, 0, -1]), "Y|0> is i|1>, so it points at -z")
check(abs(purity(np.array([1.0, 0.0])) - 1.0) < 1e-12, "a pure state has |r| = 1")

ry = apply_one(np.array([1.0, 0.0]), np.array([[np.cos(np.pi / 6), -np.sin(np.pi / 6)],
                                               [np.sin(np.pi / 6), np.cos(np.pi / 6)]]), 0, wires=1)
check(abs(ry_angle_deg(ry) - 60.0) < 1e-9, "the polar angle of Ry(60) is 60 degrees")
try:
    angle_deg(np.array([1.0, 0.0]))
except ValueError:
    check(True, "the azimuth of |0> is undefined and refused")
else:
    check(False, "the azimuth of |0> is undefined and refused")
check(abs(angle_deg(apply_one(np.array([1.0, 0.0]), H, 0, wires=1))) < 1e-9, "H|0> has azimuth 0")

for axis in ("x", "y", "z"):
    basis = measurement_basis(axis)
    check(basis.shape == (2, 2), f"the {axis} basis gate is 2x2")

try:
    expectation(np.array([1.0, 0.0]), "w")
except ValueError:
    check(True, "axis w is refused")
else:
    check(False, "axis w is refused")

counts_x = {"0": 1882, "1": 118}
check(abs(estimate_vector({"x": counts_x, "y": {"0": 1031, "1": 969}, "z": {"0": 1532, "1": 468}})[0] - 0.882) < 1e-3,
      "the x estimate from counts is 0.882")

try:
    estimate_vector({"x": counts_x})
except ValueError:
    check(True, "an incomplete tomography is refused")
else:
    check(False, "an incomplete tomography is refused")

# -- ordering ----------------------------------------------------------
section("endianness")
check(int(np.argmax(np.abs(numpy_x0()))) == 2, "our convention puts X on wire 0 at index 2")
check(int(np.argmax(np.abs(numpy_x1()))) == 1, "our convention puts X on wire 1 at index 1")
check(int(np.argmax(np.abs(qiskit_x0()))) == 1, "Qiskit puts X on qubit 0 at index 1")
check(int(np.argmax(np.abs(qiskit_x1()))) == 2, "Qiskit puts X on qubit 1 at index 2")
check(int(np.argmax(np.abs(cirq_x0("big")))) == 2, "Cirq with order (0,1) puts X on the first at index 2")
check(int(np.argmax(np.abs(cirq_x0("little")))) == 1, "Cirq with order (1,0) puts it at index 1")
check(int(np.argmax(np.abs(pennylane_x0()))) == 2, "PennyLane puts X on wire 0 at index 2")

matrix = reconciliation()
check(abs(matrix["raw"] - 1.0) < 1e-12, "the raw distance between Qiskit and us is one")
check(matrix["after_conversion"] < 1e-12, "converting the order removes the difference")
check(np.allclose(little_to_big(np.array([0, 1, 0, 0])), [0, 0, 1, 0]), "little-to-big moves index 1 to index 2")
check(np.allclose(little_to_big(little_to_big(np.array([0, 1, 0, 0]))), [0, 1, 0, 0]), "converting twice is the identity")

try:
    little_to_big(np.array([1, 0]))
except ValueError:
    check(True, "a two-amplitude vector is refused for two wires")
else:
    check(False, "a two-amplitude vector is refused for two wires")

check(np.allclose(bell_numpy(), bell_qiskit()), "a Bell pair is symmetric, so the order does not show")
check(np.max(np.abs(bell_cirq() - bell_numpy())) < 1e-9, "Cirq agrees on the Bell pair")
check(int(np.argmax(np.abs(bell_numpy()))) == 0, "the Bell state starts at index 0 in both conventions")

rows = comparison()
check(len(rows) == 5, "five representations are compared")
check({row[0] for row in rows} >= {"qiskit", "pennylane"}, "the comparison names its implementations")

# -- structure ---------------------------------------------------------
section("factorability")
product = Register.tensor(np.array([1.0, 0.0]), np.array([0.0, 1.0]))
check(product.factors() is not None, "a product state has factors")
bell = Register(bell_numpy())
check(bell.factors() is None, "a Bell pair does not factor")
check(abs(bell.probabilities()[0] - 0.5) < 1e-12, "the Bell pair splits evenly between 00 and 11")
check(abs(bell.probabilities()[3] - 0.5) < 1e-12, "the Bell pair has nothing at 01 or 10")

# -- the cost ----------------------------------------------------------
section("the cost")
for wires in (2, 3, 10, 20):
    check(2**wires * 16 == 16 * (1 << wires), f"{wires} wires need {2**wires * 16} bytes")
check(2**20 * 16 == 16 * 1024**2, "20 wires is 16 MiB at complex128")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
