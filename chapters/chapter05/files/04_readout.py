"""Demo 04: the readout matrix, and what correcting with it does to S.

Run: python3 chapters/chapter05/files/04_readout.py

Reads runs/chapter12/0009-readout-4circuits-4096-ibm (the calibration) and runs/chapter04/0007-chsh-1024-ibm (the data).
"""

import json
from pathlib import Path

import numpy as np

import calibrate
from stats import invert

ROOT = Path(__file__).resolve().parents[3]
record = calibrate.load()
matrix = calibrate.matrix(record)
inverse = invert(matrix)

print(f"calibration: {record['backend']}, {record['shots']} shots per preparation")
print("rows prepared, columns measured, order 00 01 10 11:")
print(np.round(matrix, 4))
print()

print(f"{'prepared':>10s}{'P(correct)':>12s}{'P(wrong)':>10s}")
for index, label in enumerate(("00", "01", "10", "11")):
    print(f"{label:>10s}{matrix[index, index]:12.4f}{1 - matrix[index, index]:10.4f}")
print()
print(f"average readout error: {calibrate.diagonal_error(matrix):.4f}")
print()

chsh = json.loads((ROOT / "runs/chapter04/0007-chsh-1024-ibm/result.json").read_text())
values = calibrate.corrected_chsh(chsh["counts"], inverse)

print(f"{'setting':16s}{'raw E':>9s}{'corrected':>11s}{'clipped':>9s}")
for name, row in values.items():
    print(f"{name:16s}{row['raw']:9.4f}{row['corrected']:11.4f}{row['clipped_mass']:9.4f}")

print()
print(f"S raw:       {calibrate.chsh_from(values, 'raw'):.4f}")
print(f"S corrected: {calibrate.chsh_from(values, 'corrected'):.4f}")
print(f"ideal:       2.8284")
print()
print("the correction recovers most of the loss, and overshoots on one setting")
print("because the inverse amplifies the noise in 1024 shots")
