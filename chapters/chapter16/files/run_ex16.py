"""Chapter 16 harness: the code, the rates, the axes, and the device.

Run: python3 chapters/chapter16/files/run_ex16.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ecc import code, sim

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

# -- the code -----------------------------------------------------------
section("the code")
three = code.Repetition(3)
five = code.Repetition(5)
check(three.n == 3 and three.correctable == 1, "d=3 has three qubits and corrects one")
check(five.n == 5 and five.correctable == 2, "d=5 corrects two")
check(three.encode(0) == [0, 0, 0], "the codeword for 0")
check(three.encode(1) == [1, 1, 1], "the codeword for 1")
check(three.checks() == [(0, 1), (1, 2)], "d=3 has two parity checks")

for position in range(3):
    bits = [0, 0, 0]
    bits[position] = 1
    check(three.decode(bits) == 0, f"a single flip at {position} decodes to 0")
    check(three.syndromes(bits) == tuple(
        (bits[i] + bits[i + 1]) % 2 for i in range(2)), "and its syndrome is the difference")

check(three.decode([1, 1, 0]) == 1, "two flips decode to the wrong bit, which is the limit")
check(five.decode([1, 1, 1, 0, 0]) == 1, "three flips in five are a majority for 1")
check(five.decode([1, 1, 0, 0, 0]) == 0, "two flips in five are corrected")

for bad in (2, 4, 1, 0):
    try:
        code.Repetition(bad)
    except ValueError:
        check(True, f"a distance of {bad} is refused")
    else:
        check(False, f"a distance of {bad} is refused")

# -- the rates ----------------------------------------------------------
section("the rates")
check(abs(code.logical_error_ideal(3, 0.1) - 0.028) < 1e-9, "d=3 at p=0.1 is 0.028")
check(abs(code.logical_error_ideal(5, 0.1) - 0.00856) < 1e-4, "d=5 at p=0.1 is 0.00856")
check(code.logical_error_ideal(7, 0.05) < code.logical_error_ideal(3, 0.05), "more distance, fewer errors")
check(code.logical_error_ideal(3, 0.5) == 0.5, "at p=0.5 the code is a coin flip")
check(code.logical_error_ideal(3, 0.0) == 0.0, "and at p=0 it is perfect")
check(abs(code.logical_error_ideal(3, 0.05) - 0.00725) < 1e-5, "d=3 at p=0.05 is 0.00725")

wrong, trials = sim.sample_bitflips(3, 0.1, 20000, seed=1)
check(abs(wrong / trials - 0.028) < 0.003, "the Monte Carlo agrees with the binomial")

for bad in (1.5, -0.1):
    try:
        code.logical_error_ideal(3, bad)
    except ValueError:
        check(True, f"p={bad} is refused")
    else:
        check(False, f"p={bad} is refused")

check(sim.break_even(3) == 0.5, "a single-axis code breaks even at one half")
check(sim.break_even(5) == 0.5, "whatever the distance")

# -- the axes -----------------------------------------------------------
section("the axes")
check(abs(sim.phase_flip_error(3, 0.05) - 0.1355) < 1e-3, "the phase error at d=3, p=0.05 is 0.1355")
check(abs(sim.phase_flip_error(7, 0.05) - 0.2609) < 1e-3, "and at d=7 it is 0.2609")
check(sim.phase_flip_error(7, 0.05) > sim.phase_flip_error(3, 0.05), "the phase axis gets worse with distance")
check(code.logical_error_ideal(7, 0.05) < code.logical_error_ideal(3, 0.05), "the bit axis gets better")

combined = code.logical_error_ideal(3, 0.005) + sim.phase_flip_error(3, 0.005)
check(abs(combined - 0.0149) < 0.001, "the depolarising total at d=3, p=0.01 is about 0.0149")
check(combined > 0.01, "which is worse than the bare qubit's 0.01")

# -- the device ---------------------------------------------------------
section("the device")
record = json.loads((ROOT / "runs/0029-ibm-fez-idle/result.json").read_text())
rows = sim.device_table(record)
check(record["backend"] == "ibm_marrakesh", "the run is on ibm_marrakesh")
check(len(rows) == 12, "twelve circuits came back")
check(record["shots"] == 4096, "at 4,096 shots")

by = {(row["distance"], row["prepared"], row["idle_us"]): row for row in rows}
check(abs(by[(3, 1, 20.0)]["physical"] - 0.1130) < 0.005, "d=3 at 20 us has a physical rate of 0.113")
check(abs(by[(3, 1, 20.0)]["logical"] - 0.0369) < 0.003, "and a logical rate of 0.037")
check(abs(by[(5, 1, 20.0)]["logical"] - 0.0156) < 0.003, "d=5 at 20 us is 0.0156")
check(by[(3, 1, 20.0)]["logical"] > by[(5, 1, 20.0)]["logical"], "so the distance helps")

predicted = code.logical_error_ideal(3, by[(3, 1, 20.0)]["physical"])
check(abs(predicted - by[(3, 1, 20.0)]["logical"]) < 0.005, "the binomial predicts the measured value")
check(abs(code.logical_error_ideal(5, by[(5, 1, 60.0)]["physical"]) - by[(5, 1, 60.0)]["logical"]) < 0.01,
      "and it predicts the d=5 sixty-microsecond row too")

check(abs(by[(3, 1, 60.0)]["logical"] / by[(5, 1, 60.0)]["logical"] - 1.17) < 0.1,
      "at sixty microseconds the distance buys only 1.2")
check(abs(by[(3, 1, 20.0)]["logical"] / by[(5, 1, 20.0)]["logical"] - 2.37) < 0.15,
      "at twenty microseconds it buys 2.4")

flat = [by[(distance, 0, idle)]["logical"] for distance in (3, 5) for idle in (0.0, 20.0, 60.0)]
check(max(flat) < 0.005, "the prepared-0 rows stay flat")
low, high = code.wilson(0.0, 4096)
check(high < 0.001, "a zero in 4,096 shots is below 0.001 at 95%")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
