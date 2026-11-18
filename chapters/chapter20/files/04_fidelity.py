"""Demo 04: three fidelities, and the one number that says the correction mattered.

Run: python3 chapters/chapter20/files/04_fidelity.py

The device ran the same tomography three times: with the correction applied inside the
circuit, with it applied in the arithmetic, and without it. The demo scores all three and
prints the gap, which is what the two classical bits buy.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from teleport import Prepared, run

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/0042-ibm-fez-teleport/result.json").read_text())

rows = {kind: run(record, kind) for kind in ("dynamic", "postselect", "uncorrected")}
for kind in ("dynamic", "postselect", "uncorrected"):
    print(rows[kind].report())

prepared = Prepared(record["prepared"]["theta"], record["prepared"]["phi"])
ideal = prepared.bloch()
print()
print(f"ideal bloch      ({ideal[0]:+.4f}, {ideal[1]:+.4f}, {ideal[2]:+.4f})")
print(f"dynamic minus postselect: {rows['dynamic'].fidelity - rows['postselect'].fidelity:+.4f}")
print(f"dynamic minus uncorrected: {rows['dynamic'].fidelity - rows['uncorrected'].fidelity:+.4f}")
print()
print("the two corrected runs agree to half a point, which is the shot noise at 2,048")
print("shots; the uncorrected run sits at a half, which is the classical average.")
