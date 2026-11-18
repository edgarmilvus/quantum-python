"""Demo 04: the marked item recovered from a device.

Run: python3 chapters/chapter07/files/04_hardware.py

Reads runs/0013-ibm-grover/result.json.
"""

import json
from pathlib import Path

import grover

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/0013-ibm-grover/result.json").read_text())

counts = record["counts"]
total = sum(counts.values())
marked = record["marked_bits"]
ordered = sorted(counts.items(), key=lambda item: -item[1])

print(f"backend: {record['backend']}, depth {record['transpiled_depth']}, job {record['job_id']}")
print(f"marked item: {marked}, iterations: {record['steps']}, shots: {total}")
print(f"ideal probability: {record['ideal_probability']:.4f}")
print()
print(f"{'outcome':10s}{'count':>8s}{'frequency':>12s}")
for outcome, count in ordered:
    print(f"{outcome:10s}{count:8d}{count / total:12.4f}")

top = ordered[0][0]
print()
print(f"most frequent outcome: {top} ({ordered[0][1]} shots)")
print(f"correct: {top == marked}")
print(f"frequency of the marked item: {counts.get(marked, 0) / total:.4f}")

size = 1 << record["n"]
print()
print(f"uniform guessing would find it {1 / size:.3f} of the time")
print(f"the device found it {counts.get(marked, 0) / total:.3f} of the time")
print(f"classical linear search needs {grover.classical_queries(size)} queries on average")
print(f"the circuit used {record['steps']} iterations, each with one oracle call")
print()
print(f"matching outcomes within one bit of the marked item: "
      f"{sum(v for k, v in counts.items() if bin(int(k, 2) ^ int(marked, 2)).count('1') == 1) / total:.4f}")
