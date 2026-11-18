"""Chapter 14 harness: the QUBO, the sampler, the chains, the contract.

Run: python3 chapters/chapter14/files/run_ex14.py
Prints "NN/NN checks passed" and exits non-zero on failure.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from anneal import embed, instances, qubo, sampler

checks = 0
failures: list[str] = []


def check(condition: bool, description: str) -> None:
    global checks
    checks += 1
    if not condition:
        failures.append(description)


def section(name: str) -> None:
    print(f"\n== {name}")


# -- the QUBO -----------------------------------------------------------
section("the QUBO")
edges = instances.maxcut_square()
small = qubo.qubo_from_maxcut(edges, 4)
check(small[(0, 0)] == -3.0, "x0 has diagonal -3, its degree")
check(small[(2, 2)] == -3.0, "x2 has diagonal -3 as well")
check(small[(0, 1)] == 2.0, "and the edge 0-1 carries coefficient 2")
check(len(small) == 9, "nine terms: four diagonal and five off it")

energies = qubo.all_energies(small, 4)
check(energies[0b0101] == -4.0, "0101 has energy -4")
check(energies[0b1010] == -4.0, "and so does 1010")
check(energies[0b0000] == 0.0, "all zeros has energy zero")

def cut_of(bits: int) -> float:
    return sum(weight for i, j, weight in edges if ((bits >> i) & 1) != ((bits >> j) & 1))


check(all(abs(energies[bits] + cut_of(bits)) < 1e-12 for bits in range(16)),
      "energy is minus the cut for all sixteen assignments")

best_value, assignment = qubo.brute_force(small, 4)
bits = sum(bit << index for index, bit in assignment.items())
check(best_value == -4.0, "the minimum energy is -4")
check(bits in (0b0101, 0b1010), "reached by one of the two optimal cuts")

for bad in ([(0, 0, 1.0)], [(0, 1, 0.0)], [(0, 1, -1.0)]):
    try:
        qubo.qubo_from_maxcut(bad, 2)
    except ValueError:
        check(True, f"{bad} is refused")
    else:
        check(False, f"{bad} is refused")

# -- the substitution ---------------------------------------------------
section("bits to spins")
linear, coupling, offset = qubo.to_ising(small)
check(linear == {} or len(linear) == 0, "a unit-weight cut has no local fields")
check(abs(offset + 2.5) < 1e-12, "the offset is -2.5")
check(len(coupling) == 5, "five couplings, one per edge")

same = True
for bits2 in range(16):
    assignment2 = {i: (bits2 >> i) & 1 for i in range(4)}
    spins = {i: 2 * value - 1 for i, value in assignment2.items()}
    if abs(qubo.energy(small, assignment2) - qubo.ising_energy(linear, coupling, offset, spins)) > 1e-12:
        same = False
check(same, "the substituted energy matches the QUBO energy on all sixteen")

back, constant = qubo.to_qubo(linear, coupling, offset)
check(qubo.energy(back, {0: 1, 1: 0, 2: 1, 3: 0}) + constant == -4.0,
      "and the inverse substitution returns to the QUBO")

# -- the sampler --------------------------------------------------------
section("the sampler")
glass = instances.spin_glass()
check(len(glass) == 66, "the spin glass has 66 couplings on twelve variables")
check(glass == instances.spin_glass(), "and it is reproducible")

exact = sampler.Exact({}, glass).sample()
optimum = exact.best()[0]
check(optimum == -24.0, "the exact optimum is -24")
check(int(exact.info["ground states"]) == 4, "reached by four assignments")

spins = {variable: 1 for variable in range(12)}
manual = sampler.ising_energy({}, glass, 0.0, spins)
check(manual == float(sum(glass.values())), "all spins up is the sum of the couplings")

delta = sampler.flip_delta({}, glass, spins, 0)
energy_up = sampler.ising_energy({}, glass, 0.0, spins)
flipped = dict(spins)
flipped[0] = -1
energy_down = sampler.ising_energy({}, glass, 0.0, flipped)
check(abs(delta - (energy_down - energy_up)) < 1e-12, "the flip delta matches the two energies")

field = sampler.local_field({}, glass, spins, 0)
check(abs(field - sum(strength for (i, j), strength in glass.items() if i == 0 or j == 0)) < 1e-12,
      "the local field is the sum of the couplings on that spin")

result = sampler.Annealer({}, glass, 0.0, sweeps=300, seed=11).sample(200)
rate = sampler.success_rate(result, optimum)
check(rate > 0.95, "three hundred sweeps find the optimum more than 95% of the time")
check(result.reads == 200, "the occurrences sum to the reads")
check(result.best()[0] == optimum, "and the best read is the optimum")

short = sampler.Annealer({}, glass, 0.0, sweeps=10, seed=11).sample(200)
check(sampler.success_rate(short, optimum) < rate, "ten sweeps does worse than three hundred")
check(short.info["acceptance"] > result.info["acceptance"], "and accepts more moves, because it is hotter")

trace = sampler.Annealer({}, glass, 0.0, sweeps=200, seed=11).trace(20)
check(trace[0][0] == 0, "the trace starts at sweep zero")
check(len(trace) == 11, "and samples every twentieth sweep")
check(trace[-1][1] >= optimum - 1e-12, "the final energy is at or above the optimum")

check(sampler.reads_for(0.99) == 1, "a 99% machine needs one read for 95%")
check(sampler.reads_for(0.5) == 5, "a coin needs five")
check(sampler.reads_for(0.1) == 29, "a one-in-ten machine needs twenty-nine")
check(sampler.reads_for(0.05) == 59, "a one-in-twenty needs fifty-nine")
check(sampler.reads_for(0.05, 0.99) == 90, "and ninety for 99%")

for bad in (0.0, 1.5):
    try:
        sampler.reads_for(bad)
    except ValueError:
        check(True, f"a probability of {bad} is refused")
    else:
        check(False, f"a probability of {bad} is refused")

# -- the graph ----------------------------------------------------------
section("Chimera")
graph = embed.Chimera(2, 2)
check(len(graph.qubits) == 32, "C(2,2) has 32 qubits")
check(len(graph.edges()) == 80, "and eighty couplers")
check(graph.has_edge((0, 0, 0), (0, 0, 4)), "a horizontal and a vertical qubit in one cell touch")
check(not graph.has_edge((0, 0, 0), (0, 0, 1)), "two horizontals in one cell do not")
check(graph.has_edge((0, 0, 0), (0, 1, 0)), "a horizontal qubit touches the cell on its right")
check(not graph.has_edge((0, 0, 0), (1, 0, 0)), "but not the cell below")

# -- the embedding ------------------------------------------------------
section("the embedding")
logical_linear, logical_coupling, embedding = embed.five_variable_instance()
embed.validate(embedding, graph, logical_coupling.keys())
check(len(embedding) == 5, "five logical variables")
check(sum(len(chain) for chain in embedding.values()) == 9, "on nine physical qubits")
check(embedding[4] == [(0, 0, 1)], "the tail variable is a single qubit")
check(len(embedding[0]) == 2, "and four of them need a chain of two")

broken_test = {variable: list(chain) for variable, chain in embedding.items()}
broken_test[0] = [(0, 0, 0), (0, 0, 1)]
try:
    embed.validate(broken_test, graph, logical_coupling.keys())
except ValueError:
    check(True, "a chain that is not connected is refused")
else:
    check(False, "a chain that is not connected is refused")

overlap = {variable: list(chain) for variable, chain in embedding.items()}
overlap[4] = [(0, 0, 0)]
try:
    embed.validate(overlap, graph, logical_coupling.keys())
except ValueError:
    check(True, "a physical qubit used twice is refused")
else:
    check(False, "a physical qubit used twice is refused")

sample = {qubit: 1 for qubit in graph.qubits}
logical, broken = embed.unembed(sample, embedding)
check(all(value == 1 for value in logical.values()), "an all-up sample unembeds to all-up")
check(broken == [], "with no broken chains")

split = dict(sample)
split[(0, 0, 0)] = -1
logical2, broken2 = embed.unembed(split, embedding)
check(0 in broken2, "one disagreement marks the chain broken")
check(logical2[0] == -1, "and a tie goes to -1, which is the stated convention")
check(abs(embed.chain_break_fraction(split, embedding) - 0.2) < 1e-12, "the fraction is one chain in five")

physical_linear, physical_coupling = embed.physical_problem(
    logical_linear, logical_coupling, embedding, 1.0, graph
)
check(len(physical_linear) == 9, "the physical problem has nine qubits")
check(all(value < 0 for (a, b), value in physical_coupling.items() if a[2] == b[2] and a[:2] != b[:2]),
      "chain couplings are negative, which aligns the chain")

exact_logical = sampler.Exact(logical_linear, logical_coupling).sample()
check(exact_logical.best()[0] == -5.0, "the logical optimum is -5")

rows = {}
for strength in (0.2, 1.0, 4.0):
    physical_linear, physical_coupling = embed.physical_problem(
        logical_linear, logical_coupling, embedding, strength, graph
    )
    run = sampler.Annealer(physical_linear, physical_coupling, 0.0, sweeps=300, seed=5).sample(50)
    fractions = [
        embed.chain_break_fraction(item, embedding) * count
        for item, count in zip(run.samples, run.occurrences)
    ]
    rows[strength] = sum(fractions) / run.reads

check(rows[0.2] > 0.1, "a weak chain breaks more than one run in ten")
check(rows[1.0] < 0.01, "a strength of one breaks almost never")
check(rows[4.0] < 0.01, "and so does four")

print()
if failures:
    print(f"{len(failures)} failed:")
    for failure in failures:
        print(f"  - {failure}")
    sys.exit(1)
print(f"{checks}/{checks} checks passed")
