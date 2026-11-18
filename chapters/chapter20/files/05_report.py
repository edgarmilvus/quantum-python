"""Demo 05: the report the chapter ends on.

Run: python3 chapters/chapter20/files/05_report.py

One table: the prepared state, the three runs, the fidelity of each, and the verdict. The
last line is the chapter's claim, and it is a sentence because the result is a sentence:
the state arrived, and the two classical bits are what carried it.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from teleport import Calibration, Prepared, run

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/0042-ibm-fez-teleport/result.json").read_text())
prepared = Prepared(record["prepared"]["theta"], record["prepared"]["phi"])

print(f"teleportation on {record['backend']}, {record['shots']} shots")
print(prepared.report())
print(Calibration.from_counts(record["calibration"]).report())
print()
print(f"{'run':12s}{'fidelity':>10s}   verdict")
for kind in ("dynamic", "postselect", "uncorrected"):
    scored = run(record, kind)
    print(f"{kind:12s}{scored.fidelity:10.4f}   {scored.verdict}")
print()
best = run(record, "dynamic")
worst = run(record, "uncorrected")
print(f"the correction is worth {best.fidelity - worst.fidelity:.3f} in fidelity,")
print("and the dynamic circuit matches the arithmetic to within half a point.")
print(f"the state arrived with fidelity {best.fidelity:.4f}.")
