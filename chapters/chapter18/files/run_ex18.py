"""Chapter 18 harness: the task, the metric, the sources, and the table.

Run: python3 chapters/chapter18/files/run_ex18.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bench import sources, task

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the task -----------------------------------------------------------
section("the task")
ops = task.ghz_ops(3)
check(len(ops) == 3, "a three-qubit GHZ is three operations")
check(ops[0] == ("h", (0,)), "the first is a Hadamard")
check(ops[1] == ("cx", (0, 1)) and ops[2] == ("cx", (1, 2)), "and then a CX chain")

ideal = task.ideal_distribution(3)
check(ideal == {"000": 0.5, "111": 0.5}, "the ideal is two outcomes at one half")
check(abs(sum(ideal.values()) - 1.0) < 1e-12, "and it sums to one")

for bad in (0, 1):
    try:
        task.ghz_ops(bad)
    except ValueError:
        check(True, f"a {bad}-qubit GHZ is refused")
    else:
        check(False, f"a {bad}-qubit GHZ is refused")

check(task.normalise({"00": 1, "11": 3}) == {"00": 0.25, "11": 0.75}, "counts normalise to a distribution")
try:
    task.normalise({})
except ValueError:
    check(True, "an empty histogram is refused")
else:
    check(False, "an empty histogram is refused")

# -- the metric ---------------------------------------------------------
section("the metric")
perfect = {"000": 2048, "111": 2048}
check(task.total_variation(perfect, ideal) == 0.0, "an exact histogram has distance zero")
check(task.signal(perfect) == 1.0, "and all of its signal is on the two outcomes")

half = {"000": 2048, "111": 1024, "001": 1024}
check(abs(task.total_variation(half, ideal) - 0.25) < 0.01, "moving a quarter of the mass costs 0.25")
check(abs(task.signal(half) - 0.75) < 0.01, "and the signal is three quarters")

missing = {"000": 4096}
check(abs(task.total_variation(missing, ideal) - 0.5) < 1e-12, "a run that never saw 111 is half the distance away")
check(abs(task.signal(missing) - 1.0) < 1e-12, "but its signal is one, because it saw only 000")

floor = task.noise_floor(4096, ideal)
check(0.0 < floor < 0.03, "the 4,096-shot floor is below three points")
check(task.noise_floor(16384, ideal) < floor, "more shots lower the floor")
check(abs(task.noise_floor(1024, ideal) / task.noise_floor(4096, ideal) - 2.0) < 0.5,
      "a quarter of the shots roughly doubles it")

# -- the sources --------------------------------------------------------
section("the sources")
rows = sources.ibm_ghz()
check(len(rows) == 2, "the IBM job has two rows")
check(abs(rows[0].tvd - 0.0681) < 0.005, "with no delay the distance is 0.068")
check(abs(rows[1].tvd - 0.1616) < 0.005, "with a 20 microsecond delay it is 0.162")
check(rows[0].shots == 4096, "at 4,096 shots")
check(rows[0].cost_usd == 0.0, "and no dollars, because the plan bills runtime")

aggregator = sources.qbraid_ghz()
check(aggregator.tvd < 1e-9, "the qBraid row is exactly zero")
check(aggregator.kind == "sim", "because it is a simulator")

local = sources.local_ghz()
check(abs(local.tvd - floor) < 0.02, "the local row is the floor, within seed noise")

bell = sources.bell_rows()
check(len(bell) == 3, "three Bell sources are recorded")
values = {row.source: row.tvd for row in bell}
check(abs(values["ibm_fez"] - 0.0537) < 0.005, "the device is 0.054 from ideal")
check(abs(values["quantum inspire emulator"] - 0.0205) < 0.005, "the emulator 0.021")
check(values["IonQ simulator"] < 1e-9, "and the ideal simulator zero")

ranked = sources.by_provider(bell + [local])
check(list(ranked)[0] in ("ionq", "qi"), "a simulator or the emulator ranks first")
check(ranked["ibm"] > ranked["qi"], "the device ranks below the emulator")

# -- the prices ---------------------------------------------------------
section("the prices")
check(abs(sources.quoted("ionq", 4096) - 328.0) < 1.0, "4,096 IonQ shots would cost 328 dollars")
check(abs(sources.quoted("braket-iqm", 4096) - 6.85) < 0.2, "and 6.85 on the cheapest Braket device")
check(sources.quoted("local", 4096) == 0.0, "a local run costs nothing")
check(sources.quoted("ibm", 4096) == 0.0, "and the open plan bills runtime, not shots")

try:
    sources.quoted("nonsense", 100)
except KeyError:
    check(True, "an unknown provider has no price")
else:
    check(False, "an unknown provider has no price")

try:
    sources.quoted("ionq", 0)
except ValueError:
    check(True, "a zero-shot quote is refused")
else:
    check(False, "a zero-shot quote is refused")

# -- the table ----------------------------------------------------------
section("the table")
all_rows = rows + [aggregator, local]
text = task.table(all_rows)
check(text.count("\n") == len(all_rows), "one line per row plus the header")
check("ibm_kingston" in text and "qbraid" in text, "the table names the sources")

spread = task.improvements(all_rows)
check(spread["worst"] > spread["best"], "the spread is positive")
check(spread["spread"] > 0.05, "and larger than five points")

try:
    task.improvements(rows[:1])
except ValueError:
    check(True, "a comparison of one row is refused")
else:
    check(False, "a comparison of one row is refused")

try:
    task.Row(source="x", provider="x", kind="sim", tvd=1.5, shots=10, wall_seconds=0, cost_usd=0)
except ValueError:
    check(True, "a distance above one is refused")
else:
    check(False, "a distance above one is refused")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
