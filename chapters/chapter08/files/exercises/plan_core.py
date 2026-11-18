"""Exercise 5, file 1 of 3: the pure part.

A target precision in, a plan out: how many bits, how many runs for the required
confidence, and what the circuit costs at that size.
"""

from __future__ import annotations

import math
from typing import Dict

import phase
import qft


def bits_for(precision: float) -> int:
    """The smallest n with 1/2^n at most `precision`."""
    if not 0.0 < precision < 1.0:
        raise ValueError(f"a precision is in (0, 1), got {precision}")
    n = 1
    while 1.0 / (1 << n) > precision:
        n += 1
        if n > 40:
            raise ValueError(f"precision {precision} needs more than forty bits")
    return n


def runs_for(n: int, phi: float, confidence: float = 0.95, limit: int = 101) -> int:
    if not 0.0 < confidence < 1.0:
        raise ValueError(f"a confidence is in (0, 1), got {confidence}")
    k, p = phase.estimate(phi, n)
    q = 1.0 - p
    for runs in range(1, limit + 1, 2):
        tail = sum(
            math.comb(runs, wrong) * q**wrong * p ** (runs - wrong)
            for wrong in range((runs + 1) // 2, runs + 1)
        )
        if 1.0 - tail >= confidence:
            return runs
    raise ValueError(f"confidence {confidence} not reached in {limit} runs")


def plan(precision: float, phi: float, confidence: float = 0.95) -> Dict[str, float]:
    n = bits_for(precision)
    k, single = phase.estimate(phi, n)
    runs = runs_for(n, phi, confidence)
    return {
        "bits": n,
        "single_shot": single,
        "runs": runs,
        "confidence": confidence,
        "gates": qft.gate_count(n + 1),
        "depth": qft.circuit_depth(n + 1),
        "total_gates": qft.gate_count(n + 1) * runs,
    }


def rows(result: Dict[str, float]) -> list:
    return [
        ("bits", str(int(result["bits"]))),
        ("single shot", f"{result['single_shot']:.4f}"),
        ("runs for target", str(int(result["runs"]))),
        ("confidence", f"{result['confidence']:.2f}"),
        ("gates per run", str(int(result["gates"]))),
        ("depth per run", str(int(result["depth"]))),
        ("total gates", str(int(result["total_gates"]))),
    ]
