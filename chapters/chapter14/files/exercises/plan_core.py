"""Exercise 5, file 1 of 3: the pure part.

A sampler result and an optimum in, a verdict out. No annealer, no file, no
print: the core cannot tell whether the result came from twelve spins or from
nine physical ones that were unembedded before it arrived.
"""

from __future__ import annotations

from typing import Dict

from anneal import sampler


def summarise(
    result: sampler.Result, optimum: float, tolerance: float = 1e-9
) -> Dict[str, float]:
    """The four numbers an annealing report owes: best, gap, rate, reads."""
    if result.reads < 1:
        raise ValueError("an empty result has no summary")
    best, _ = result.best()
    hits = sum(
        count for energy, count in zip(result.energies, result.occurrences) if energy <= optimum + tolerance
    )
    return {
        "best": float(best),
        "optimum": float(optimum),
        "gap": float(best - optimum),
        "success": hits / result.reads,
        "reads": float(result.reads),
        "distinct": float(result.unique()),
    }


def verdict(summary: Dict[str, float]) -> str:
    """A word for whether the run found the ground state and how often."""
    if summary["gap"] > 1e-9:
        return "missed the optimum"
    if summary["success"] >= 0.95:
        return "at the optimum"
    if summary["success"] >= 0.5:
        return "usually at the optimum"
    return "sometimes at the optimum"


def reads_for_summary(summary: Dict[str, float], target: float = 0.95) -> int:
    """Reads a run of this quality would need, given its per-read success."""
    if summary["success"] <= 0:
        raise ValueError("a run that never succeeds has no read count")
    return sampler.reads_for(summary["success"], target)
