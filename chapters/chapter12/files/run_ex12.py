"""Chapter 12 harness: channels, the device model, mitigation, and its limits.

Run: python3 chapters/chapter12/files/run_ex12.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from noise import channels, confusion, device, fit, simulate, states, zne

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- states -------------------------------------------------------------
section("density matrices")
zero = states.zero(2)
check(zero.shape == (4, 4), "two wires make a 4x4 matrix")
check(abs(np.trace(zero) - 1) < 1e-12, "a state has unit trace")
check(states.purity(zero) == 1.0, "a pure state has purity one")

bell = states.apply(zero, states._gate("h"), (0,), 2)
bell = states.apply(bell, states._gate("cx"), (0, 1), 2)
probabilities = states.probabilities(bell)
check(abs(probabilities[0] - 0.5) < 1e-12 and abs(probabilities[3] - 0.5) < 1e-12, "the Bell pair is half 00 and half 11")
check(abs(states.coherence(bell, 0, 3) - 0.5) < 1e-12, "and its coherence is a half")
check(abs(states.purity(bell) - 1.0) < 1e-12, "it is pure")

flipped = states.apply(states.ket(2, 1), states._gate("cx"), (0, 1), 2)
check(int(np.argmax(np.real(np.diag(flipped)))) == 3, "CX(0,1) takes 01 to 11, wire 0 as the control")
check(states.labels(2) == ["00", "01", "10", "11"], "labels count in Qiskit order")

for bad in (0, -1):
    try:
        states.zero(bad)
    except ValueError:
        check(True, f"{bad} wires is refused")
    else:
        check(False, f"{bad} wires is refused")

try:
    states.apply(zero, states._gate("x"), (2,), 2)
except ValueError:
    check(True, "a wire outside the register is refused")
else:
    check(False, "a wire outside the register is refused")

# -- channels -----------------------------------------------------------
section("the three channels")
for p in (0.0, 0.1, 0.5):
    check(channels.check_complete(channels.depolarizing(p)) < 1e-12, f"depolarizing {p} is trace preserving")
for gamma in (0.0, 0.3, 0.9):
    check(channels.check_complete(channels.amplitude_damping(gamma)) < 1e-12, f"amplitude {gamma} is trace preserving")
for lam in (0.0, 0.3, 0.9):
    check(channels.check_complete(channels.phase_damping(lam)) < 1e-12, f"phase {lam} is trace preserving")

one = states.apply(states.zero(1), states._gate("ry", np.pi / 3), (0,), 1)
damped = channels.apply_channel(one, channels.depolarizing(0.2), (0,), 1)
x, _, z = states.bloch(damped)
check(abs(x - 0.6928) < 1e-4 and abs(z - 0.4) < 1e-9, "depolarizing shrinks x and z by the same factor")
relaxed = channels.apply_channel(one, channels.amplitude_damping(0.2), (0,), 1)
x2, _, z2 = states.bloch(relaxed)
check(z2 > 0.5, "amplitude damping moves z toward +1")
check(pow(x2, 2) + pow(z2, 2) < 1.0, "and shrinks the vector")
dephased = channels.apply_channel(one, channels.phase_damping(0.2), (0,), 1)
x3, _, z3 = states.bloch(dephased)
check(abs(z3 - 0.5) < 1e-12, "phase damping leaves z untouched")
check(abs(x3 - 0.7746) < 1e-4, "and shrinks x by sqrt(1-lambda)")

with_bell = channels.apply_channel(bell, channels.depolarizing(0.1, 2), (0, 1), 2)
population = states.fidelity_to(with_bell, 0)
check(abs(population - 0.475) < 1e-9, "two-qubit depolarizing at 0.1 leaves 0.475 on 00")
check(abs(states.coherence(with_bell, 0, 3) - 0.45) < 1e-9, "and a coherence of 0.45, which is (1-p) times a half")

t1, t2 = channels.relaxation_channels(t1_us=100.0, t2_us=80.0, gate_us=1.0)
check(abs(channels.check_complete(t1)) < 1e-12, "the T1 channel from times is valid")
try:
    channels.relaxation_channels(t1_us=10.0, t2_us=25.0, gate_us=1.0)
except ValueError:
    check(True, "T2 above twice T1 is refused")
else:
    check(False, "T2 above twice T1 is refused")

# -- the readout matrix -------------------------------------------------
section("the readout matrix")
record = device.load_json(device.READOUT_RUN)
matrix = device.readout_from_record().matrix()
check(matrix.shape == (4, 4), "the calibration makes a 4x4 matrix")
check(bool(np.allclose(matrix.sum(axis=0), 1.0)), "every column sums to one")
check(abs(np.linalg.det(matrix) - 0.8357) < 1e-3, "the determinant is 0.836")
check(abs(float(np.trace(matrix)) - 3.8264) < 1e-3, "the diagonal sums to 3.826")
check(abs(confusion.amplification(matrix) - 1.094) < 0.01, "the inverse amplifies by 1.09")

zero_to_one, one_to_zero = device.asymmetry(record)
check(zero_to_one < 0.012 and one_to_zero > 0.030, "readout is asymmetric: 1 decays, 0 almost does not")
check(one_to_zero / zero_to_one > 3.0, "by more than a factor of three")
flips = device.estimate_flips(record)
check(len(flips) == 2 and all(0 < flip < 0.05 for flip in flips), "a symmetric fit gives two small flips")
check(confusion.independence_error(record, flips) > 0.02, "and the independent model misses a cell by more than 2%")

truth = np.array([0.5, 0.0, 0.0, 0.5])
seen = matrix @ truth
recovered, _ = confusion.correct(
    {key: int(round(float(value) * 10_000)) for key, value in zip(states.labels(2), seen)}, matrix
)
check(abs(recovered["00"] - 0.5) < 0.002 and abs(recovered["11"] - 0.5) < 0.002,
      "a known state round-trips through the matrix and its inverse")

try:
    confusion.inverse(np.zeros((4, 4)))
except ValueError:
    check(True, "a singular matrix is refused")
else:
    check(False, "a singular matrix is refused")

# -- the recorded corrections ------------------------------------------
section("the recorded runs")
bell_run = json.loads((device.ROOT / "runs/chapter18/0001-bell-1024-ibm/result.json").read_text())
bell_fixed, clipped = confusion.correct(bell_run["counts"], matrix)
bell_raw = (bell_run["counts"]["00"] + bell_run["counts"]["11"]) / sum(bell_run["counts"].values())
check(abs(bell_raw - 0.9463) < 1e-4, "the Bell run is 0.9463 correlated")
check(abs(bell_fixed["00"] + bell_fixed["11"] - 0.9896) < 1e-3, "the correction takes it to 0.9896")
check(clipped < 1e-9, "and clips nothing")

chsh_run = json.loads((device.ROOT / "runs/chapter04/0007-chsh-1024-ibm/result.json").read_text())
raw_correlators = {
    name: confusion.correlation({key: value / sum(counts.values()) for key, value in counts.items()})
    for name, counts in chsh_run["counts"].items()
}
fixed_correlators = {
    name: confusion.correlation(confusion.correct(counts, matrix)[0])
    for name, counts in chsh_run["counts"].items()
}
check(abs(confusion.chsh(raw_correlators) - 2.541) < 1e-3, "the CHSH run is 2.541")
check(abs(confusion.chsh(fixed_correlators) - 2.7815) < 1e-3, "the correction takes it to 2.7815")
check(confusion.chsh(fixed_correlators) < 2 * math.sqrt(2), "and stays below the Tsirelson bound")

grover_run = json.loads((device.ROOT / "runs/chapter07/0013-grover-3qubits-1024-ibm/result.json").read_text())
three = device.Readout.independent((flips[0], flips[1], flips[1]))
grover_fixed, _ = confusion.correct(grover_run["counts"], three.matrix())
check(abs(grover_run["counts"]["101"] / 1024 - 0.7148) < 1e-4, "Grover found the item 0.7148 of the time")
check(abs(grover_fixed["101"] - 0.7649) < 1e-3, "the three-wire correction takes it to 0.7649")
check(grover_fixed["101"] < 0.8, "and leaves it far from the ideal 0.9453")

# -- the simulator ------------------------------------------------------
section("the simulator")
rate = 1 - confusion.chsh(fixed_correlators) / (2 * math.sqrt(2))
check(abs(rate - 0.01661) < 1e-4, "the corrected CHSH leaves a rate of 0.01661")

simulator = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=rate), readout=None)
bell_model = matrix @ simulator.distribution(2, simulate.bell())
model_correlation = float(bell_model[0] + bell_model[3])
check(abs(model_correlation - 0.9488) < 1e-3, "the model puts the raw Bell correlation at 0.9488")
check(abs(model_correlation - 0.9463) < 3 * device.sigma_binomial(0.9463, 1024), "within three sigma of the run")

ideal = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=0.0), readout=None)
exact = ideal.distribution(2, simulate.bell())
check(abs(exact[0] - 0.5) < 1e-12, "with a zero rate the Bell pair is exact")

sampled = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=0.0), readout=None, seed=1)
counts = sampled.run(2, simulate.bell(), 2048)
check(sum(counts.values()) == 2048, "a sampled run returns its shots")
check(set(counts) <= {"00", "11"}, "and only the two Bell outcomes")

two_qubit = simulate.Simulator(rates=device.uniform_rates(single=0.0, two=0.1), readout=None)
p = two_qubit.distribution(2, simulate.bell())
check(abs(p[1] - 0.025) < 1e-9, "a 0.1 two-qubit rate puts 0.025 on 01")

# -- folding and extrapolation -----------------------------------------
section("folding")
base = simulate.bell()
check(len(zne.fold(base, 1)) == 2, "scale 1 is the circuit itself")
check(len(zne.fold(base, 3)) == 6, "scale 3 triples the gates")
check(len(zne.fold(base, 5)) == 10, "scale 5 quintuples them")
check(zne.fold(base, 3)[2] == ("cx", (0, 1), None), "the fold inverts the copy")
check(zne.fold(base, 3)[3] == ("h", (0,), None), "and reverses the order")

for bad in (0, 2, 4, -1):
    try:
        zne.fold(base, bad)
    except ValueError:
        check(True, f"a fold scale of {bad} is refused")
    else:
        check(False, f"a fold scale of {bad} is refused")

points = [zne.Point(1, 2.7815, 0.045), zne.Point(3, 2.6898, 0.045), zne.Point(5, 2.6013, 0.045)]
linear_fit = zne.linear(points)
check(abs(linear_fit.value - 2.8260) < 1e-3, "linear extrapolation of the corrected points gives 2.8260")
check(abs(linear_fit.sigma - 1.208 * 0.045) < 1e-3, "with 1.208 times one point's error")
check(abs(sum(linear_fit.weights) - 1.0) < 1e-12, "the weights sum to one")
exponential_fit = zne.exponential(points)
check(abs(exponential_fit.value - 2.8284) < 1e-3, "exponential extrapolation gives the ideal value")
check(abs(exponential_fit.value - 2 * math.sqrt(2)) < 1e-3, "which is 2.8284")

raw_points = [zne.Point(1, 2.5405, 0.045), zne.Point(3, 2.4567, 0.045), zne.Point(5, 2.3756, 0.045)]
raw_fit = zne.linear(raw_points)
check(abs(raw_fit.value - 2.5812) < 1e-3, "without the readout correction, ZNE returns 2.5812")
check(raw_fit.value < linear_fit.value, "which is worse than doing the correction first")

try:
    zne.exponential([zne.Point(1, 0.0), zne.Point(3, 0.0)])
except ValueError:
    check(True, "a log of zero is refused")
else:
    check(False, "a log of zero is refused")

# -- the prediction that fails -----------------------------------------
section("the falsification")
budget, record = device.calibration_budget()
check(record["circuit"]["depth"] == 169, "the exported circuit transpiles to depth 169, as the run says")
check(budget.two_qubit_gates == 45, "with 45 two-qubit gates")
check(abs(budget.gates - 0.8229) < 1e-3, "whose survival is 0.8229")
check(abs(budget.total - 0.8135) < 1e-3, "and 0.8135 with the snapshot's readout")

peak_per_gate = fit.peak(0.9453, budget.gates)
check(abs(peak_per_gate - 0.7779) < 1e-3, "the per-gate model predicts a peak of 0.7779")
gate_test = fit.test("gate", peak_per_gate, 0.7649, 1024)
check(abs(gate_test.z) < 1.5, "which is within a sigma and a half of the measurement")
check(gate_test.verdict == "consistent", "so the per-gate model survives")

uniform = fit.peak(0.9453, fit.predict(rate, 45))
check(abs(uniform - 0.4449) < 1e-3, "one rate from CHSH predicts 0.4449")
uniform_test = fit.test("uniform", uniform, 0.7649, 1024)
check(uniform_test.z < -10, "which is more than ten sigma below the measurement")
check(uniform_test.verdict == "falsified", "so the uniform model is falsified")

bell_rate = 1 - 0.9896
check(abs(bell_rate - 0.01035) < 0.0005, "the Bell correlation fits 0.01035")
check(bell_rate < rate, "which is smaller than the CHSH fit, by a factor of 1.6")

worst = record["cz_catalogue"]["max"]
check(worst > 0.5, "the device has an edge with error above one half, which is a dead coupler")
check(record["cz_catalogue"]["edges"] > 100, "over a catalogue of more than a hundred edges")

# -- the fit arithmetic -------------------------------------------------
section("the fit")
check(abs(fit.uniform_rate(0.9896, 1.0, 1) - 0.0104) < 1e-4, "one gate that leaves 0.9896 has rate 0.0104")
check(abs(fit.predict(0.0104, 45) - 0.6247) < 1e-3, "raised to 45 gates it leaves 0.6247")
check(abs(fit.uniform_rate(0.9453, 1.0, 45) - 0.001249) < 1e-5, "and the inverse fit recovers it")

for bad in (0.0, -0.1, 1.5):
    try:
        fit.uniform_rate(bad)
    except ValueError:
        check(True, f"a measured value of {bad} is refused")
    else:
        check(False, f"a measured value of {bad} is refused")

check(abs(device.sigma_binomial(0.5, 100) - 0.05) < 1e-12, "a coin at 100 shots has a 0.05 error")
check(fit.residuals([gate_test, uniform_test]) > 10, "the worst residual is the uniform model's")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
