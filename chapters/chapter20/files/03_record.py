"""Demo 03: the recorded run, read from the file.

Run: python3 chapters/chapter20/files/03_record.py

The record holds thirteen histograms: three bases for the dynamic circuit, three for the
postselected one, three for the uncorrected control, and four calibration circuits. The
demo prints the readout rates, the raw margins, and the counts the correction has to fix.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from teleport import Calibration, Prepared

ROOT = Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/0042-ibm-fez-teleport/result.json").read_text())

print(f"{record['backend']}, job {record['job_id']}, {record['shots']} shots, depth {record['transpiled_depth']}")
prepared = Prepared(record["prepared"]["theta"], record["prepared"]["phi"])
print(prepared.report())

calibration = Calibration.from_counts(record["calibration"])
print(calibration.report())
print()
print(f"{'basis':6s}{'dynamic p(0)':>14s}{'postselect p(0)':>18s}{'uncorrected p(0)':>18s}")
for basis in ("X", "Y", "Z"):
    row = []
    for kind in ("dynamic", "postselect", "uncorrected"):
        counts = record[kind]["counts"][basis]
        total = sum(counts.values())
        ones = sum(value for key, value in counts.items() if key[0] == "1")
        row.append(1 - ones / total)
    print(f"{basis:6s}{row[0]:14.4f}{row[1]:18.4f}{row[2]:18.4f}")

print()
print("the receiving qubit is measured in all thirteen circuits; the raw margins already")
print("show the dynamic and postselected runs agreeing and the uncorrected one at a half.")
