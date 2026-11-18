"""Chapter 4 harness: Bell pair, CHSH, the local model, and the recorded run.

Run: python3 chapters/chapter04/files/run_ex4.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

import bell

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

# -- the state ---------------------------------------------------------
section("the Bell pair")
state = bell.bell_state()
check(state.shape == (4,), "four amplitudes")
check(abs(np.sum(np.abs(state) ** 2) - 1.0) < 1e-12, "the state is normalized")
check(abs(abs(state[0]) ** 2 - 0.5) < 1e-12, "half the probability is at 00")
check(abs(abs(state[3]) ** 2 - 0.5) < 1e-12, "half the probability is at 11")
check(abs(state[1]) < 1e-12 and abs(state[2]) < 1e-12, "nothing at 01 or 10")
check(bell.bell_state().dtype == np.complex128, "the state is complex128")

# -- the expectations --------------------------------------------------
section("expectations")
for name, (angle_a, angle_b) in bell.SETTINGS.items():
    predicted = bell.predicted_expectation(angle_a, angle_b)
    simulated = bell.expectation_from_probabilities(bell.probabilities(angle_a, angle_b))
    check(abs(simulated - predicted) < 1e-12, f"{name} matches cos(a-b)")

check(abs(bell.simulate()["ab"] - math.sqrt(0.5)) < 1e-12, "E(0,45) is 0.7071")
check(abs(bell.simulate()["ab_prime"] + math.sqrt(0.5)) < 1e-12, "E(0,135) is -0.7071")

p = bell.probabilities(0.0, 45.0)
check(abs(p.sum() - 1.0) < 1e-12, "the distribution sums to one")
check(bell.expectation_from_probabilities([0.5, 0, 0, 0.5]) == 1.0, "same outcomes give E = 1")
check(bell.expectation_from_probabilities([0, 0.5, 0.5, 0]) == -1.0, "different outcomes give E = -1")

try:
    bell.expectation_from_probabilities([0.5, 0.5])
except ValueError:
    check(True, "a two-entry distribution is refused")
else:
    check(False, "a two-entry distribution is refused")

try:
    bell.expectation_from_probabilities([0.5, 0.5, 0.5, 0.5])
except ValueError:
    check(True, "a distribution that sums to two is refused")
else:
    check(False, "a distribution that sums to two is refused")

# -- from counts -------------------------------------------------------
section("expectations from counts")
rng = np.random.default_rng(3)
counts = {"00": 512, "01": 0, "10": 0, "11": 512}
check(bell.expectation_from_counts(counts) == 1.0, "perfectly correlated counts give 1")
check(bell.expectation_from_counts({"00": 0, "01": 500, "10": 524, "11": 0}) == -1.0,
      "perfectly anti-correlated counts give -1")

draws = rng.choice(4, size=10_000, p=p)
sampled = {"00": 0, "01": 0, "10": 0, "11": 0}
for draw in draws:
    sampled[format(int(draw), "02b")] += 1
check(abs(bell.expectation_from_counts(sampled) - math.sqrt(0.5)) < 0.03,
      "10k shots land within three points of 0.7071")

try:
    bell.expectation_from_counts({})
except ValueError:
    check(True, "an empty histogram is refused")
else:
    check(False, "an empty histogram is refused")

# -- S and the bounds --------------------------------------------------
section("the CHSH combination")
simulated = bell.simulate()
s = bell.chsh(simulated)
check(abs(s - 2.0 * math.sqrt(2.0)) < 1e-12, "an ideal pair gives 2 sqrt 2")
check(abs(bell.TSIRELSON_BOUND - 2.0 * math.sqrt(2.0)) < 1e-12, "the Tsirelson bound is 2 sqrt 2")
check(bell.CLASSICAL_BOUND == 2.0, "the classical bound is 2")
check(s - bell.CLASSICAL_BOUND > 0.8, "the ideal margin is above 0.8")

zero = {"ab": 0.0, "ab_prime": 0.0, "a_prime_b": 0.0, "a_prime_b_prime": 0.0}
check(bell.chsh(zero) == 0.0, "two independent qubits give S = 0")

try:
    bell.chsh({"ab": 0.7})
except ValueError:
    check(True, "a partial set of settings is refused")
else:
    check(False, "a partial set of settings is refused")

check(abs(bell.chsh({k: -v for k, v in simulated.items()}) + s) < 1e-12,
      "flipping every expectation flips S")

# -- errors ------------------------------------------------------------
section("error bars")
check(abs(bell.standard_error(0.5, 100) - math.sqrt(0.75) / 10) < 1e-12, "the shot error of E = 0.5 at 100 shots is 0.0866")
check(bell.standard_error(1.0, 100) == 0.0, "a certain expectation has no shot error")
check(bell.chsh_error(simulated, 1024) < 0.1, "four settings at 1024 shots give a small S error")

try:
    bell.standard_error(1.5, 10)
except ValueError:
    check(True, "an expectation above one is refused")
else:
    check(False, "an expectation above one is refused")

try:
    bell.standard_error(0.5, 0)
except ValueError:
    check(True, "zero shots is refused")
else:
    check(False, "zero shots is refused")

# -- the local model ---------------------------------------------------
section("the local hidden-variable model")
rng = np.random.default_rng(9)
angles = np.radians([0.0, 90.0])
settings_b = np.radians([45.0, 135.0])
hidden = rng.uniform(0.0, 2 * np.pi, size=20_000)
left = np.where(np.cos(angles[0] - hidden) >= 0, 1, -1)
right = np.where(np.cos(settings_b[0] - hidden) >= 0, 1, -1)
local_e = float(np.mean(left * right))
check(abs(local_e) <= 1.0, "a local expectation stays inside [-1, 1]")
check(abs(local_e - 0.5) < 0.05, "the local model gives about 0.5 at these angles")

# -- the recorded run --------------------------------------------------
section("the recorded run")
record = json.loads((ROOT / "runs/0007-ibm-chsh/result.json").read_text())
check(record["backend"] == "ibm_fez", "the run is from ibm_fez")
check(record["shots"] == 1024, "1024 shots per setting")
check(len(record["counts"]) == 4, "four settings were measured")
check(record["transpiled_depths"] == [8, 8, 8, 8], "every circuit ran at depth 8")
for name, counts in record["counts"].items():
    check(sum(counts.values()) == 1024, f"{name} counts add up to the shots")

measured = {name: bell.expectation_from_counts(c) for name, c in record["counts"].items()}
s_measured = bell.chsh(measured)
check(abs(s_measured - 2.541) < 0.01, "S measured is 2.541")
check(s_measured > bell.CLASSICAL_BOUND, "the device violated the classical bound")
check(s_measured < bell.TSIRELSON_BOUND, "and stayed below the quantum one")
sigma = bell.violation_sigma(measured, record["shots"])
check(sigma > 5, "the violation is more than five sigma")
check(abs((s_measured - 2) / (2.828427124746 - 2) - 0.653) < 0.01, "65% of the ideal violation survived")
check(abs(measured["ab_prime"] + 0.6426) < 0.01, "the anti-correlated setting is negative")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
