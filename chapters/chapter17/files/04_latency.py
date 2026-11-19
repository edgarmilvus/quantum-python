"""Demo 04: is the classical round trip the cost, or is it the correction?

Run: python3 chapters/chapter17/files/04_latency.py

Reads runs/chapter17/0033-latency-conditional-4096-ibm: three circuits on a clean |111>, one with no
conditional, one whose conditionals apply an identity, and one that corrects. The
middle circuit is free, so the cost is not the feed-forward latency; it is the
gates the correction applies on the strength of a syndrome that is sometimes wrong.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
record = json.loads((ROOT / "runs/chapter17/0033-latency-conditional-4096-ibm/result.json").read_text())

print(f"job {record['job_id']} on {record['backend']}, {record['shots']} shots")
print(f"{'circuit':>10s}{'clean 111':>12s}{'logical error':>15s}")
for row in record["results"]:
    total = sum(row["counts"].values())
    clean = row["counts"].get("111", 0) / total
    wrong = sum(count for key, count in row["counts"].items()
                if sum(1 for character in key if character == "1") * 2 <= 3) / total
    print(f"{row['mode']:>10s}{clean:12.4f}{wrong:15.4f}")
print()
print("the conditional with an identity inside costs nothing measurable: 0.0005")
print("against a control's 0.0010, both inside the shot error of 4,096 shots.")
print("the conditional with a real X costs 0.0237, which is twenty times the control")
print("and is produced by corrections that fire when the syndrome was wrong.")
print()
print("so the chapter's first claim is that the mechanism works and the latency is")
print("not the problem; the second is that the syndrome's own error rate is.")
