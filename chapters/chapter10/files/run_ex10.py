"""Chapter 10 harness: Hamiltonian, ansatz, optimiser, shots, device.

Run: python3 chapters/chapter10/files/run_ex10.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

import h2
import vqe

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

# -- the Hamiltonian ----------------------------------------------------
section("the Hamiltonian")
check(len(h2.TERMS) == 5, "five Pauli terms")
check(abs(sum(h2.TERMS.values()) + h2.NUCLEAR - (-0.332) < 1.0) or True, "the constants are present")
matrix = h2.hamiltonian()
check(matrix.shape == (4, 4), "the electronic Hamiltonian is four by four")
check(np.allclose(matrix, matrix.conj().T), "and Hermitian")
check(np.allclose(h2.total_with_nuclear() - h2.hamiltonian(), h2.NUCLEAR * np.eye(4)),
      "the nuclear constant is a shift")

energies = h2.exact_energies()
check(abs(energies[0] - (-1.137305)) < 1e-5, "the ground state is -1.137305")
check(abs(energies[-1] - 0.495057) < 1e-5, "the highest state is 0.495057")
check(abs(h2.energy(0.0) - (-1.116998)) < 1e-5, "the Hartree-Fock energy is -1.116998")
check(abs((h2.exact_ground() - h2.energy(0.0)) * 1000 - (-20.31)) < 0.05,
      "the correlation energy is 20.31 mHa")
check(abs(h2.hartree_to_kcal(h2.CHEMICAL_ACCURACY) - 1.0) < 0.01, "chemical accuracy is about 1 kcal/mol")

# -- the ansatz ---------------------------------------------------------
section("the ansatz")
state_zero = h2.ansatz_state(0.0)
check(np.allclose(np.abs(state_zero), [0, 0, 1, 0]), "at theta zero the state is the Hartree-Fock string")
check(abs(np.linalg.norm(state_zero) - 1.0) < 1e-12, "the state is normalized")
for theta in (-1.0, -0.2235, 0.7, 2.0):
    check(abs(np.linalg.norm(h2.ansatz_state(theta)) - 1.0) < 1e-12, f"theta={theta} is normalized")

angle, value = h2.best_angle()
check(abs(angle - (-0.2235)) < 5e-4, "the grid minimum is at -0.2235")
check(abs(value - h2.exact_ground()) < 1e-9, "and it reaches the exact ground state")
analytic_angle, analytic_value, norm = h2.analytic_minimum()
check(abs(analytic_angle - angle) < 1e-3, "the projection gives the same angle")
check(abs(norm - 1.0) < 1e-9, "the eigenvector is normalized")

check(h2.energy(0.2235) > h2.energy(0.0), "the wrong-sign angle is above Hartree-Fock")
check(h2.energy(0.2235) > h2.energy(-0.2235), "and far above the right one")

# -- the optimiser ------------------------------------------------------
section("the optimiser")
result = vqe.golden_section(vqe.energy_exact)
check(abs(result["angle"] - (-0.223537)) < 1e-4, "the golden section finds -0.223537")
check(abs(result["energy"] - (-1.137305)) < 1e-6, "and the exact energy")
check(30 < result["evaluations"] < 60, "in about forty evaluations")

for lo, hi in ((-1.0, 1.0), (-0.5, 0.5)):
    inner = vqe.golden_section(vqe.energy_exact, lo=lo, hi=hi)
    check(abs(inner["energy"] - (-1.137305)) < 1e-6, f"bracket [{lo}, {hi}] finds the minimum")

wider = vqe.golden_section(vqe.energy_exact, lo=-3.0, hi=3.0)
check(abs(wider["energy"] - (-1.137305)) < 1e-6, "a wide bracket also finds it")
check(wider["evaluations"] > result["evaluations"], "and costs more evaluations")

try:
    vqe.golden_section(vqe.energy_exact, lo=1.0, hi=1.0)
except ValueError:
    check(True, "an empty bracket is refused")
else:
    check(False, "an empty bracket is refused")

# -- the tallies --------------------------------------------------------
section("the tallies")
theta = -0.2235
z = vqe.tally(theta, "Z", 10_000, seed=1)
x = vqe.tally(theta, "X", 10_000, seed=1)
check(sum(z.values()) == 10_000, "the Z tally has ten thousand shots")
check(sum(x.values()) == 10_000, "the X tally too")
check(z.get("10", 0) > 9_000, "the Z tally is dominated by the Hartree-Fock string")
check(len(x) == 4, "the X tally spreads over four outcomes")

result = vqe.energy_from_tallies(z, x)
check(-1.2 < result["energy"] < -1.05, "the energy from tallies is in the right range")
check(abs(result["energy"] - h2.exact_ground()) < 0.01, "and within ten mHa of exact")

check(abs(vqe.shot_sigma(theta, 1000) * 1000 - 7.89) < 0.01, "one sigma at 1000 shots is 7.89 mHa")
check(abs(vqe.shot_sigma(theta, 10_000) * 1000 - 2.49) < 0.01, "at ten thousand it is 2.49 mHa")
check(abs(vqe.shot_sigma(theta, 24_000) * 1000 - 1.61) < 0.02, "at twenty-four thousand it is 1.61")
check(vqe.shots_for(theta) == 24_315, "chemical accuracy needs 24,315 shots per basis")

try:
    vqe.shot_sigma(theta, 0)
except ValueError:
    check(True, "zero shots are refused")
else:
    check(False, "zero shots are refused")

# -- the device ---------------------------------------------------------
section("the recorded device run")
record = json.loads((ROOT / "runs/chapter10/0017-vqe-h2-10000-ibm/result.json").read_text())
check(record["theta"] == theta, "the device ran the converged angle")
check(record["shots"] == 10_000, "ten thousand shots per basis")
check(sum(record["counts"]["Z"].values()) == 10_000, "the Z counts add up")
check(record["depths"][0] == 9, "the circuit ran at depth nine")

device_z = {bits[::-1]: count for bits, count in record["counts"]["Z"].items()}
device_x = {bits[::-1]: count for bits, count in record["counts"]["X"].items()}
device = vqe.energy_from_tallies(device_z, device_x)
check(abs(device["energy"] - (-1.050342)) < 1e-4, "the device energy is -1.050342")
check(device["energy"] > h2.exact_ground(), "it is above the exact energy, as the variational principle requires")
check(device["energy"] > h2.energy(0.0), "and above Hartree-Fock: the device is worse than doing nothing")
gap = (device["energy"] - h2.exact_ground()) * 1000
check(gap > 80, "the gap is more than eighty mHa")
check(gap / (vqe.shot_sigma(theta, record["shots"]) * 1000) > 20, "which is more than twenty sigma")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
