"""Exercise 5, file 1 of 3: the pure part.

A function in, a comparison of costs out. No printing, no file access, no globals.
"""

from __future__ import annotations

from typing import Callable, Dict

from algorithms import (
    classical_queries_bernstein_vazirani,
    classical_queries_deutsch_jozsa,
    deutsch_jozsa,
    deutsch_jozsa_answer,
    bernstein_vazirani,
    most_likely,
)
from oracle import is_balanced, is_constant


def deutsch_jozsa_report(f: Callable[[int], int], n: int) -> Dict[str, float]:
    distribution = deutsch_jozsa(f, n)
    label, probability = most_likely(distribution)
    classical = classical_queries_deutsch_jozsa(f, n)
    return {
        "answer": deutsch_jozsa_answer(distribution),
        "outcome": label,
        "probability": probability,
        "classical_queries": classical,
        "quantum_queries": 1,
        "ratio": classical / 1,
        "constant": is_constant(f, n),
        "balanced": is_balanced(f, n),
    }


def bernstein_vazirani_report(secret: int, n: int) -> Dict[str, float]:
    distribution = bernstein_vazirani(secret, n)
    label, probability = most_likely(distribution)
    classical = classical_queries_bernstein_vazirani(secret, n)
    return {
        "answer": "secret recovered",
        "outcome": label,
        "probability": probability,
        "classical_queries": classical,
        "quantum_queries": 1,
        "ratio": classical / 1,
        "constant": False,
        "balanced": True,
    }


def rows(report: Dict[str, float]) -> list:
    return [
        ("answer", str(report["answer"])),
        ("outcome", str(report["outcome"])),
        ("probability", f"{report['probability']:.4f}"),
        ("classical queries", str(report["classical_queries"])),
        ("quantum queries", str(report["quantum_queries"])),
        ("ratio", f"{report['ratio']:.1f}x"),
    ]
