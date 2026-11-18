"""Exercise 5, file 1 of 3: the pure part.

A problem size in, a plan out: how many iterations, what probability to expect, and what
the classical alternatives would cost.
"""

from __future__ import annotations

from typing import Dict

import grover


def plan(size: int, marked: int = 1, n: int | None = None) -> Dict[str, float]:
    """The iteration count, the expected success and both classical costs."""
    if size < 2:
        raise ValueError(f"a search needs at least two items, got {size}")
    bits = n if n is not None else size.bit_length() - 1
    if (1 << bits) != size:
        raise ValueError(f"{size} is not a power of two")
    if not 1 <= marked <= size:
        raise ValueError(f"marked items must be in [1, {size}], got {marked}")
    steps = max(1, int(round(grover.math.pi / (4 * grover.math.asin(grover.math.sqrt(marked / size))) - 0.5)))
    if marked == 1:
        probability = grover.success_probability(0, bits, steps)
    else:
        probability = float(grover.math.sin((2 * steps + 1) * grover.math.asin(grover.math.sqrt(marked / size))) ** 2)
    return {
        "size": size,
        "bits": bits,
        "steps": steps,
        "probability": probability,
        "linear": grover.classical_queries(size),
        "binary": grover.binary_search_queries(size),
        "ratio_to_linear": grover.classical_queries(size) / steps,
        "ratio_to_binary": steps / grover.binary_search_queries(size),
    }


def rows(result: Dict[str, float]) -> list:
    return [
        ("items", str(int(result["size"]))),
        ("qubits", str(int(result["bits"]))),
        ("iterations", str(int(result["steps"]))),
        ("success probability", f"{result['probability']:.4f}"),
        ("linear queries", str(int(result["linear"]))),
        ("binary queries", str(int(result["binary"]))),
        ("Grover vs linear", f"{result['ratio_to_linear']:.1f}x better"),
        ("Grover vs binary", f"{result['ratio_to_binary']:.1f}x worse"),
    ]
