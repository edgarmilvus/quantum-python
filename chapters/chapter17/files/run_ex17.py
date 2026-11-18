"""Chapter 17 harness: the dynamic circuit, the trajectory, and the device.

Run: python3 chapters/chapter17/files/run_ex17.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dyn import circuit, sim

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


ROOT = Path(__file__).resolve().parents[3]

# -- the circuit --------------------------------------------------------
section("the circuit")
clean = circuit.memory(prepared=0, correct=True)
check(circuit.qubits(clean) == 5, "three data qubits and two ancillas")
check(circuit.clbits(clean) == 5, "two syndrome bits and three data bits")
check(clean[4] == ("measure", (3,), 3), "the fifth operation is the first ancilla measurement")

flipped = circuit.memory(prepared=1)
check(flipped[:3] == [("x", (0,)), ("x", (1,)), ("x", (2,))], "a one is three X gates")

table = circuit.correction()
check(len(table) == 3, "three syndromes to correct")
check(table[0][1] == ((3, 4), 1) and table[0][2] == [("x", (0,))], "value 1 flips qubit 0")
check(table[1][1] == ((3, 4), 3) and table[1][2] == [("x", (1,))], "value 3 flips qubit 1")
check(table[2][1] == ((3, 4), 2) and table[2][2] == [("x", (2,))], "value 2 flips qubit 2")

for bad in (2, -1):
    try:
        circuit.prepare(bad)
    except ValueError:
        check(True, f"a prepared bit of {bad} is refused")
    else:
        check(False, f"a prepared bit of {bad} is refused")

try:
    circuit.memory(rounds=0)
except ValueError:
    check(True, "zero rounds is refused")
else:
    check(False, "zero rounds is refused")

try:
    circuit.inject(3, (1, 1))
except ValueError:
    check(True, "flipping one qubit twice is refused")
else:
    check(False, "flipping one qubit twice is refused")

check(len(circuit.memory(rounds=2)) > len(circuit.memory(rounds=1)), "a second round is longer")

# -- the trajectory -----------------------------------------------------
section("the trajectory")
for position in range(3):
    counts = sim.sample(circuit.memory(prepared=0, correct=True, flips=(position,)), 400, seed=1)
    check(counts.get("000", 0) == 400, f"a single flip at {position} is corrected")
    loose = sim.sample(circuit.memory(prepared=0, correct=False, flips=(position,)), 400, seed=1)
    check(loose.get("000", 0) == 0, f"and is left alone without the correction")

double = sim.sample(circuit.memory(prepared=0, correct=True, flips=(0, 1)), 400, seed=1)
check(double.get("000", 0) == 0, "two flips are a majority for the wrong answer")

prepared_one = sim.sample(circuit.memory(prepared=1, correct=True), 200, seed=1)
check(prepared_one == {"111": 200}, "a clean one comes back clean")

conditional = [
    ("h", (0,)),
    ("cx", (0, 1)),
    ("measure", (1,), 2),
    ("if", (2, 1), [("x", (0,))]),
    ("measure", (0,), 0),
]
joint = sim.histogram(conditional, 1000, bits=(2, 0), seed=2)
check(set(joint) == {"00", "10"}, "the conditional forces the data to zero")
check(all(key[1] == "0" for key in joint), "in both branches")
plain = sim.histogram(conditional[:3] + conditional[4:], 1000, bits=(2, 0), seed=2)
check(set(plain) == {"00", "11"}, "without it the pair is correlated instead")

# -- the device ---------------------------------------------------------
section("the device")
injection = json.loads((ROOT / "runs/0032-ibm-fez-inject/result.json").read_text())
check(len(injection["results"]) == 6, "six injection circuits")
rows = {(row["flip"], row["corrected"]): row for row in injection["results"]}


def clean_fraction(row) -> float:
    total = sum(row["counts"].values())
    return row["counts"].get("000", 0) / total


check(abs(clean_fraction(rows[(1, True)]) - 0.904) < 0.01, "the middle qubit is restored 90.4% of the time")
check(abs(clean_fraction(rows[(1, False)]) - 0.010) < 0.01, "against 1.0% without the correction")
check(clean_fraction(rows[(0, True)]) > 0.75, "the edge qubits are restored above 75%")
check(clean_fraction(rows[(0, False)]) < 0.05, "against below 5% without")

latency = json.loads((ROOT / "runs/0033-ibm-fez-latency/result.json").read_text())
modes = {row["mode"]: row for row in latency["results"]}


def logical(row, prepared=1) -> float:
    total = sum(row["counts"].values())
    wrong = 0
    for key, count in row["counts"].items():
        bits = [int(character) for character in key[::-1]]
        if (sum(bits) * 2 > 3) != prepared:
            wrong += count
    return wrong / total


check(abs(logical(modes["none"]) - 0.0010) < 0.001, "the control's logical error is 0.001")
check(logical(modes["noop"]) < 0.002, "the conditional with an identity is free")
check(abs(logical(modes["correct"]) - 0.0237) < 0.003, "the real correction costs 0.024")

syndrome = json.loads((ROOT / "runs/0034-ibm-fez-syndrome/result.json").read_text())
prepared_one = next(row for row in syndrome["results"] if row["prepared"] == 1)
total = sum(prepared_one["syndromes"].values())
false_rate = sum(count for key, count in prepared_one["syndromes"].items() if key != "00") / total
check(abs(false_rate - 0.063) < 0.01, "a clean one produces a false syndrome 6.3% of the time")
check(prepared_one["syndromes"]["00"] / total > 0.9, "and the true one 93.7%")

memory = json.loads((ROOT / "runs/0031-ibm-fez-dynamic/result.json").read_text())
check(len(memory["results"]) == 8, "eight memory circuits")
memory_rows = {(row["prepared"], row["idle_us"], row["corrected"]): row for row in memory["results"]}
check(abs(logical(memory_rows[(1, 0.0, True)]) - 0.0325) < 0.005, "correction on a clean one costs 0.0325")
check(logical(memory_rows[(1, 0.0, False)]) < 0.002, "the control is under 0.002")
check(logical(memory_rows[(1, 0.0, True)]) > 10 * logical(memory_rows[(1, 0.0, False)]),
      "so the correction is an order of magnitude worse than doing nothing")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
