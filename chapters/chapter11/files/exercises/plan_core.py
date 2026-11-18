"""Exercise 5, file 1 of 3: the pure part.

A result and an expected outcome in, a verdict out. No provider, no network, no printing.
"""

from __future__ import annotations

from typing import Dict

import providers as p


def summarise(result: p.Result, expected: str) -> Dict[str, float]:
    if result.shots <= 0:
        raise ValueError("an empty result has no summary")
    if len(expected) != 2:
        raise ValueError(f"a two-qubit outcome has two bits, got {expected!r}")
    top = max(result.counts, key=result.counts.get)
    return {
        "shots": result.shots,
        "top": top,
        "frequency": result.frequency(top),
        "expected": result.frequency(expected),
        "correct": float(top == expected),
        "outcomes": float(len(result.counts)),
    }
