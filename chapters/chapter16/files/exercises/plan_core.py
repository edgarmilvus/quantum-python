"""Exercise 5, file 1 of 3: the pure part.

A histogram, a distance and the prepared bit in; the two rates and their interval
out. No file, no device, no print.
"""

from __future__ import annotations

from typing import Dict

from ecc import code


def summarise(distance: int, prepared: int, counts: Dict[str, int]) -> Dict[str, float]:
    """Physical rate, logical rate, and the interval the logical rate deserves."""
    if distance < 3 or distance % 2 == 0:
        raise ValueError(f"a repetition code has an odd distance of at least three, got {distance}")
    if prepared not in (0, 1):
        raise ValueError(f"a prepared bit is 0 or 1, got {prepared}")
    total = sum(counts.values())
    if total <= 0:
        raise ValueError("an empty histogram has no rate")

    instance = code.Repetition(distance)
    flips = 0
    wrong = 0
    for key, count in counts.items():
        bits = [int(character) for character in str(key)[::-1]]
        if len(bits) != distance:
            raise ValueError(f"{key!r} is not a {distance}-bit codeword")
        flips += sum(1 for value in bits if value != prepared) * count
        if instance.decode(bits) != prepared:
            wrong += count

    low, high = code.wilson(wrong, total)
    return {
        "physical": flips / (total * distance),
        "logical": wrong / total,
        "low": low,
        "high": high,
        "shots": float(total),
    }


def verdict(summary: Dict[str, float]) -> str:
    """Whether the code beat the physical rate, and by how much."""
    if summary["logical"] < summary["physical"] / 10:
        return "ten times better"
    if summary["logical"] < summary["physical"]:
        return "better than the physical rate"
    return "no better than the physical rate"
