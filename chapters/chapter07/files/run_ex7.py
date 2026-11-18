"""Chapter 7 harness: oracle, diffusion, the curve, the optimum, the device.

Run: python3 chapters/chapter07/files/run_ex7.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import grover

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

# -- the operators ------------------------------------------------------
section("the oracle and the diffusion")
for n in (2, 3, 4):
    size = 1 << n
    flip = grover.oracle(2, n) if size > 2 else grover.oracle(1, n)
    check(np.allclose(np.abs(np.diag(flip)), 1.0), f"n={n}: the oracle is diagonal with unit entries")
    check(np.allclose(flip @ flip, np.eye(size)), f"n={n}: applying the oracle twice is the identity")
    check(np.linalg.det(flip) < 0, f"n={n}: the determinant is minus one")

    mirror = grover.diffusion(n)
    check(np.allclose(mirror.conj().T @ mirror, np.eye(size)), f"n={n}: the diffusion is unitary")
    s = grover.uniform(n)
    expected = 2 * np.outer(s, s.conj()) - np.eye(size)
    check(np.allclose(mirror, expected), f"n={n}: the diffusion equals 2|s><s| - I")

try:
    grover.oracle(8, 3)
except ValueError:
    check(True, "a marked index outside the register is refused")
else:
    check(False, "a marked index outside the register is refused")

# -- one iteration ------------------------------------------------------
section("one iteration")
state = grover.uniform(3)
check(abs(grover.probabilities(state).sum() - 1.0) < 1e-12, "the uniform state is normalized")
check(np.allclose(grover.probabilities(state), np.ones(8) / 8), "every item starts at one eighth")

after = grover.iterate(5, 3, 1)
check(abs(grover.probabilities(after)[5] - 0.78125) < 1e-9, "one iteration raises the marked item to 0.78125")
check(grover.probabilities(after)[5] > 6 * grover.probabilities(after)[0],
      "the marked item is at least six times any other")

# -- the curve ----------------------------------------------------------
section("the curve")
for n in (3, 4, 5):
    size = 1 << n
    steps = grover.optimal_iterations(size)
    numeric = grover.success_probability(0, n, steps)
    analytic = grover.analytic_success(size, steps)
    check(abs(numeric - analytic) < 1e-12, f"n={n}: the simulated curve matches the formula")

check(abs(grover.success_probability(0, 3, 0) - 0.125) < 1e-12, "at n=3 with no iterations the chance is one eighth")
check(abs(grover.success_probability(0, 3, 1) - 0.78125) < 1e-12, "after one it is 0.78125")
check(abs(grover.success_probability(0, 3, 2) - 0.9453125) < 1e-9, "after two it is 0.9453")
check(grover.success_probability(0, 3, 3) < 0.4, "after three it has fallen below 0.4")
check(grover.success_probability(0, 3, 4) < 0.05, "after four it is under five percent")
check(grover.success_probability(0, 3, 5) > grover.success_probability(0, 3, 4),
      "and the curve turns back up, as the rotation predicts")

# -- the optimum --------------------------------------------------------
section("the optimum")
check(grover.optimal_iterations(4) == 1, "four items need one iteration")
check(grover.optimal_iterations(8) == 2, "eight need two")
check(grover.optimal_iterations(16) == 3, "sixteen need three")
check(grover.optimal_iterations(2) == 1, "two items need one")
check(grover.optimal_iterations(1024) == 25, "a thousand items need twenty-five")

check(abs(grover.success_probability(0, 2, 1) - 1.0) < 1e-12, "at N=4 one iteration is certain")
check(abs(grover.success_probability(0, 2, 2) - 0.25) < 1e-12, "and two iterations undo it")
check(grover.approx_iterations(4) == 2, "the textbook approximation asks for two at N=4")
check(grover.approx_iterations(8) == 2, "and agrees with the exact count at N=8")

check(grover.classical_queries(8) == 4, "linear search needs four queries at N=8")
check(grover.classical_queries(1024) == 512, "and 512 at N=1024")
check(grover.binary_search_queries(1024) == 10, "a binary search needs ten")
check(grover.binary_search_queries(1) == 1, "and one for a single item")
check(grover.optimal_iterations(1024) > grover.binary_search_queries(1024),
      "Grover is worse than a binary search at N=1024")

for bad in (0, 1):
    try:
        grover.optimal_iterations(bad)
    except ValueError:
        check(True, f"N={bad} is refused")
    else:
        check(False, f"N={bad} is refused")

# -- the device ---------------------------------------------------------
section("the recorded device run")
record = json.loads((ROOT / "runs/0013-ibm-grover/result.json").read_text())
counts = record["counts"]
total = sum(counts.values())
marked = record["marked_bits"]
top = max(counts, key=counts.get)

check(record["n"] == 3, "three qubits")
check(record["steps"] == 2, "two iterations")
check(total == 1024, "the counts add up to the shots")
check(top == marked, "the most frequent outcome is the marked item")
check(counts.get(marked, 0) / total > 4 * (1 / 8),
      "the marked item beats uniform guessing by more than four times")
check(record["transpiled_depth"] > 100, "the compiled circuit is deeper than a hundred layers")
check(abs(record["ideal_probability"] - 0.9453125) < 1e-9, "the simulator predicted 0.9453")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
