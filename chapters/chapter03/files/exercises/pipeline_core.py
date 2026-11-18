"""Exercise 5, file 1 of 3: the pure part.

A circuit in, a table of costs out. No SDK, no printing, no I/O: the same circuit
always produces the same numbers, which is what lets the wiring compare two
compilers without trusting either.
"""

from __future__ import annotations

from typing import Dict, List

from circuit import Circuit
from compiler import compiled_cost


def stats(circuit: Circuit) -> Dict[str, float]:
    """Cost of compiling this circuit with this chapter's compiler."""
    cost = compiled_cost(circuit)
    return {
        "ops_in": cost["ops_before"],
        "ops_out": cost["ops_after"],
        "depth_in": cost["depth_before"],
        "depth_out": cost["depth_after"],
        "ratio": cost["depth_ratio"],
        "distance": cost["distance"],
    }


def rows(name: str, cost: Dict[str, float]) -> List[tuple]:
    """One row per number, so the renderer never formats arithmetic."""
    return [
        (name, "gates", f"{cost['ops_in']} -> {cost['ops_out']}"),
        (name, "depth", f"{cost['depth_in']} -> {cost['depth_out']}"),
        (name, "ratio", f"{cost['ratio']:.2f}"),
        (name, "distance", f"{cost['distance']:.1e}"),
    ]


def deeper_than_written(cost: Dict[str, float]) -> bool:
    return cost["depth_out"] >= cost["depth_in"]
