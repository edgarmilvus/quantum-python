"""Demo 05: what the recorded device profile predicts, against what ran.

Run: python3 chapters/chapter03/files/05_hardware.py

It reads two recorded files and nothing from the network:
  runs/0001-ibm-fez-bell/result.json   the job that ran
  chapter03/profiles/ibm_fez.json      the device, captured before the job
"""

import json
from pathlib import Path

from profile import depth_where_prediction_crosses, load, predicted_error, summary, worst_two_qubit_error

ROOT = Path(__file__).resolve().parents[3]
run = json.loads((ROOT / "runs/0001-ibm-fez-bell/result.json").read_text())
device = load()

info = summary(device)
print(f"backend: {info['backend']}, {info['qubits']} qubits")
print(f"basis: {info['basis']}")
print(f"two-qubit errors: {[round(e, 5) for e in info['two_qubit_errors']]}")
print(f"readout: {info['readout']:.5f}   T1: {info['t1_us']} us   T2: {info['t2_us']} us")
print()

circuit = run["circuit"]
print(f"the job: {run['backend']}, depth {circuit['logical_depth']} written, "
      f"{circuit['transpiled_depth']} after transpilation on the device")
print(f"counts: {run['counts']}")
print(f"anti-correlated fraction measured: {run['derived']['p_anti_correlated']:.4f}")
print()

prediction = predicted_error(device, two_qubit_gates=1, measured_qubits=2)
print(f"predicted from the profile, one CZ plus two readouts: {prediction:.4f}")
print(f"observed: {run['derived']['p_anti_correlated']:.4f}")
print(f"difference: {abs(prediction - run['derived']['p_anti_correlated']):.4f}")
print()

print("if the depth were the only thing that mattered:")
for depth in (8, 16, 32, 64):
    print(f"  depth {depth:3d}: predicted error {predicted_error(device, depth, 2):.4f}")
print()
print(f"depth at which the prediction crosses 50%: {depth_where_prediction_crosses(device, 0.5)}")
print(f"worst two-qubit error in the profile: {worst_two_qubit_error(device):.5f}")
