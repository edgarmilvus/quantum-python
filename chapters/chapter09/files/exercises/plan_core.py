"""Exercise 5, file 1 of 3: the pure part.

A modulus and a base in, a plan out: the order, the width, the success rate, the attempts
and the factors the classical half would return.
"""

from __future__ import annotations

import math
from typing import Dict

import order


def plan(n: int, a: int, ancillas: int | None = None) -> Dict[str, float]:
    if n < 4:
        raise ValueError(f"a modulus must be at least four, got {n}")
    if math.gcd(a, n) != 1:
        raise ValueError(f"{a} and {n} are not coprime; the gcd is a factor by itself")
    resources = order.circuit_resources(n)
    width = ancillas if ancillas is not None else resources["ancillas"]
    if resources["bits"] + width > order.MAX_BITS:
        # Too wide to simulate: report the arithmetic count and leave the probability out.
        probability = 0.0
        attempts = 0
    else:
        success = order.quantum_success(a, n, resources["bits"], width)
        probability = success["probability"]
        attempts = math.ceil(math.log(0.05) / math.log(1 - min(probability, 0.999)))
    r = order.order_of(a, n)
    factors = order.factors_from_order(a, n, r) if r else None
    return {
        "n": n,
        "a": a,
        "order": r or 0,
        "bits": resources["bits"],
        "ancillas": width,
        "qubits": resources["bits"] + width,
        "probability": probability,
        "attempts": attempts,
        "factors": factors or (0, 0),
    }


def rows(result: Dict[str, float]) -> list:
    left, right = result["factors"]
    return [
        ("modulus", str(int(result["n"]))),
        ("base", str(int(result["a"]))),
        ("order", str(int(result["order"]))),
        ("bits", str(int(result["bits"]))),
        ("ancillas", str(int(result["ancillas"]))),
        ("qubits", str(int(result["qubits"]))),
        ("one-run success", f"{result['probability']:.4f}"),
        ("runs for 95%", str(int(result["attempts"]))),
        ("factors", f"{int(left)} x {int(right)}" if left else "none"),
    ]
