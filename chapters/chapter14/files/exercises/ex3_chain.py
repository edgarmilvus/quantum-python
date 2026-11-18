"""Exercise 3 (measure): the chain strength that is neither too weak nor too strong.

Run: python3 chapters/chapter14/files/exercises/ex3_chain.py

The five-variable instance needs four chains of two physical qubits. At strength
0.2 one chain in five breaks and the majority vote reads the wrong assignment;
at 1.0 nothing breaks and every read is optimal; at 4.0 nothing breaks and a
quarter of the reads are trapped, because the chain terms dominate the couplings
they are supposed to serve.
"""

import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from typing import Callable, Dict, List

from anneal import embed, sampler


def run_at(graph: embed.Chimera, strength: float, reads: int = 50, sweeps: int = 300) -> Dict[str, float]:
    """One annealing run on the embedded problem, summarised."""
    linear, coupling, embedding = embed.five_variable_instance()
    optimum = sampler.Exact(linear, coupling).sample().best()[0]
    physical_linear, physical_coupling = embed.physical_problem(
        linear, coupling, embedding, strength, graph
    )
    result = sampler.Annealer(physical_linear, physical_coupling, 0.0, sweeps=sweeps, seed=5).sample(reads)
    breaks = 0.0
    hits = 0
    total = 0.0
    for sample, count in zip(result.samples, result.occurrences):
        breaks += embed.chain_break_fraction(sample, embedding) * count
        logical, _ = embed.unembed(sample, embedding)
        energy = sampler.ising_energy(linear, coupling, 0.0, logical)
        total += energy * count
        if energy <= optimum + 1e-9:
            hits += count
    return {
        "breaks": breaks / result.reads,
        "success": hits / result.reads,
        "mean energy": total / result.reads,
        "optimum": optimum,
        "reads": float(result.reads),
    }


def sweep(graph: embed.Chimera, strengths: List[float]) -> List[Dict[str, float]]:
    return [{"strength": strength, **run_at(graph, strength)} for strength in strengths]


def best_strength(graph: embed.Chimera, strengths: List[float]) -> float:
    rows = sweep(graph, strengths)
    return max(rows, key=lambda row: (row["success"], row["mean energy"]))["strength"]


def checks(check: Callable[[bool, str], None]) -> None:
    graph = embed.Chimera(2, 2)
    rows = {row["strength"]: row for row in sweep(graph, [0.2, 0.5, 1.0, 2.0, 4.0])}

    weak = rows[0.2]
    sweet = rows[1.0]
    strong = rows[4.0]

    check(weak["breaks"] > 0.1, "0.2 breaks more than one chain in ten")
    check(weak["success"] < 0.6, "and fewer than six reads in ten are optimal")
    check(weak["mean energy"] > -3.0, "the mean logical energy is above -3")

    check(sweet["breaks"] < 0.01, "1.0 breaks almost no chain")
    check(sweet["success"] > 0.95, "and almost every read is optimal")
    check(abs(sweet["mean energy"] + 5.0) < 0.01, "with a mean energy at the optimum")

    check(strong["breaks"] < 0.01, "4.0 breaks none either")
    check(strong["success"] < 0.85, "and still loses reads, because the landscape is rugged")
    check(strong["mean energy"] > sweet["mean energy"], "so its mean energy is worse than 1.0's")

    check(rows[0.5]["success"] > weak["success"], "0.5 is better than 0.2")
    check(rows[0.5]["breaks"] < weak["breaks"], "and breaks fewer chains")

    best = best_strength(graph, [0.2, 0.5, 1.0, 2.0, 4.0])
    check(0.5 <= best <= 2.0, "the best strength in the sweep is between 0.5 and 2.0")

    check(all(row["reads"] == 50 for row in rows.values()), "every run used fifty reads")
    check(all(row["optimum"] == -5.0 for row in rows.values()), "and the same logical optimum")


if __name__ == "__main__":
    from selfcheck import main

    main(_sys.modules[__name__])
