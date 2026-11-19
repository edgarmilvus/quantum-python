"""Demo 04: the four settings as they ran on a real device, and the margin.

Run: python3 chapters/chapter04/files/04_hardware.py

Reads runs/chapter04/0007-chsh-1024-ibm/result.json. No network, no new spend.
"""

import json
from pathlib import Path

import bell

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/chapter04/0007-chsh-1024-ibm/result.json").read_text())

print(f"backend: {record['backend']}, job {record['job_id']}")
print(f"shots per setting: {record['shots']}")
print(f"transpiled depths: {record['transpiled_depths']}")
print()

measured = {}
print(f"{'setting':16s}{'E measured':>12s}{'E predicted':>13s}{'difference':>12s}")
for name, counts in record["counts"].items():
    measured[name] = bell.expectation_from_counts(counts)
    angle_a, angle_b = record["settings"][name]
    predicted = bell.predicted_expectation(angle_a, angle_b)
    print(f"{name:16s}{measured[name]:12.4f}{predicted:13.4f}{measured[name] - predicted:12.4f}")

s = bell.chsh(measured)
error = bell.chsh_error(measured, record["shots"])
sigma = bell.violation_sigma(measured, record["shots"])

print()
print(f"S measured:      {s:.4f}")
print(f"1 sigma error:   {error:.4f}")
print(f"classical bound: {bell.CLASSICAL_BOUND:.4f}")
print(f"Tsirelson bound: {bell.TSIRELSON_BOUND:.4f}")
print(f"margin over classical: {s - bell.CLASSICAL_BOUND:+.4f} ({sigma:.1f} sigma)")
print()
ideal = bell.chsh(bell.simulate())
print(f"ideal S for comparison: {ideal:.4f}")
print(f"fraction of the ideal violation kept: {(s - 2) / (ideal - 2):.3f}")
