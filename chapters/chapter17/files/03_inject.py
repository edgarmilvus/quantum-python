"""Demo 03: the injection test, on the device.

Run: python3 chapters/chapter17/files/03_inject.py

Reads runs/chapter17/0032-inject-one-flip-4096-ibm: one X on a data qubit before the syndrome, with and
without the conditional correction. The correction brings the codeword back 81 to
90 percent of the time; the control brings it back 1 to 3 percent of the time.
That is the mechanism working, measured.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/chapter17/0032-inject-one-flip-4096-ibm/result.json").read_text())

print(f"job {record['job_id']} on {record['backend']}, {record['shots']} shots")
print()
print(f"{'flip':>5s}{'correction':>12s}{'clean 000':>11s}{'one flip':>10s}")
rows = {}
for row in record["results"]:
    total = sum(row["counts"].values())
    clean = row["counts"].get("000", 0) / total
    single = sum(count for key, count in row["counts"].items()
                 if sum(1 for character in key if character == "1") == 1) / total
    rows[(row["flip"], row["corrected"])] = (clean, single)
    print(f"{row['flip']:5d}{str(row['corrected']):>12s}{clean:11.3f}{single:10.3f}")
print()

print("the correction's gain, per injected error:")
for flip in (0, 1, 2):
    fixed = rows[(flip, True)][0]
    loose = rows[(flip, False)][0]
    print(f"  qubit {flip}: clean {loose:.3f} -> {fixed:.3f}, a factor of {fixed / loose:.1f}")
print()
print("the middle qubit does best because its syndrome 11 is two flips away from 00")
print("in readout terms, while the edge qubits sit at 10 and 01 and one misread")
print("turns them into a false 00. That asymmetry is the ancilla's, not the code's.")
