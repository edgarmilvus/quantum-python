"""Demo 03: the same matrix, applied to three recorded runs.

Run: python3 chapters/chapter12/files/03_readout.py

The correction closes most of the Bell gap and a fifth of the Grover gap. That
ratio is the chapter's first clue: readout is not the dominant error in a deep
circuit, and a mitigation report has to say how much of a shortfall it explains.
"""

import json
from pathlib import Path

import numpy as np

from noise import confusion, device

ROOT = Path(__file__).resolve().parents[3]
readout_record = json.loads((ROOT / "runs/chapter12/0009-readout-4circuits-4096-ibm/result.json").read_text())
matrix = device.readout_from_record().matrix()

print("the measured matrix, rows reported, columns prepared:")
print(np.round(matrix, 4))
print()
print(f"determinant {np.linalg.det(matrix):.4f}, worst-case amplification {confusion.amplification(matrix):.3f}")
zero_to_one, one_to_zero = device.asymmetry(readout_record)
print(f"P(report 1 | prepare 0) = {zero_to_one:.4f}, P(report 0 | prepare 1) = {one_to_zero:.4f}")
print(f"so a one-parameter symmetric model is wrong by {one_to_zero / zero_to_one:.1f}x on one column")
flips = device.estimate_flips(readout_record)
print(f"the symmetric fit would use {flips[0]:.4f} and {flips[1]:.4f}, and it misses the four diagonal entries")
print(f"  measured   {[round(float(matrix[i, i]), 4) for i in range(4)]}")
tensor = device.Readout.independent(flips).matrix()
print(f"  independent {[round(float(tensor[i, i]), 4) for i in range(4)]}")
print(f"  the largest cell the independence assumption gets wrong: {confusion.independence_error(readout_record, flips):.4f}")
print()

bell = json.loads((ROOT / "runs/chapter18/0001-bell-1024-ibm/result.json").read_text())
corrected, clipped = confusion.correct(bell["counts"], matrix)
raw = (bell["counts"].get("00", 0) + bell["counts"].get("11", 0)) / sum(bell["counts"].values())
fixed = corrected["00"] + corrected["11"]
print(f"Bell pair      raw {raw:.4f}   corrected {fixed:.4f}   ideal 1.0000   clipped {clipped:.4f}")
print(f"               the matrix explains {(fixed - raw) / (1 - raw):.1%} of the gap")
print()

chsh = json.loads((ROOT / "runs/chapter04/0007-chsh-1024-ibm/result.json").read_text())
raw_correlators = {
    name: confusion.correlation({key: value / sum(counts.values()) for key, value in counts.items()})
    for name, counts in chsh["counts"].items()
}
fixed_correlators = {
    name: confusion.correlation(confusion.correct(counts, matrix)[0])
    for name, counts in chsh["counts"].items()
}
print(f"CHSH           raw {confusion.chsh(raw_correlators):.4f}   corrected {confusion.chsh(fixed_correlators):.4f}   ideal 2.8284")
print(f"               the matrix explains {(confusion.chsh(fixed_correlators) - confusion.chsh(raw_correlators)) / (2.828427 - confusion.chsh(raw_correlators)):.1%} of the gap")
print()

grover = json.loads((ROOT / "runs/chapter07/0013-grover-3qubits-1024-ibm/result.json").read_text())
three = device.Readout.independent((flips[0], flips[1], flips[1]))
corrected_three, clipped_three = confusion.correct(grover["counts"], three.matrix())
raw_peak = grover["counts"]["101"] / sum(grover["counts"].values())
fixed_peak = corrected_three["101"]
print(f"Grover         raw {raw_peak:.4f}   corrected {fixed_peak:.4f}   ideal {grover['ideal_probability']:.4f}   clipped {clipped_three:.4f}")
print(f"               the matrix explains {(fixed_peak - raw_peak) / (grover['ideal_probability'] - raw_peak):.1%} of the gap")
print(f"               amplification {confusion.amplification(three.matrix()):.3f}, from a three-wire matrix")
print()
print("the Grover correction borrows the pair's per-qubit flips for a third qubit it")
print("never calibrated: the number is an estimate, and the prose says so")
