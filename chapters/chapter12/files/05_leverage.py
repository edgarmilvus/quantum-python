"""Demo 05: one average rate fails; the per-gate table survives.

Run: python3 chapters/chapter12/files/05_leverage.py

The rate fitted on CHSH is 0.0166. The median two-qubit gate in the published
calibration of ibm_fez is 0.0039. Those are the same device, measured two ways,
and the difference is not an error: one is an average over a circuit's losses,
the other is a property of an edge. Grover's 45 gates decide which of the two is
allowed to make a prediction.
"""

import json
from pathlib import Path

import numpy as np

from noise import device, fit

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/chapter12/0020-calibration-snapshot/circuit.json").read_text())
measured_raw = 0.7148
measured_corrected = 0.7649
shots = 1024
ideal = record["circuit"]["ideal_probability"]

rate_chsh = 0.01661   # demo 04, from the readout-corrected CHSH value
rate_bell = 0.01035   # demo 03, from the readout-corrected Bell correlation
uniform_survival = fit.predict(rate_chsh, 45)
uniform_peak = fit.peak(ideal, uniform_survival)

budget, _ = device.calibration_budget()
per_gate_peak = fit.peak(ideal, budget.gates)
raw_peak = fit.peak(ideal, budget.total)

print(f"Grover: {record['circuit']['two_qubit_gates']} two-qubit gates, "
      f"{record['circuit']['single_qubit_gates']} single-qubit, depth {record['circuit']['depth']}")
print(f"ideal peak {ideal:.4f}, measured raw {measured_raw:.4f}, measured corrected {measured_corrected:.4f}")
print()
print(f"the two short experiments disagree about the rate: Bell says {rate_bell:.5f}, CHSH says {rate_chsh:.5f}")
print(f"  a factor of {rate_chsh / rate_bell:.2f}, which is what a coherent rotation error does to a correlator")
print()

bell_peak = fit.peak(ideal, fit.predict(rate_bell, 45))
bell_test = fit.test("bell", bell_peak, measured_corrected, shots)
chsh_test = fit.test("chsh", uniform_peak, measured_corrected, shots)
gate_test = fit.test("gate", per_gate_peak, measured_corrected, shots)

print(f"{'model':28s}{'survival':>10s}{'peak':>8s}{'vs corrected':>16s}")
print(f"{'one rate from Bell':28s}{fit.predict(rate_bell, 45):10.4f}{bell_peak:8.4f}{bell_test.z:+11.1f} sigma")
print(f"{'one rate from CHSH':28s}{uniform_survival:10.4f}{uniform_peak:8.4f}{chsh_test.z:+11.1f} sigma")
print(f"{'per-gate calibration':28s}{budget.gates:10.4f}{per_gate_peak:8.4f}{gate_test.z:+11.1f} sigma")
print()
print(f"including the snapshot's own readout, the per-gate model predicts the raw value:")
print(f"  {budget.report()}")
print(f"  predicted raw peak {raw_peak:.4f} against a measured {measured_raw:.4f}"
      f"  ({fit.test('raw', raw_peak, measured_raw, shots).z:+.1f} sigma)")
print()

two_qubit = [op for op in record["ops"] if len(op["qubits"]) == 2]
errors = np.array([op["error"] for op in two_qubit])
catalogue = record["cz_catalogue"]
print("the edges the transpiler chose, against the whole device:")
print(f"  used      min {errors.min():.4f}  median {np.median(errors):.4f}  max {errors.max():.4f}")
print(f"  device    min {catalogue['min']:.4f}  median {catalogue['median']:.4f}  max {catalogue['max']:.4f}"
      f"  over {catalogue['edges']} edges")
print(f"  the median edge used is {np.median(errors) / catalogue['median']:.2f} times the device's median")
print(f"  the average rate the CHSH fit produced is {rate_chsh / np.median(errors):.1f} times the used median")
print()
print("that factor is the whole argument: an average is a property of a circuit,")
print("a per-gate number is a property of an edge, and only the second one extrapolates")
print()
print(f"the device's worst edge has error {catalogue['max']:.2f}, which is a dead coupler;")
print("the transpiler never routes through it, and no average would have told you it existed")
