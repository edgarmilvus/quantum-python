"""Chapter 19 harness: the task, the estimate, the correction, the report.

Run: python3 chapters/chapter19/files/run_ex19.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipe import estimate, run, spec

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the task -----------------------------------------------------------
section("the task")
task = spec.Task(name="bv-1011", qubits=4, shots=2048, provider="ibm", budget_usd=5.0)
check(task.circuits == 6, "a four-qubit task needs six circuits")
check(task.ideal() == {"1011": 1.0}, "the ideal is the secret")
check(len(spec.bv_ops("1011")) > 6, "the gate list has the Hadamards and the CNOTs")
check(spec.bv_ops("1011")[0] == ("x", (4,)), "the ancilla is put in |1> first")

for bad in (
    dict(name="", qubits=4, shots=2048, provider="ibm"),
    dict(name="x", qubits=1, shots=2048, provider="ibm"),
    dict(name="x", qubits=4, shots=0, provider="ibm"),
    dict(name="x", qubits=4, shots=2048, provider="nonsense"),
    dict(name="x", qubits=4, shots=2048, provider="ibm", secret="101"),
    dict(name="x", qubits=4, shots=2048, provider="ibm", secret="10x1"),
    dict(name="x", qubits=4, shots=2048, provider="ibm", budget_usd=-1),
):
    try:
        spec.Task(**bad)
    except ValueError:
        check(True, f"{bad} is refused")
    else:
        check(False, f"{bad} is refused")

# -- the estimate -------------------------------------------------------
section("the estimate")
free = estimate.estimate(task)
check(free.allowed, "the IBM task fits a five-dollar budget")
check(free.usd == 0.0, "because the open plan bills runtime")
check(free.circuits == 6 and free.shots == 2048, "six circuits at 2,048 shots")

ionq = spec.Task(**{**task.__dict__, "provider": "ionq"})
priced = estimate.estimate(ionq)
check(not priced.allowed, "the IonQ task is refused")
check(abs(priced.usd - 984.84) < 1.0, "at 984.84 dollars")
check("over the 5.00 budget" in priced.reason, "and the reason names the budget")

braket = spec.Task(**{**task.__dict__, "provider": "braket-iqm"})
check(abs(estimate.estimate(braket).usd - 21.46) < 0.2, "Braket's cheapest device is 21.46")

check(estimate.cheapest(task) == "local", "the cheapest provider is the local one")
check(estimate.price("ibm", 6, 2048) == 0.0, "IBM prices at zero per job")
check(abs(estimate.price("ionq", 1, 1000) - 80.3) < 0.1, "and IonQ at 0.30 plus 0.08 a shot")

for bad in (0, -1):
    try:
        estimate.price("ionq", bad, 1024)
    except ValueError:
        check(True, f"{bad} circuits is refused")
    else:
        check(False, f"{bad} circuits is refused")

check(estimate.estimate(task, key_present=False).allowed is False, "a missing key refuses the task")

# -- the readout --------------------------------------------------------
section("the readout")
record = run.load("0039-ibm-fez-pipeline")
model = run.readout(record)
check(len(model.p_one_given_zero) == 4, "four qubits in the model")
check(abs(model.p_one_given_zero[3] - 0.0488) < 0.01, "qubit 3 misreads a zero 4.9% of the time")
check(model.p_one_given_zero[3] > model.p_one_given_zero[0], "which is the worst of the four")
check(abs(float(np.linalg.det(model.matrix())) - 0.236) < 0.05, "the 16 by 16 matrix has a workable determinant")
check(float(np.linalg.cond(model.matrix())) < 2.0, "and an inverse that does not amplify")

corrected = run.correct(record["counts"], model)
check(abs(corrected["1011"] - 0.988) < 0.005, "the corrected peak is 0.988")
raw_share = record["counts"]["1011"] / sum(record["counts"].values())
check(abs(raw_share - 0.9551) < 0.005, "the raw peak was 0.955")
check(corrected["1011"] > raw_share, "so the correction improves it")

transposed = np.clip(np.array([corrected[key] for key in sorted(corrected)]), 0, None)
check(abs(sum(transposed) - 1.0) < 1e-9, "the corrected distribution sums to one")

try:
    run.correct({}, model)
except ValueError:
    check(True, "an empty histogram is refused")
else:
    check(False, "an empty histogram is refused")

try:
    run.readout({"counts": {}})
except ValueError:
    check(True, "a record with no calibration is refused")
else:
    check(False, "a record with no calibration is refused")

# -- the report ---------------------------------------------------------
section("the report")
report = run.run(record, task, seconds=4.0, usd=0.0)
check(report.ok, "the secret is recovered")
check(report.corrected_top == "1011", "at the right outcome")
check(report.raw_top == "1011", "and the raw peak agreed")
check(report.shots == 2048, "with the recorded shot count")
check("recovered" in report.report(), "the text says so")

wrong = spec.Task(**{**task.__dict__, "secret": "0110"})
try:
    run.run(record, wrong)
except ValueError:
    check(True, "a record with another secret is refused")
else:
    check(False, "a record with another secret is refused")

key, share = run.top({"00": 0.2, "11": 0.8})
check(key == "11" and abs(share - 0.8) < 1e-12, "the top is the largest entry")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
