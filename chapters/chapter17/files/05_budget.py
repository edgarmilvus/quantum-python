"""Demo 05: the syndrom's error rate is the budget, and on this device it is overdrawn.

Run: python3 chapters/chapter17/files/05_budget.py

Reads runs/chapter17/0034-syndrome-two-registers-8192-ibm, two circuits at 8,192 shots that return both the
syndrome and the data. A clean |111> produces a nonzero syndrome 6.3 percent of the
time, and each false syndrome becomes a real flip. The code needs the syndrome to be
cleaner than the data; here it is about twice as dirty.
"""

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
syndromes = json.loads((ROOT / "runs/chapter17/0034-syndrome-two-registers-8192-ibm/result.json").read_text())
memory = json.loads((ROOT / "runs/chapter17/0031-dynamic-correction-4096-ibm/result.json").read_text())

print(f"job {syndromes['job_id']} on {syndromes['backend']}, {syndromes['shots']} shots")
print()
print(f"{'prepared':>9s}{'syndromes':>28s}{'false rate':>12s}")
for row in syndromes["results"]:
    total = sum(row["syndromes"].values())
    false = sum(count for key, count in row["syndromes"].items() if key != "00") / total
    shown = ", ".join(f"{key}:{count / total:.3f}" for key, count in sorted(row["syndromes"].items()))
    print(f"{row['prepared']:>9d}{shown:>28s}{false:12.3f}")
print()

print("the false syndrome rate is 6.3 percent on the decaying codeword, and the data")
print("qubits themselves err at 1.9 percent each in the same experiments. The syndrome")
print("is more than three times dirtier than the data it is supposed to diagnose,")
print("which is the one inequality a code cannot afford.")
print()

print("the memory experiment, for the same job family:")
print(f"{'prepared':>9s}{'idle':>7s}{'corrected':>12s}{'control':>10s}")
by = {(row["prepared"], row["idle_us"], row["corrected"]): row for row in memory["results"]}
for prepared in (0, 1):
    for idle in (0.0, 20.0):
        fixed = by[(prepared, idle, True)]
        loose = by[(prepared, idle, False)]

        def wrong(row):
            total = sum(row["counts"].values())
            return sum(count for key, count in row["counts"].items()
                       if (sum(1 for character in key if character == "1") * 2 > 3) != row["prepared"]) / total

        print(f"{prepared:>9d}{idle:7.0f}{wrong(fixed):12.4f}{wrong(loose):10.4f}")
print()
print("on a clean codeword the correction is fifty times worse than the control,")
print("0.0325 against 0.0005, and the reason is in the first table: a correction that")
print("fires on a wrong syndrome adds the error it was meant to remove.")
