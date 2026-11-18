"""Demo 04: the same code on ibm_fez, held idle for 0, 20 and 60 microseconds.

Run: python3 chapters/chapter16/files/04_device.py

Reads runs/0029-ibm-fez-idle: twelve circuits, two distances, two preparations,
three idle times. The binomial law takes the measured physical error and predicts
the logical one to within ten percent, and the distance buys a factor of 2.4 at
twenty microseconds and 1.2 at sixty.
"""

import json
import pathlib

from ecc import code, sim

ROOT = pathlib.Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/0029-ibm-fez-idle/result.json").read_text())
rows = sim.device_table(record)

print(f"job {record['job_id']} on {record['backend']}, {len(rows)} circuits, {record['shots']} shots")
print()
print(f"{'d':>2s}{'prep':>6s}{'idle':>7s}{'physical':>10s}{'logical':>10s}{'predicted':>11s}")
for row in sorted(rows, key=lambda r: (r["distance"], r["prepared"], r["idle_us"])):
    predicted = code.logical_error_ideal(row["distance"], row["physical"])
    print(f"{row['distance']:2d}{row['prepared']:6d}{row['idle_us']:7.0f}{row['physical']:10.4f}"
          f"{row['logical']:10.4f}{predicted:11.4f}")
print()

print("the distance pays at twenty microseconds and much less at sixty:")
for idle in (20.0, 60.0):
    d3 = next(row for row in rows if row["distance"] == 3 and row["prepared"] == 1 and row["idle_us"] == idle)
    d5 = next(row for row in rows if row["distance"] == 5 and row["prepared"] == 1 and row["idle_us"] == idle)
    print(f"  {idle:.0f} us: d=3 {d3['logical']:.4f}, d=5 {d5['logical']:.4f}, factor {d3['logical'] / d5['logical']:.1f}")
print()
print("the prepared-0 rows stay flat because a |000> codeword has nothing to decay;")
print("the prepared-1 rows fall apart because T1 moves |1> to |0> and the vote sees it.")
print("at zero idle time the code is already working: 1.2e-3 against a physical 1.5e-2.")
print()

low, high = code.wilson(0.0, record["shots"])
print(f"a logical error of zero in {record['shots']} shots is below {high:.4f} at 95%")
