"""Chapter 13 harness: the graph, the state, the optimiser, and the device.

Run: python3 chapters/chapter13/files/run_ex13.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from qaoa import graph as g, optimize, qaoa, state as st

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

# -- the graph ----------------------------------------------------------
section("the graph")
instance = g.square_with_diagonal()
check(instance.n == 4 and instance.m == 5, "the instance has 4 vertices and 5 edges")
check(instance.cut(0b0101) == 4.0, "0101 cuts all five edges")
check(instance.cut(0b1010) == 4.0, "and so does its complement")
check(instance.cut(0b0000) == 0.0, "one side holds everything, so nothing crosses")
check(instance.max_cut()[0] == 4.0, "the optimum is 4")
check(instance.uniform_mean() == 2.5, "a uniform guess averages 2.5")
check(instance.spectrum() == {0.0: 2, 2.0: 4, 3.0: 8, 4.0: 2}, "the spectrum is 2/4/8/2")
check(sum(instance.spectrum().values()) == 16, "and covers all sixteen assignments")

for bad in (1, 0, -3):
    try:
        g.Graph(n=bad, edges=((0, 1, 1.0),))
    except ValueError:
        check(True, f"{bad} vertices is refused")
    else:
        check(False, f"{bad} vertices is refused")

for edges, why in (
    (((0, 0, 1.0),), "a self-loop"),
    (((0, 1, 0.0),), "a zero weight"),
    (((0, 1, -1.0),), "a negative weight"),
    (((0, 1, 1.0), (1, 0, 1.0)), "a repeated edge"),
):
    try:
        g.Graph(n=2, edges=edges)
    except ValueError:
        check(True, f"{why} is refused")
    else:
        check(False, f"{why} is refused")

ring = g.ring(4)
check(ring.max_cut()[0] == 4.0, "a 4-ring has max cut 4")
check(g.ring(5).max_cut()[0] == 4.0, "a 5-ring has max cut 4, one edge short")
check(g.complete(4).max_cut()[0] == 4.0, "K4 has max cut 4")

# -- the state ----------------------------------------------------------
section("the state")
vector = st.zero(2)
check(abs(st.norm(vector) - 1.0) < 1e-12, "the zero state is normalised")
superposition = st.h(st.h(vector, 0), 1)
check(float(np.max(np.abs(superposition - 0.5))) < 1e-12, "two Hadamards make four equal amplitudes")
check(abs(st.norm(superposition) - 1.0) < 1e-12, "and keep it normalised")

rotated = st.rx(st.zero(1), 0, np.pi / 2)
check(abs(abs(rotated[0]) ** 2 - 0.5) < 1e-12, "RX(pi/2) takes |0> to an equal superposition")

# RZZ on |11> is a phase, on |10> it is not
pair = np.zeros(4, dtype=complex)
pair[3] = 1.0
phased = st.rzz(pair, 0, 1, 0.7)
check(abs(abs(phased[3]) - 1.0) < 1e-12, "RZZ leaves the population of |11> alone")
check(abs(np.angle(phased[3]) + 0.35) < 1e-9, "and phases it by -theta/2")

for bad in (0, -1):
    try:
        st.zero(bad)
    except ValueError:
        check(True, f"{bad} wires is refused")
    else:
        check(False, f"{bad} wires is refused")

# -- the qaoa state -----------------------------------------------------
section("the QAOA state")
unchanged = qaoa.state_for(instance, [0.0], [0.0])
check(abs(st.norm(unchanged) - 1.0) < 1e-12, "the circuit keeps the state normalised")
check(abs(qaoa.expected_cut(instance, unchanged) - 2.5) < 1e-9,
      "at zero angles the expected cut is the uniform mean")

optimum_point = qaoa.state_for(instance, [0.3109], [0.5713])
mean = qaoa.expected_cut(instance, optimum_point)
check(abs(mean - 3.2371) < 1e-3, "the optimal one-layer state averages 3.2371")
check(abs(qaoa.approximation_ratio(mean, 4.0) - 0.8093) < 1e-3, "which is 0.8093 of the optimum")
distribution = qaoa.distribution_over_cuts(instance, optimum_point)
check(abs(distribution[4.0] - 0.3281) < 1e-3, "32.8% of the probability sits on the optimal cuts")
check(abs(distribution[3.0] - 0.6110) < 1e-3, "and 61.1% on the near misses")
check(abs(sum(distribution.values()) - 1.0) < 1e-12, "the histogram sums to one")

# -- the gradient -------------------------------------------------------
section("the gradient")
for beta, gamma in ((0.3, 0.6), (0.42, 1.13), (0.9, 0.2)):
    d_beta, d_gamma = qaoa.gradient(instance, [beta], [gamma])
    epsilon = 1e-5

    def f(b: float, ga: float) -> float:
        return qaoa.expected_cut(instance, qaoa.state_for(instance, [b], [ga]))

    finite_beta = (f(beta + epsilon, gamma) - f(beta - epsilon, gamma)) / (2 * epsilon)
    finite_gamma = (f(beta, gamma + epsilon) - f(beta, gamma - epsilon)) / (2 * epsilon)
    check(abs(d_beta[0] - finite_beta) < 1e-6, f"the beta gradient matches at ({beta}, {gamma})")
    check(abs(d_gamma[0] - finite_gamma) < 1e-6, f"the gamma gradient matches at ({beta}, {gamma})")

d_betas, d_gammas = qaoa.gradient(instance, [0.2, 0.5], [0.7, 1.1])
check(len(d_betas) == 2 and len(d_gammas) == 2, "a two-layer circuit has four derivatives")

# -- the optimiser ------------------------------------------------------
section("the optimiser")
grid = optimize.grid_search(instance, 1, 12, 12)
check(abs(grid.cost - 3.2316) < 1e-3, "a 12 by 12 grid finds 3.2316")
check(grid.evaluations == 144, "in 144 evaluations")

peak, value = optimize.nelder_mead(
    lambda point: -float(np.sum((np.array(point) - np.array([0.4, 0.7])) ** 2)), [0.0, 0.0], step=0.3
)
check(abs(value) < 1e-6, "the simplex maximises a known quadratic")
check(np.allclose(peak, [0.4, 0.7], atol=1e-3), "and lands on its peak")

best = optimize.optimise(instance, 1)
check(abs(best.cost - 3.2371) < 1e-3, "the chapter's p=1 optimum is 3.2371")
check(abs(best.betas[0] - 0.3109) < 1e-3, "at beta 0.3109")
check(abs(best.gammas[0] - 0.5713) < 1e-3, "and gamma 0.5713")
check(best.evaluations < 400, "in under four hundred evaluations")

deeper = optimize.optimise(instance, 2, restarts=8)
check(deeper.cost > best.cost, "two layers beat one")
check(abs(deeper.cost - 3.8558) < 1e-2, "and reach 3.8558 with eight starts")
check(abs(deeper.cost / 4.0 - 0.9640) < 1e-2, "which is 0.9640 of the optimum")

fewer = optimize.optimise(instance, 2, restarts=1)
check(fewer.cost < deeper.cost, "one start finds less than eight")
check(abs(fewer.cost - 3.4573) < 1e-2, "3.4573 against 3.8558")

# -- the budget ---------------------------------------------------------
section("the budget")
check(optimize.shots_to_resolve(0.05, 1.13) == 2044, "resolving 0.05 of cut needs 2,044 shots")
check(optimize.shots_to_resolve(0.1, 1.13) == 511, "resolving 0.10 needs 511")
check(optimize.shots_to_resolve(0.01, 1.13) == 51076, "resolving 0.01 needs 51,076")

budget = optimize.budget(1, 5, 1024, 20)
check(budget["circuits per gradient"] == 12, "one layer on five edges needs twelve circuits a gradient")
check(budget["circuits for the run"] == 240, "so twenty steps need 240")
check(budget["shots for the run"] == 245760, "and 245,760 shots")

for bad in (0.0, -0.1):
    try:
        optimize.shots_to_resolve(bad, 1.13)
    except ValueError:
        check(True, f"a gap of {bad} is refused")
    else:
        check(False, f"a gap of {bad} is refused")

# -- the device ---------------------------------------------------------
section("the device")
record = json.loads((ROOT / "runs/0022-ibm-fez-qaoa/result.json").read_text())
check(record["backend"] == "ibm_marrakesh", "the run is on ibm_marrakesh")
check(len(record["results"]) == 36, "36 circuits came back")
check(record["transpiled_depth"] == 76, "at depth 76")
check(record["shots"] == 1024, "with 1,024 shots each")

device_graph = g.Graph(n=record["graph"]["n"], edges=tuple(tuple(edge) for edge in record["graph"]["edges"]))
measured = []
simulated = []
for entry in record["results"]:
    counts = {int(key, 2): value for key, value in entry["counts"].items()}
    measured.append(qaoa.expected_cut_from_counts(device_graph, counts))
    simulated.append(
        qaoa.expected_cut(device_graph, qaoa.state_for(device_graph, [entry["beta"]], [entry["gamma"]]))
    )
measured_values = np.array(measured)
simulated_values = np.array(simulated)

correlation = float(np.corrcoef(simulated_values, measured_values)[0, 1])
check(correlation > 0.98, "the two surfaces correlate above 0.98")
check(int(np.argmax(measured_values)) == int(np.argmax(simulated_values)), "they peak at the same grid point")
check(abs(measured_values.max() - 3.1006) < 1e-2, "the measured peak is 3.1006")
check(abs(qaoa.approximation_ratio(measured_values.max(), 4.0) - 0.7751) < 1e-3, "0.7751 of the optimum")

slope, intercept = np.polyfit(simulated_values, measured_values, 1)
check(slope < 1.0, "the device compresses the landscape, so the slope is below one")
check(abs(slope * 2.5 + intercept - 2.5) < 0.01, "and the line passes through the uniform mean 2.5")
check(measured_values.min() > simulated_values.min(), "the troughs come up")
check(measured_values.max() < simulated_values.max(), "and the peaks come down")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
