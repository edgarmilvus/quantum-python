"""Demo 05: the converged circuit on a device, and the energy it returns.

Run: python3 chapters/chapter10/files/05_hardware.py

Reads runs/chapter10/0017-vqe-h2-10000-ibm/result.json: two tallies, 10,000 shots each, theta = -0.2235.
"""

import json
from pathlib import Path

import h2
import vqe

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/chapter10/0017-vqe-h2-10000-ibm/result.json").read_text())

# Qiskit writes the bitstring with qubit 1 first; this book puts qubit 0 first.
z_counts = {bits[::-1]: count for bits, count in record["counts"]["Z"].items()}
x_counts = {bits[::-1]: count for bits, count in record["counts"]["X"].items()}

theta = record["theta"]
print(f"backend: {record['backend']}, depth {record['depths'][0]}, shots {record['shots']}")
print(f"theta = {theta}, exact energy {record['exact_energy']:.6f}")
print()
print(f"Z tally: {dict(sorted(z_counts.items()))}")
print(f"X tally: {dict(sorted(x_counts.items()))}")
print()

result = vqe.energy_from_tallies(z_counts, x_counts)
for key, value in result.items():
    print(f"  {key:10s} {value:+.6f}")

sigma = vqe.shot_sigma(theta, record["shots"])
print()
print(f"energy from the device: {result['energy']:.6f} +/- {sigma:.6f}")
print(f"exact:                  {h2.exact_ground():.6f}")
print(f"Hartree-Fock:           {h2.energy(0.0):.6f}")
print()
difference = (result["energy"] - h2.exact_ground()) * 1000
print(f"difference from exact:  {difference:+.2f} mHa")
print(f"in units of sigma:      {difference / 1000 / sigma:+.2f}")
print(f"chemical accuracy:      +/- {h2.CHEMICAL_ACCURACY * 1000:.2f} mHa")
