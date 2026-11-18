"""Demo 05: the secret recovered from a real device.

Run: python3 chapters/chapter06/files/05_hardware.py

Reads runs/0011-ibm-bv/result.json: one job, one circuit, 1024 shots.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/0011-ibm-bv/result.json").read_text())

counts = record["counts"]
total = sum(counts.values())
secret = record["secret_bits"]
ordered = sorted(counts.items(), key=lambda item: -item[1])

print(f"backend: {record['backend']}, depth {record['transpiled_depth']}, job {record['job_id']}")
print(f"secret submitted: {secret}")
print(f"shots: {total}")
print()
print(f"{'outcome':10s}{'count':>8s}{'frequency':>12s}")
for outcome, count in ordered:
    print(f"{outcome:10s}{count:8d}{count / total:12.4f}")

top_count = counts.get(secret, 0)
print()
print(f"the secret came back {top_count} times out of {total}: {top_count / total:.4f}")
print(f"correct: {ordered[0][0] == secret}")
print()
print(f"outcomes seen: {len(counts)} of the {2 ** record['n']} possible")
print(f"error rate on this run: {1 - top_count / total:.4f}")
