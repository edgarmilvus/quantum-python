"""Chapter 13 exercise harness: runs every exercise's checks.

Run: python3 chapters/chapter18/files/exercises/run_exercises.py
     python3 chapters/chapter18/files/exercises/run_exercises.py --only 4
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ex1_metric
import ex2_signal
import ex3_floor
import ex4_compare
import ex5_bench

count = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global count
    count += 1
    if not condition:
        failures.append(description)


MODULES = [
    ("exercise 1 (repair)", ex1_metric),
    ("exercise 2 (extend)", ex2_signal),
    ("exercise 3 (measure)", ex3_floor),
    ("exercise 4 (break)", ex4_compare),
    ("exercise 5 (integrate)", ex5_bench),
]

selected = None
if len(sys.argv) == 3 and sys.argv[1] == "--only":
    selected = int(sys.argv[2])
    if not 1 <= selected <= len(MODULES):
        raise SystemExit(f"--only takes 1..{len(MODULES)}, got {selected}")

for position, (title, module) in enumerate(MODULES, start=1):
    if selected is not None and position != selected:
        continue
    print(f"\n== {title}")
    module.checks(check)

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{count}/{count} exercise checks passed" + (f" (exercise {selected})" if selected else ""))
