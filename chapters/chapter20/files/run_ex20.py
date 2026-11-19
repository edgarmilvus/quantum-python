"""Chapter 20 harness: the protocol, the frame, the record and the fidelity.

Run: python3 chapters/chapter20/files/run_ex20.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector

from teleport import Calibration, Prepared, bloch, calibration, distance, fidelity, postselect, run, teleport
from teleport.circuit import BASES, before_measurement

ROOT = Path(__file__).resolve().parents[3]
checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the state ----------------------------------------------------------
section("the state")
prepared = Prepared(math.pi / 3, math.pi / 4)
x, y, z = prepared.bloch()
check(abs(x - 0.6124) < 0.001, "the bloch x is sin(theta) cos(phi)")
check(abs(y - 0.6124) < 0.001, "the bloch y is sin(theta) sin(phi)")
check(abs(z - 0.5) < 0.001, "the bloch z is cos(theta)")
check(abs(fidelity(prepared, prepared.bloch()) - 1.0) < 1e-9, "a state is perfectly faithful to itself")
check(abs(fidelity(prepared, (0.0, 0.0, 0.0)) - 0.5) < 1e-9, "the centre is a coin flip")
check(abs(fidelity(prepared, (-x, -y, -z))) < 1e-9, "the opposite vector is orthogonal")
check(abs(distance(prepared, prepared.bloch())) < 1e-12, "the distance to itself is zero")
check(Prepared(0.0, 0.0).bloch() == (0.0, 0.0, 1.0), "theta zero is the north pole")

for bad in ((4.0, 0.0), (-0.1, 0.0), (1.0, -0.5), (1.0, 7.0)):
    try:
        Prepared(*bad)
    except ValueError:
        check(True, f"{bad} is refused")
    else:
        check(False, f"{bad} is refused")

# -- the circuit --------------------------------------------------------
section("the circuit")
one = teleport(prepared, "Z", dynamic=True)
check(one.num_qubits == 3 and one.num_clbits == 3, "three qubits and three classical bits")
check(one.count_ops().get("if_else", 0) == 2, "two conditional corrections")
check(teleport(prepared, "Z", dynamic=False).count_ops().get("if_else", 0) == 0, "the postselect version has none")
check(teleport(prepared, "Z", dynamic=False, correct=False).count_ops().get("if_else", 0) == 0, "and neither does the control")
check(len({basis: teleport(prepared, basis) for basis in BASES}) == 3, "three bases, three circuits")
check(len(calibration()) == 4, "four calibration circuits")
check(len(before_measurement(prepared).cregs) == 0, "the pre-measurement circuit has no register")

try:
    teleport(prepared, "W")
except ValueError:
    check(True, "an unknown basis is refused")
else:
    check(False, "an unknown basis is refused")

# -- the branches -------------------------------------------------------
section("the branches")
psi_circuit = QuantumCircuit(1)
psi_circuit.u(prepared.theta, prepared.phi, 0.0, 0)
psi = Statevector.from_int(0, 2).evolve(psi_circuit).data
state = Statevector(before_measurement(prepared)).data
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
for m0 in (0, 1):
    for m1 in (0, 1):
        branch = np.zeros(8, dtype=complex)
        for index, amplitude in enumerate(state):
            if (index & 1) == m0 and ((index >> 1) & 1) == m1:
                branch[index] = amplitude
        branch /= np.linalg.norm(branch)
        base = m0 | (m1 << 1)
        received = np.array([branch[base], branch[base + 4]])
        received /= np.linalg.norm(received)
        corrected = received.copy()
        if m0:
            corrected = Z @ corrected
        if m1:
            corrected = X @ corrected
        check(abs(abs(np.vdot(psi, corrected)) ** 2 - 1.0) < 1e-9, f"branch {m0}{m1} corrects to the state")

# -- the frame ----------------------------------------------------------
section("the frame")
counts = {}
for basis in BASES:
    circuit = before_measurement(prepared)
    if basis == "X":
        circuit.h(2)
    elif basis == "Y":
        circuit.sdg(2)
        circuit.h(2)
    probabilities = Statevector(circuit).probabilities_dict()
    counts[basis] = {key.replace(" ", ""): int(round(p * 100_000)) for key, p in probabilities.items()}

exact = bloch(counts, 0.0, 0.0, postselected=True, correct=True)
check(abs(fidelity(prepared, exact) - 1.0) < 1e-3, "the frame returns the state exactly")
check(abs(fidelity(prepared, bloch(counts, 0.0, 0.0, postselected=True, correct=False)) - 0.5) < 1e-3,
      "and without it the state is a coin flip")

histogram = {"101": 40, "100": 10, "001": 30, "000": 20}
flipped = postselect(histogram, "X", correct=True)
check(flipped["1"] == 40, "the X basis flips on m0")
check(postselect(histogram, "Z", correct=True)["1"] == 50, "the Z basis flips on m1")
check(postselect(histogram, "Y", correct=True)["1"] == 40, "the Y basis flips on both")
check(postselect(histogram, "X", correct=False)["1"] == 50, "the control flips nothing")

# -- the record ---------------------------------------------------------
section("the record")
record = json.loads((ROOT / "runs/chapter20/0042-teleport-pi3-pi4-2048-ibm/result.json").read_text())
check(record["shots"] == 2048, "2,048 shots")
check(record["transpiled_depth"] == 18, "depth 18 after transpilation")
check(record["backend"] == "ibm_kingston", "the backend is ibm_kingston")
check(record["job_id"].startswith("dburv"), "the job id is recorded")
check(len(record["calibration"]) == 4, "four calibration circuits")
check(set(record["dynamic"]["counts"]) == {"X", "Y", "Z"}, "three bases for the dynamic run")
check(set(record["postselect"]["counts"]) == {"X", "Y", "Z"}, "three for the postselect run")
check(set(record["uncorrected"]["counts"]) == {"X", "Y", "Z"}, "three for the control")
check(sum(record["dynamic"]["counts"]["Z"].values()) == 2048, "a basis is 2,048 shots")

rates = Calibration.from_counts(record["calibration"])
check(abs(rates.p_one_given_zero - 0.0020) < 0.002, "the receiving qubit misreads a zero rarely")
check(abs(rates.p_zero_given_one - 0.0293) < 0.004, "and a one about three percent of the time")

# -- the fidelity -------------------------------------------------------
section("the fidelity")
dynamic = run(record, "dynamic")
post = run(record, "postselect")
control = run(record, "uncorrected")
check(abs(dynamic.fidelity - 0.9558) < 0.005, "the dynamic circuit teleports at 0.9558")
check(abs(post.fidelity - 0.9499) < 0.005, "the postselect version at 0.9499")
check(control.fidelity < 0.55, "the control sits near a half")
check(dynamic.fidelity - control.fidelity > 0.40, "the correction is worth more than forty points")
check(abs(dynamic.fidelity - post.fidelity) < 0.02, "the two corrected runs agree within two points")
check(dynamic.verdict == "the state arrived", "and the verdict says so")
check(control.verdict == "not teleported", "the control is not teleported")
check(dynamic.distance < 0.15, "the bloch vector is within 0.15 of the ideal")

try:
    run(record, "nonsense")
except KeyError:
    check(True, "an unknown kind is refused")
else:
    check(False, "an unknown kind is refused")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
