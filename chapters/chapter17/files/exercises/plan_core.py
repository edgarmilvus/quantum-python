"""Exercise 5, file 1 of 3: the pure part.

A histogram and the prepared bit in; the two numbers a dynamic-circuit report owes
out: the logical error and the fraction of codewords that came back clean.
"""

from __future__ import annotations

from typing import Dict

from dyn import circuit


def summarise(counts: Dict[str, int], prepared: int, distance: int = 3) -> Dict[str, float]:
    if prepared not in (0, 1):
        raise ValueError(f"a prepared bit is 0 or 1, got {prepared}")
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no rate")
    code = circuit.memory(prepared=prepared)
    clean = counts.get("0" * distance, 0) / total
    wrong = 0
    for key, count in counts.items():
        bits = [int(character) for character in key[::-1]]
        if len(bits) != distance:
            raise ValueError(f"{key!r} is not a {distance}-bit codeword")
        if (sum(bits) * 2 > distance) != prepared:
            wrong += count
    return {"clean": clean, "logical": wrong / total, "shots": float(total)}


def verdict(summary: Dict[str, float], control: Dict[str, float]) -> str:
    """Separate the mechanism from the rate, because they disagree on this device.

    "The codeword came back" and "the logical bit is more often right" are two
    different claims. The injection test repairs the codeword 90% of the time and
    still loses on the logical rate, because a false syndrome adds a second flip;
    a verdict with one word cannot say that, so this one has four.
    """
    repaired = summary["clean"] > control["clean"] + 0.1
    logical_worse = summary["logical"] > control["logical"] + 0.01
    if repaired and logical_worse:
        return "codeword repaired, logical rate worse"
    if repaired:
        return "correction helped"
    if logical_worse:
        return "correction hurt"
    if summary["clean"] < control["clean"] - 0.1:
        return "correction hurt"
    return "no difference"
