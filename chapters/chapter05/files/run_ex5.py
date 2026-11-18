"""Chapter 5 harness: intervals, budgets, readout calibration and correction.

Run: python3 chapters/chapter05/files/run_ex5.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

import calibrate
from stats import (
    DEFAULT_ORDER,
    bonferroni,
    clip_and_renormalize,
    combine_independent,
    confusion,
    counts_to_distribution,
    frequency,
    interval_width,
    invert,
    shots_for,
    standard_error,
    total_variation,
    wilson,
    z_score,
)

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

# -- frequencies --------------------------------------------------------
section("frequencies and intervals")
check(frequency(50, 100) == 0.5, "50 of 100 is one half")
check(abs(standard_error(0.5, 100) - 0.05) < 1e-12, "the error of a half at 100 shots is 0.05")
check(abs(standard_error(0.5, 400) - 0.025) < 1e-12, "four times the shots halves the error")

low, high = wilson(500, 1000)
check(abs(low - 0.4691) < 0.001, "the 95% interval starts at 0.469")
check(abs(high - 0.5309) < 0.001, "and ends at 0.531")
check(low < 0.5 < high, "the estimate is inside its own interval")
check(interval_width(50, 100) > interval_width(5000, 10000), "more shots narrow the interval")

check(wilson(0, 20)[0] == 0.0, "zero successes cannot go below zero")
check(abs(wilson(0, 20)[1] - 0.1611) < 0.001, "and have a finite upper bound")
check(wilson(20, 20)[1] == 1.0, "all successes end at exactly one")
check(abs(wilson(20, 20)[0] - 0.8389) < 0.001, "and have a finite lower bound")

for bad in ((11, 10), (-1, 10), (5, 0)):
    try:
        wilson(*bad)
    except ValueError:
        check(True, f"wilson{bad} is refused")
    else:
        check(False, f"wilson{bad} is refused")

# -- budgets ------------------------------------------------------------
section("shot budgets")
check(shots_for(0.05) == 385, "five points needs 385 shots at p=0.5")
check(shots_for(0.01) == 9604, "one point needs 9604")
check(shots_for(0.05, p=0.9) < shots_for(0.05), "a skewed p needs fewer shots")
try:
    shots_for(0.0)
except ValueError:
    check(True, "zero precision is refused")
else:
    check(False, "zero precision is refused")

check(bonferroni(0.05, 4) == 0.0125, "four tests at family 5% need 1.25% each")
check(bonferroni(0.05, 16) < bonferroni(0.05, 4), "more tests need a smaller threshold")

# -- combination --------------------------------------------------------
section("combining estimates")
value, error = combine_independent([0.5, 0.5], [0.02, 0.02])
check(abs(value - 1.0) < 1e-12, "two halves sum to one")
check(abs(error - math.sqrt(0.0008)) < 1e-12, "errors add in quadrature")
try:
    combine_independent([0.5], [0.02, 0.02])
except ValueError:
    check(True, "mismatched lengths are refused")
else:
    check(False, "mismatched lengths are refused")

# -- readout ------------------------------------------------------------
section("the readout matrix")
record = calibrate.load()
matrix = calibrate.matrix(record)
check(matrix.shape == (4, 4), "a two-qubit readout matrix is 4x4")
check(np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9), "every row is a distribution")
check(abs(calibrate.diagonal_error(matrix) - 0.0434) < 0.001, "the average readout error is 4.3%")
check(np.linalg.det(matrix) > 0.8, "the matrix is far from singular")
check(matrix[0, 0] > 0.97, "|00> is read correctly 97.9% of the time")
check(matrix[3, 3] > 0.93, "|11> is read correctly 93.2% of the time")
check(calibrate.expected_key([1]) == "10", "X on wire 1 is Qiskit key 10")
check(calibrate.expected_key([0]) == "01", "X on wire 0 is Qiskit key 01")
check(calibrate.expected_key([0, 1]) == "11", "both wires are 11")

try:
    invert(np.eye(4) * 0.0)
except ValueError:
    check(True, "a zero matrix is refused as singular")
else:
    check(False, "a zero matrix is refused as singular")

try:
    invert(np.array([[0.5, 0.4], [0.5, 0.6]]))
except ValueError:
    check(True, "rows that do not sum to one are refused")
else:
    check(False, "rows that do not sum to one are refused")

# -- correction ---------------------------------------------------------
section("correcting the CHSH data")
inverse = invert(matrix)
chsh = json.loads((ROOT / "runs/0007-ibm-chsh/result.json").read_text())
values = calibrate.corrected_chsh(chsh["counts"], inverse)

check(abs(calibrate.chsh_from(values, "raw") - 2.541) < 0.01, "the raw S is 2.541")
check(abs(calibrate.chsh_from(values, "corrected") - 2.7796) < 0.01, "the corrected S is 2.780")
check(calibrate.chsh_from(values, "corrected") > calibrate.chsh_from(values, "raw"),
      "correction increases S")
check(calibrate.chsh_from(values, "corrected") < 2.828427124746 + 1e-9,
      "the corrected S stays under the quantum maximum")
check(all(row["clipped_mass"] == 0.0 for row in values.values()), "no mass was clipped")
check(abs(values["ab"]["raw"] - 0.6016) < 0.001, "the first setting is 0.6016 raw")
check(abs(values["ab"]["corrected"] - 0.6551) < 0.001, "and 0.6551 corrected")
check(abs(values["a_prime_b_prime"]["corrected"] - 0.7484) < 0.001,
      "one setting overshoots the ideal 0.7071")

# -- bias and variance --------------------------------------------------
section("correction removes bias and adds variance")
TRUE = np.array([0.4268, 0.0732, 0.0732, 0.4268])
seen = matrix.T @ TRUE
rng = np.random.default_rng(4)
raw_values, fixed_values = [], []
for _ in range(400):
    counts = rng.multinomial(1024, seen)
    distribution = counts / 1024
    corrected, _ = calibrate.correct_distribution(distribution, inverse)
    raw_values.append(calibrate.expectation(distribution))
    fixed_values.append(calibrate.expectation(corrected))
raw = np.array(raw_values)
fixed = np.array(fixed_values)
truth = calibrate.expectation(TRUE)

check(abs(raw.mean() - truth) > 0.04, "the raw estimate is biased by more than four points")
check(abs(fixed.mean() - truth) < 0.01, "the corrected estimate is unbiased within one point")
check(fixed.std(ddof=1) > raw.std(ddof=1), "the corrected estimate has a wider spread")
check(fixed.std(ddof=1) - raw.std(ddof=1) < 0.01, "but not much wider")

# -- the second domain --------------------------------------------------
section("the same arithmetic elsewhere")
check(clip_and_renormalize(np.array([0.6, 0.6, -0.2]))[1] > 0.0, "clipping reports the mass lost")
clipped, mass = clip_and_renormalize(np.array([0.6, 0.6, -0.2]))
check(abs(clipped.sum() - 1.0) < 1e-12, "the clipped vector is renormalized")
check(abs(total_variation([0.5, 0.5], [0.5, 0.5])) < 1e-12, "identical distributions are zero apart")
check(abs(total_variation([1.0, 0.0], [0.0, 1.0]) - 1.0) < 1e-12, "disjoint distributions are one apart")

check(abs(z_score(520, 1000, 0.5) - 1.2649) < 0.001, "520 of 1000 is 1.26 sigma from a half")
try:
    z_score(500, 1000, 1.0)
except ValueError:
    check(True, "a certain expectation has no z score")
else:
    check(False, "a certain expectation has no z score")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
