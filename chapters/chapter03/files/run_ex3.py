"""Chapter 3 harness: unitaries, depth, decomposition, compilation, profile.

Run: python3 chapters/chapter03/files/run_ex3.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from circuit import Circuit, H, S, T, X, gate_matrix, rotation
from compiler import BASIS_1Q, check_basis, compile_1q, compile_circuit, compiled_cost
from decompose import distance_up_to_phase, rebuild, zyz
from profile import (
    depth_where_prediction_crosses,
    load,
    predicted_error,
    summary,
    worst_two_qubit_error,
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


ROOT = Path(__file__).resolve().parents[3]

# -- the unitary -------------------------------------------------------
section("a circuit is a unitary")
bell = Circuit(2).add("h", 0).add("cx", 0, 1)
check(bell.gate_count() == 2, "the bell circuit has two gates")
check(bell.depth() == 2, "the bell circuit has depth two")
check(bell.is_unitary(), "the bell circuit is unitary")
check(bell.unitary().shape == (4, 4), "two wires give a 4x4 unitary")
check(np.allclose(np.eye(4), Circuit(2).unitary()), "an empty circuit is the identity")

swapped = Circuit(2).add("cx", 0, 1).add("h", 0)
check(not np.allclose(bell.unitary(), swapped.unitary()), "gate order changes the unitary")
check(abs(np.max(np.abs(bell.unitary() - swapped.unitary())) - np.sqrt(0.5)) < 1e-9,
      "the distance between the two orders is 0.707")

check(np.allclose(Circuit(2).add("x", 0).add("x", 0).unitary(), np.eye(4)), "X twice is the identity")
check(np.allclose(Circuit(1).add("h", 0).unitary(), H), "one H is the H matrix")

try:
    Circuit(2).add("cx", 1, 1)
except ValueError:
    check(True, "CX on the same wire twice is refused")
else:
    check(False, "CX on the same wire twice is refused")

try:
    Circuit(2).add("h", 2)
except ValueError:
    check(True, "a wire outside the circuit is refused")
else:
    check(False, "a wire outside the circuit is refused")

try:
    Circuit(2).add("rx", 0)
except ValueError:
    check(True, "a rotation without an angle is refused")
else:
    check(False, "a rotation without an angle is refused")

# -- depth ---------------------------------------------------------------
section("depth is layers, not gates")
sequential = Circuit(2).add("h", 0).add("x", 0).add("y", 0).add("z", 0)
parallel = Circuit(2).add("h", 0).add("x", 1).add("y", 0).add("z", 1)
check(sequential.gate_count() == parallel.gate_count() == 4, "both circuits have four gates")
check(sequential.depth() == 4, "four gates on one wire have depth four")
check(parallel.depth() == 2, "four gates on two wires have depth two")
check(len(parallel.layers()) == 2, "the parallel circuit has two layers")
check(len(parallel.layers()[0]) == 2, "the first layer holds two gates")
check([n for n, _, _ in parallel.layers()[0]] == ["h", "x"], "the first layer holds h and x")
check(bell.depth() == 2 and bell.gate_count() == 2, "the bell circuit packs one gate per layer")
check(Circuit(2).depth() == 0, "an empty circuit has depth zero")

two_qubit_layer = Circuit(2).add("cx", 0, 1).add("h", 0)
check(two_qubit_layer.depth() == 2, "a CX occupies both wires, so the next gate waits")
check(len(two_qubit_layer.layers()[0]) == 1, "the CX is alone in its layer")

# -- decomposition -------------------------------------------------------
section("three rotations are enough")
for name in ("h", "t", "s", "x", "y", "z", "sx"):
    alpha, theta, beta, phase = zyz(gate_matrix(name))
    error = np.max(np.abs(rebuild(alpha, theta, beta, phase) - gate_matrix(name)))
    check(error < 1e-12, f"{name} rebuilds from its ZYZ angles")

alpha, theta, beta, _ = zyz(T)
check(abs(alpha - np.pi / 4) < 1e-12, "T is a quarter-turn on the rz axis")
check(abs(theta) < 1e-12, "T needs no ry")
check(abs(beta) < 1e-12, "T needs one rz")

rng = np.random.default_rng(1)
worst = 0.0
for _ in range(20):
    u = np.linalg.qr(rng.normal(size=(2, 2)) + 1j * rng.normal(size=(2, 2)))[0]
    a, t, b, p = zyz(u)
    worst = max(worst, np.max(np.abs(rebuild(a, t, b, p) - u)))
check(worst < 1e-12, "twenty random unitaries rebuild below 1e-12")

try:
    zyz(np.array([[1, 0], [0, 2]]))
except ValueError:
    check(True, "a non-unitary matrix is refused")
else:
    check(False, "a non-unitary matrix is refused")

check(distance_up_to_phase(S, S) == 0.0, "a matrix is zero distance from itself")
check(distance_up_to_phase(S, S * 1j) < 1e-12, "a global phase is invisible")
check(distance_up_to_phase(S, np.eye(2)) > 0.5, "S and the identity are far apart")

# -- compilation ---------------------------------------------------------
section("compilation keeps the unitary and pays in depth")
cost = compiled_cost(bell)
check(cost["ops_before"] == 2 and cost["ops_after"] == 10, "the bell circuit goes from 2 to 10 gates")
check(cost["depth_before"] == 2 and cost["depth_after"] == 7, "and from depth 2 to depth 7")
check(abs(cost["depth_ratio"] - 3.5) < 1e-12, "the depth ratio is 3.5")
check(cost["distance"] < 1e-12, "compilation preserves the unitary")

compiled = compile_circuit(bell)
check(check_basis(compiled) == [], "the compiled bell uses only the basis")
check(set(n for n, _, _ in compiled.ops) <= set(BASIS_1Q) | {"cz"}, "only rz, ry and cz survive")

for name in ("h", "t", "s", "x"):
    single = Circuit(1).add(name, 0)
    compiled_single = compile_circuit(single)
    check(compiled_single.gate_count() == 3, f"{name} compiles to three rotations")
    check(distance_up_to_phase(single.unitary(), compiled_single.unitary()) < 1e-12,
          f"{name} keeps its unitary through compilation")

chain = Circuit(1).add("h", 0).add("t", 0).add("s", 0).add("x", 0).add("h", 0)
chain_cost = compiled_cost(chain)
check(chain_cost["ops_before"] == 5 and chain_cost["ops_after"] == 15, "five gates become fifteen")
check(chain_cost["depth_ratio"] == 3.0, "a one-wire chain triples its depth")

parallel_cost = compiled_cost(Circuit(2).add("h", 0).add("t", 1).add("x", 0).add("s", 1))
check(parallel_cost["depth_before"] == 2 and parallel_cost["depth_after"] == 6,
      "parallel gates keep some of their advantage")

check(compile_1q("t")[1][1] == 0.0, "T compiles to a zero ry")

# -- the profile ---------------------------------------------------------
section("what the device profile predicts")
device = load()
info = summary(device)
check(info["backend"] == "ibm_fez", "the profile is from ibm_fez")
check(info["qubits"] == 156, "the device has 156 qubits")
check("cz" in info["basis"] and "rz" in info["basis"], "the basis is the cz family")
check(abs(info["readout"] - 0.029296875) < 1e-12, "the recorded readout error is 0.0293")
check(len(info["two_qubit_errors"]) >= 3, "at least three two-qubit errors were captured")
check(abs(worst_two_qubit_error(device) - 0.009599078697140023) < 1e-12, "the worst CZ error is 0.0096")

low = predicted_error(device, two_qubit_gates=1, measured_qubits=2)
high = predicted_error(device, two_qubit_gates=20, measured_qubits=2)
check(0 < low < high < 1, "the prediction grows with the gate count")
check(abs(low - 0.0668) < 5e-4, "one CZ plus two readouts predicts 6.7%")
check(predicted_error(device, 0, 0) == 0.0, "no gates and no readout predict no error")

crossing = depth_where_prediction_crosses(device, 0.5)
check(60 <= crossing <= 70, "the prediction crosses 50% around depth 66")

try:
    depth_where_prediction_crosses(device, 1.5)
except ValueError:
    check(True, "a threshold above one is refused")
else:
    check(False, "a threshold above one is refused")

# -- the recorded run ----------------------------------------------------
section("the recorded run")
recorded = json.loads((ROOT / "runs/0001-ibm-fez-bell/result.json").read_text())
check(recorded["backend"] == "ibm_fez", "the run is from the same device as the profile")
check(recorded["circuit"]["logical_depth"] == 2, "two logical layers were written")
check(recorded["circuit"]["transpiled_depth"] == 8, "the device ran eight layers")
check(sum(recorded["counts"].values()) == 1024, "the counts add up to the shots")
observed = recorded["derived"]["p_anti_correlated"]
check(abs(observed - 0.0537) < 1e-4, "the anti-correlated fraction is 5.4%")
check(abs(observed - low) < 0.02, "the profile predicts the observed error within two points")
check(recorded["counts"]["00"] > 400 and recorded["counts"]["11"] > 400, "the two Bell outcomes dominate")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
