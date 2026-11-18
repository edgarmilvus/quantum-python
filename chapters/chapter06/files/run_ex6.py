"""Chapter 6 harness: oracles, phase kickback, DJ, BV, and the promise.

Run: python3 chapters/chapter06/files/run_ex6.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from algorithms import (
    amplitude_pattern,
    bernstein_vazirani,
    classical_queries_bernstein_vazirani,
    classical_queries_deutsch_jozsa,
    deutsch_jozsa,
    deutsch_jozsa_answer,
    most_likely,
    query_counts,
)
from oracle import balanced, bits, constant, index, is_balanced, linear, permutation

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

# -- the oracle ---------------------------------------------------------
section("an oracle is a permutation")
for n in (1, 2, 3):
    matrix = permutation(lambda x: x & 1, n)
    check(np.allclose(matrix.sum(axis=0), 1.0), f"n={n}: every column has one entry")
    check(np.allclose(matrix.sum(axis=1), 1.0), f"n={n}: every row has one entry")
    check(matrix.shape == (1 << (n + 1),) * 2, f"n={n}: the matrix is {1 << (n + 1)} square")

one = permutation(lambda x: 1, 2)
check(one.shape == (8, 8), "two input bits give an eight-amplitude permutation")
check(index(3, 1) == 7, "the last amplitude is x=11, y=1")

try:
    permutation(lambda x: 2, 2)
except ValueError:
    check(True, "a function returning 2 is refused")
else:
    check(False, "a function returning 2 is refused")

try:
    permutation(lambda x: 0, 0)
except ValueError:
    check(True, "zero input bits are refused")
else:
    check(False, "zero input bits are refused")

check(bits(5, 3) == [1, 0, 1], "bits(5, 3) is 101")

# -- the functions ------------------------------------------------------
section("the oracle families")
check([constant(0)(x) for x in range(4)] == [0, 0, 0, 0], "constant zero on four inputs")
check([constant(1)(x) for x in range(4)] == [1, 1, 1, 1], "constant one on four inputs")
check(is_balanced(balanced(1, 2), 2), "the mask-1 function is balanced")
check(is_balanced(balanced(3, 2), 2), "the mask-3 function is balanced")
check([linear(5, 3)(x) for x in range(8)] == [bin(x & 5).count("1") % 2 for x in range(8)],
      "the linear family is parity of the mask")

try:
    balanced(0, 2)
except ValueError:
    check(True, "a zero mask is refused as a balanced function")
else:
    check(False, "a zero mask is refused as a balanced function")

try:
    balanced(4, 2)
except ValueError:
    check(True, "a mask that does not fit is refused")
else:
    check(False, "a mask that does not fit is refused")

# -- phase kickback -----------------------------------------------------
section("phase kickback")
pattern_zero = amplitude_pattern(constant(0), 2)
pattern_one = amplitude_pattern(constant(1), 2)
pattern_bal = amplitude_pattern(balanced(1, 2), 2)

check(all(value > 0 for value in pattern_zero.values()), "a constant zero writes no sign")
check(all(value < 0 for value in pattern_one.values()), "a constant one writes a sign on every amplitude")
check(any(value > 0 for value in pattern_bal.values()) and any(value < 0 for value in pattern_bal.values()),
      "a balanced function writes a mixed pattern")
check(abs(pattern_zero["00"] - 1 / np.sqrt(8)) < 1e-12, "the amplitudes are uniform at 1/sqrt(8)")

# -- Deutsch-Jozsa ------------------------------------------------------
section("Deutsch-Jozsa")
for n in (1, 2, 3, 4):
    for value in (0, 1):
        distribution = deutsch_jozsa(constant(value), n)
        check(abs(max(distribution.values()) - 1.0) < 1e-12, f"n={n}: a constant function gives a certain outcome")
        check(deutsch_jozsa_answer(distribution) == "constant", f"n={n}: and it is labelled constant")
        check(distribution[format(0, f"0{n}b")] > 0.99, f"n={n}: the outcome is the zero string")

    balanced_distribution = deutsch_jozsa(balanced(1, n), n)
    check(abs(max(balanced_distribution.values()) - 1.0) < 1e-12, f"n={n}: a balanced function is also certain")
    check(deutsch_jozsa_answer(balanced_distribution) == "balanced", f"n={n}: and it is labelled balanced")
    check(balanced_distribution[format(0, f"0{n}b")] < 1e-12, f"n={n}: the zero string never appears")

check(classical_queries_deutsch_jozsa(constant(0), 4) == 9, "a constant function costs nine classical queries at four bits")
check(classical_queries_deutsch_jozsa(balanced(1, 4), 4) == 2, "a balanced one can cost two")
check(query_counts(4, 5)["deutsch_jozsa_constant"] == (9, 1), "the table says nine against one")

# -- Bernstein-Vazirani -------------------------------------------------
section("Bernstein-Vazirani")
for n in (1, 2, 3, 4):
    for secret in range(1, 1 << n):
        label, probability = most_likely(bernstein_vazirani(secret, n))
        check(label == format(secret, f"0{n}b"), f"n={n} secret {secret}: the secret comes back")
        check(abs(probability - 1.0) < 1e-12, f"n={n} secret {secret}: with probability one")

check(classical_queries_bernstein_vazirani(5, 3) == 3, "three bits need three classical queries")

try:
    bernstein_vazirani(8, 3)
except ValueError:
    check(True, "a secret that does not fit is refused")
else:
    check(False, "a secret that does not fit is refused")

# -- the promise --------------------------------------------------------
section("the promise")
total_functions = 1 << (1 << 2)
labels = {"constant": 0, "balanced": 0, "neither": 0}
right = 0
for value in range(total_functions):
    f = lambda x, v=value: (v >> x) & 1
    answers = {f(x) for x in range(4)}
    if len(answers) == 1:
        truth = "constant"
    elif answers == {0, 1} and sum((value >> x) & 1 for x in range(4)) == 2:
        truth = "balanced"
    else:
        truth = "neither"
    labels[truth] += 1
    answer = deutsch_jozsa_answer(deutsch_jozsa(f, 2))
    if answer == truth:
        right += 1

check(total_functions == 16, "two bits have sixteen functions")
check(labels["constant"] == 2, "two of them are constant")
check(labels["balanced"] == 6, "six are balanced")
check(labels["neither"] == 8, "eight are neither")
check(right == 8, "the algorithm labels only the promised eight correctly")

# -- the recorded run ---------------------------------------------------
section("the recorded device run")
record = json.loads((ROOT / "runs/0011-ibm-bv/result.json").read_text())
check(record["secret_bits"] == "101", "the secret submitted was 101")
check(record["n"] == 3, "three input bits")
check(sum(record["counts"].values()) == 1024, "the counts add up to the shots")
top = max(record["counts"], key=record["counts"].get)
check(top == "101", "the most frequent outcome is the secret")
check(record["counts"]["101"] == 965, "it came back 965 times")
check(abs(record["counts"]["101"] / 1024 - 0.9424) < 1e-4, "which is 94.2%")
check(len(record["counts"]) == 5, "five outcomes appeared out of eight")
check(record["transpiled_depth"] >= 5, "the circuit ran at depth at least five")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
