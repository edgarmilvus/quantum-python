"""Chapter 1 exercise harness: runs every exercise's checks.

Run: python3 chapters/chapter01/files/exercises/run_exercises.py
Prints "NN/NN exercise checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import ex1_normalize
import ex2_measure_many
import ex3_shots
import ex4_float32
import ex5_report

count = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global count
    count += 1
    if not condition:
        failures.append(description)


MODULES = [
    ("exercise 1 (repair)", ex1_normalize),
    ("exercise 2 (extend)", ex2_measure_many),
    ("exercise 3 (measure)", ex3_shots),
    ("exercise 4 (break)", ex4_float32),
    ("exercise 5 (integrate)", ex5_report),
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
